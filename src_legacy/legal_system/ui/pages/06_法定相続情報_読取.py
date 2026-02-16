# src/legal_system/ui/pages/06_法定相続情報_読取.py

import base64
import json
import logging
import os
import re
import sys
import time
import unicodedata
from datetime import date, datetime
from io import BytesIO

import pandas as pd
import streamlit as st
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_bytes
from PIL import Image
from sqlalchemy.orm import joinedload

# パス解決
# pages -> ui -> legal_system -> src -> ROOT
current_dir = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Address, Case, Deceased, H_AddressHistory, Heir

# ★修正: src. を付与して絶対インポートに変更
from services.deceased_service import (
    find_cases_by_attributes,
    search_zip_by_address_api,
)

logger = logging.getLogger(__name__)

st.set_page_config(page_title="法定相続情報 読取", page_icon="👪", layout="wide")


# -----------------------------------------------------------------------------
# ユーティリティ関数
# -----------------------------------------------------------------------------
def normalize_name_with_space(name: str) -> str:
    if not name:
        return ""
    name = unicodedata.normalize("NFKC", name)
    if " " in name:
        return name.replace(" ", "　")
    if "　" in name:
        return name
    return name


def get_clean_name_for_compare(name: str) -> str:
    if not name:
        return ""
    return name.replace(" ", "").replace("　", "")


def parse_wareki_str(date_str: str) -> date:
    if not date_str:
        return None
    s = unicodedata.normalize("NFKC", date_str).strip()
    try:
        return datetime.strptime(s.replace("/", "-"), "%Y-%m-%d").date()
    except:
        pass
    eras = {
        "令和": (2018, "R"),
        "平成": (1988, "H"),
        "昭和": (1925, "S"),
        "大正": (1911, "T"),
        "明治": (1868, "M"),
    }
    pattern = r"([A-Za-z]+|[^\x00-\x7F]+)(\d+|元)[./年](\d+)[./月](\d+)[日]?"
    match = re.match(pattern, s)
    if match:
        era_str = match.group(1)
        year_str = match.group(2)
        month = int(match.group(3))
        day = int(match.group(4))
        year_num = 1 if year_str == "元" else int(year_str)
        seireki_year = 0
        for name, (base, alpha) in eras.items():
            if name in era_str or alpha.lower() == era_str.lower():
                seireki_year = base + year_num
                break
        if seireki_year > 0:
            try:
                return date(seireki_year, month, day)
            except ValueError:
                return None
    return None


def split_address_smart(full_address: str) -> dict:
    if not full_address:
        return {"pref": "", "city_ward": "", "street": "", "build": ""}
    addr = unicodedata.normalize("NFKC", full_address)
    pref = ""
    rest = addr
    m_pref = re.match(r"(.{2,3}[都道府県])(.*)", addr)
    if m_pref:
        pref = m_pref.group(1)
        rest = m_pref.group(2)
    city_ward = ""
    street = ""
    m_split = re.search(r"\d", rest)
    if m_split:
        idx = m_split.start()
        city_ward = rest[:idx]
        street = rest[idx:]
    else:
        city_ward = rest
        street = ""
    build = ""
    if " " in street or "　" in street:
        parts = re.split(r"[ 　]+", street, 1)
        street = parts[0]
        build = parts[1]
    return {"pref": pref, "city_ward": city_ward, "street": street, "build": build}


# ★追加: 漢数字を算用数字に変換する関数
def normalize_address_number(text: str) -> str:
    """
    住所検索のために、漢数字（一丁目など）を算用数字（1丁目）に簡易変換する。
    """
    if not text:
        return ""
    # 簡易変換
    text = (
        text.replace("一丁目", "1丁目")
        .replace("二丁目", "2丁目")
        .replace("三丁目", "3丁目")
    )
    text = (
        text.replace("四丁目", "4丁目")
        .replace("五丁目", "5丁目")
        .replace("六丁目", "6丁目")
    )
    text = (
        text.replace("七丁目", "7丁目")
        .replace("八丁目", "8丁目")
        .replace("九丁目", "9丁目")
    )
    text = text.replace("十丁目", "10丁目").replace("十一丁目", "11丁目")

    return text


def smart_zip_search(pref, city_ward, street):
    """
    住所から郵便番号を検索する。漢数字対応版。
    """
    # 1. そのまま結合して検索
    full = f"{pref}{city_ward}{street}".strip()
    if not full:
        return ""

    zip_code = search_zip_by_address_api(full)
    if zip_code:
        return zip_code

    # 2. 漢数字を変換して検索 (例: 夏見台一丁目 -> 夏見台1丁目)
    normalized_full = normalize_address_number(full)
    if normalized_full != full:
        zip_code = search_zip_by_address_api(normalized_full)
        if zip_code:
            return zip_code

    # 3. 町域レベルで再検索
    town_level = f"{pref}{city_ward}".strip()
    if town_level:
        zip_code = search_zip_by_address_api(town_level)

    return zip_code if zip_code else ""


# -----------------------------------------------------------------------------
# AI解析ロジック
# -----------------------------------------------------------------------------
def analyze_heir_document_with_ai(image_bytes: bytes) -> dict:
    try:
        img_str = base64.b64encode(image_bytes).decode("utf-8")
        llm = AIFactory.get_llm(mode="cloud", temperature=0.0)
        prompt_text = """
        あなたは熟練した行政書士補助者です。
        提供された「法定相続情報一覧図」の画像を読み取り、JSONとして抽出してください。
        
        【抽出項目】
        {
            "deceased": {
                "name": "被相続人の氏名",
                "birth_date": "生年月日(記載通りの和暦)",
                "death_date": "死亡日(記載通りの和暦)",
                "last_address": "最後の住所",
                "registered_domicile": "本籍地"
            },
            "heirs": [
                {
                    "name": "相続人氏名",
                    "relationship": "続柄",
                    "birth_date": "生年月日(記載通りの和暦)",
                    "address": "住所"
                },
                ...
            ]
        }
        """
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_str}"},
            ]
        )
        response = llm.invoke([message])
        content = response.content.replace("```json", "").replace("```", "").strip()
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(content[start:end])
        else:
            raise ValueError("JSON parse error")
    except Exception as e:
        logger.error(f"Heir Analysis Error: {e}")
        return {"error": str(e)}


# -----------------------------------------------------------------------------
# メイン画面
# -----------------------------------------------------------------------------
def main():
    st.title("👪 法定相続情報 読取・自動紐付け")
    st.caption(
        "書類をアップロードすると、**自動的に**内容を読み取り、該当する案件を検索します。"
    )

    db = DatabaseManager()
    session = db._get_session()

    if "heir_result" not in st.session_state:
        st.session_state["heir_result"] = None
    if "target_case_id" not in st.session_state:
        st.session_state["target_case_id"] = None
    if "candidate_cases" not in st.session_state:
        st.session_state["candidate_cases"] = []
    if "last_analyzed_file_id" not in st.session_state:
        st.session_state["last_analyzed_file_id"] = None

    uploaded_file = st.file_uploader(
        "法定相続情報一覧図 (PDF/画像)", type=["pdf", "png", "jpg"]
    )

    if uploaded_file:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"

        file_bytes = uploaded_file.getvalue()
        target_bytes = None
        display_img = None

        try:
            if uploaded_file.type == "application/pdf":
                images = convert_from_bytes(
                    file_bytes, dpi=200, first_page=1, last_page=1
                )
                display_img = images[0]
            else:
                display_img = Image.open(BytesIO(file_bytes))

            buf = BytesIO()
            display_img.convert("RGB").save(buf, format="JPEG")
            target_bytes = buf.getvalue()
        except Exception as e:
            st.error(f"画像変換エラー: {e}")
            return

        # 1. 自動AI解析
        if st.session_state["last_analyzed_file_id"] != file_id:
            st.image(display_img, caption="プレビュー (解析中...)", width=400)

            with st.spinner("🤖 自動解析中... (文字読取 & 案件検索)"):
                result = analyze_heir_document_with_ai(target_bytes)

                if "error" in result:
                    st.error(f"解析失敗: {result['error']}")
                else:
                    st.session_state["heir_result"] = result
                    st.session_state["last_analyzed_file_id"] = file_id

                    dec_name = result.get("deceased", {}).get("name", "")
                    if dec_name:
                        clean_name = get_clean_name_for_compare(dec_name)
                        candidates = find_cases_by_attributes(deceased_name=clean_name)
                        st.session_state["candidate_cases"] = candidates

                    st.toast("解析が完了しました！", icon="✅")
                    time.sleep(0.5)
                    st.rerun()

        # 2. 案件選択
        elif (
            st.session_state["heir_result"]
            and st.session_state["target_case_id"] is None
        ):
            col_prev, col_sel = st.columns([1, 1.5])

            with col_prev:
                st.image(display_img, use_container_width=True)

            with col_sel:
                res = st.session_state["heir_result"]
                dec_info = res.get("deceased", {})
                st.success(f"✅ 読み取り完了: 被相続人 **{dec_info.get('name')}**")

                candidates = st.session_state["candidate_cases"]
                st.subheader("🔍 紐付け先の案件を選択")

                if candidates:
                    st.info(f"{len(candidates)} 件の候補が見つかりました。")
                    selected_idx = st.radio(
                        "候補案件リスト",
                        options=range(len(candidates)),
                        format_func=lambda i: (
                            f"【{candidates[i]['case_number']}】 依頼者: {candidates[i]['client_name']} (被相続人: {candidates[i]['deceased_name']})"
                        ),
                        key="case_selector_radio",
                    )
                    if st.button(
                        "✅ この案件に紐付ける",
                        type="primary",
                        use_container_width=True,
                    ):
                        st.session_state["target_case_id"] = candidates[selected_idx][
                            "case_id"
                        ]
                        st.rerun()
                else:
                    st.warning("⚠️ 自動検索では該当する案件が見つかりませんでした。")

                st.markdown("---")
                with st.expander(
                    "手動検索 (見つからない場合)", expanded=not candidates
                ):
                    manual_q = st.text_input("案件番号(Gxxxx) または 氏名で検索")
                    if st.button("再検索"):
                        hits = find_cases_by_attributes(
                            case_number=manual_q,
                            client_name=manual_q,
                            deceased_name=manual_q,
                        )
                        if hits:
                            st.session_state["candidate_cases"] = hits
                            st.rerun()
                        else:
                            st.error("見つかりませんでした。")

        # 3. 編集・登録
        elif st.session_state["target_case_id"]:
            target_case = (
                session.query(Case)
                .options(joinedload(Case.deceased_ref).joinedload(Deceased.heirs))
                .filter_by(case_id=st.session_state["target_case_id"])
                .first()
            )

            existing_heirs = []
            if target_case.deceased_ref:
                existing_heirs = target_case.deceased_ref.heirs

            existing_heir_map = {}
            for h in existing_heirs:
                full_key = get_clean_name_for_compare(f"{h.name_last}{h.name_first}")
                existing_heir_map[full_key] = h

            st.info(
                f"📁 紐付け先: **{target_case.case_number} {target_case.client_name}** 様"
            )

            col_img, col_data = st.columns([1, 1.2])
            with col_img:
                st.image(display_img, use_container_width=True)

            with col_data:
                st.subheader("📝 データ確認・編集")
                data = st.session_state["heir_result"]
                d_info = data.get("deceased", {})

                # --- 1. 被相続人 ---
                st.markdown("##### 1. 被相続人情報")
                with st.container(border=True):
                    db_d = target_case.deceased_ref

                    init_name = (
                        f"{db_d.name_last}　{db_d.name_first}"
                        if db_d and db_d.name_last
                        else normalize_name_with_space(d_info.get("name", ""))
                    )
                    init_kana = (
                        f"{db_d.name_last_kana}　{db_d.name_first_kana}"
                        if db_d and db_d.name_last_kana
                        else ""
                    )
                    init_honseki = (
                        db_d.hometown
                        if db_d and db_d.hometown
                        else d_info.get("registered_domicile", "")
                    )

                    c1, c2 = st.columns(2)
                    d_name = c1.text_input("氏名 (全角スペース区切り)", value=init_name)
                    d_kana = c2.text_input("フリガナ", value=init_kana)

                    c3, c4 = st.columns(2)
                    d_dod_str = c3.text_input(
                        "死亡日 (和暦入力可)",
                        value=d_info.get("death_date", ""),
                        help="例: 令和5年1月1日",
                    )
                    d_dob_str = c4.text_input(
                        "生年月日 (和暦入力可)",
                        value=d_info.get("birth_date", ""),
                        help="例: 昭和24年5月1日",
                    )

                    d_honseki = st.text_input("本籍地", value=init_honseki)

                    st.markdown("---")
                    st.caption("最後の住所")
                    ai_addr_full = d_info.get("last_address", "")
                    split_res = split_address_smart(ai_addr_full)

                    # 郵便番号自動検索 (漢数字対応)
                    auto_zip = ""
                    if ai_addr_full:
                        auto_zip = smart_zip_search(
                            split_res["pref"],
                            split_res["city_ward"],
                            split_res["street"],
                        )

                    az, ap = st.columns([1, 1])
                    d_zip = az.text_input("郵便番号", value=auto_zip)
                    d_pref = ap.text_input("都道府県", value=split_res["pref"])
                    ac, ab = st.columns([2, 2])
                    d_city = ac.text_input("市区町村", value=split_res["city_ward"])
                    d_street = ab.text_input("番地", value=split_res["street"])
                    d_bldg = st.text_input("建物名", value=split_res["build"])

                # --- 2. 相続人 (マージロジック適用) ---
                st.markdown("##### 2. 相続人一覧 (手動修正可)")
                heirs_raw = data.get("heirs", [])

                grid_data = []

                for h in heirs_raw:
                    ai_name_clean = get_clean_name_for_compare(h.get("name", ""))
                    matched_heir = existing_heir_map.get(ai_name_clean)

                    # 住所から郵便番号を検索 (漢数字対応)
                    h_addr_val = h.get("address", "")
                    h_auto_zip = ""
                    if h_addr_val:
                        split_h = split_address_smart(h_addr_val)
                        h_auto_zip = smart_zip_search(
                            split_h["pref"], split_h["city_ward"], split_h["street"]
                        )

                    row = {
                        "name": normalize_name_with_space(h.get("name", "")),
                        "kana": "",
                        "relationship": h.get("relationship", ""),
                        "birth_date": h.get("birth_date", ""),
                        "address": h_addr_val,
                        "zip_code": h_auto_zip,
                        "is_contractor": False,
                    }

                    if matched_heir:
                        row["name"] = (
                            f"{matched_heir.name_last}　{matched_heir.name_first}"
                        )
                        if matched_heir.name_last_kana:
                            row["kana"] = (
                                f"{matched_heir.name_last_kana}　{matched_heir.name_first_kana}"
                            )
                        row["is_contractor"] = matched_heir.is_contracting_party

                    grid_data.append(row)

                df_heirs = pd.DataFrame(grid_data)
                if df_heirs.empty:
                    df_heirs = pd.DataFrame(
                        columns=[
                            "name",
                            "kana",
                            "relationship",
                            "birth_date",
                            "address",
                            "zip_code",
                            "is_contractor",
                        ]
                    )

                column_config = {
                    "name": st.column_config.TextColumn("氏名", required=True),
                    "kana": st.column_config.TextColumn("フリガナ", width="medium"),
                    "relationship": st.column_config.TextColumn("続柄", required=True),
                    "birth_date": st.column_config.TextColumn("生年月日(和暦)"),
                    "address": st.column_config.TextColumn(
                        "住所 (全住所)", width="large"
                    ),
                    # 郵便番号列 (手動修正可能)
                    "zip_code": st.column_config.TextColumn("郵便番号", width="small"),
                    "is_contractor": st.column_config.CheckboxColumn(
                        "契約者", default=False
                    ),
                }

                edited_df = st.data_editor(
                    df_heirs,
                    column_config=column_config,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="heir_grid",
                )

                st.divider()

                if st.button(
                    "💾 データベースを更新 (マージ保存)",
                    type="primary",
                    use_container_width=True,
                ):
                    try:
                        # --- Deceased Save ---
                        deceased = target_case.deceased_ref
                        if not deceased:
                            deceased = Deceased(case_id=target_case.case_id)
                            session.add(deceased)

                        if d_name:
                            parts = d_name.replace("　", " ").split(" ")
                            deceased.name_last = parts[0]
                            deceased.name_first = parts[1] if len(parts) > 1 else ""

                        if d_kana:
                            kp = d_kana.replace("　", " ").split(" ")
                            deceased.name_last_kana = kp[0]
                            deceased.name_first_kana = kp[1] if len(kp) > 1 else ""

                        deceased.hometown = d_honseki
                        deceased.date_of_death = parse_wareki_str(d_dod_str)
                        deceased.date_of_birth = parse_wareki_str(d_dob_str)

                        # Deceased Address
                        target_addr = None
                        if deceased.last_address_id:
                            target_addr = session.query(Address).get(
                                deceased.last_address_id
                            )
                        if not target_addr:
                            target_addr = Address(prefecture="", street_address="")
                            session.add(target_addr)
                            session.flush()
                            deceased.last_address_id = target_addr.id

                        target_addr.zip_code = d_zip
                        target_addr.prefecture = d_pref
                        target_addr.city_ward_town = d_city
                        target_addr.street_address = d_street
                        target_addr.building_name = d_bldg

                        # --- Heirs Save (Smart Merge) ---
                        processed_heir_ids = []

                        for index, row in edited_df.iterrows():
                            if not row["name"]:
                                continue

                            full_name = normalize_name_with_space(row["name"])
                            parts = full_name.split("　")
                            lname = parts[0]
                            fname = parts[1] if len(parts) > 1 else ""
                            clean_key = get_clean_name_for_compare(full_name)

                            k_lname, k_fname = "", ""
                            if row["kana"]:
                                k_parts = normalize_name_with_space(row["kana"]).split(
                                    "　"
                                )
                                k_lname = k_parts[0]
                                k_fname = k_parts[1] if len(k_parts) > 1 else ""

                            target_heir = existing_heir_map.get(clean_key)

                            if not target_heir:
                                target_heir = Heir(deceased_id=deceased.id)
                                session.add(target_heir)

                            # 1. 相続人情報の更新 (郵便番号はここではまだ更新されない)
                            target_heir.name_last = lname
                            target_heir.name_first = fname
                            target_heir.name_last_kana = k_lname
                            target_heir.name_first_kana = k_fname
                            target_heir.relationship_type = row["relationship"]
                            target_heir.date_of_birth = parse_wareki_str(
                                str(row["birth_date"])
                            )
                            target_heir.is_contracting_party = row["is_contractor"]

                            session.flush()
                            processed_heir_ids.append(target_heir.id)

                            # 2. 住所情報の更新 (★ここで郵便番号も保存される)
                            if row["address"]:
                                h_addr_val = row["address"]
                                split_h = split_address_smart(h_addr_val)

                                # テーブル上の郵便番号を採用 (編集済み優先)
                                h_zip = str(row.get("zip_code", "")).strip()
                                # 空なら裏で再検索 (漢数字対応)
                                if not h_zip:
                                    h_zip = smart_zip_search(
                                        split_h["pref"],
                                        split_h["city_ward"],
                                        split_h["street"],
                                    )

                                current_link = (
                                    session.query(H_AddressHistory)
                                    .filter(
                                        H_AddressHistory.heir_id == target_heir.id,
                                        H_AddressHistory.is_current_address == True,
                                    )
                                    .first()
                                )

                                h_addr_obj = None
                                if current_link:
                                    h_addr_obj = session.query(Address).get(
                                        current_link.address_id
                                    )

                                if not h_addr_obj:
                                    h_addr_obj = Address(
                                        prefecture="", street_address=""
                                    )
                                    session.add(h_addr_obj)
                                    session.flush()
                                    session.add(
                                        H_AddressHistory(
                                            heir_id=target_heir.id,
                                            address_id=h_addr_obj.id,
                                            is_current_address=True,
                                        )
                                    )

                                # ★保存処理の核心部分
                                h_addr_obj.zip_code = h_zip  # ←ここで保存
                                h_addr_obj.prefecture = split_h["pref"]
                                h_addr_obj.city_ward_town = split_h["city_ward"]
                                h_addr_obj.street_address = split_h["street"]
                                h_addr_obj.building_name = split_h["build"]

                        session.commit()
                        st.success(
                            f"✅ 案件「{target_case.client_name}」の情報を更新しました！"
                        )
                        time.sleep(2)

                        st.session_state["heir_result"] = None
                        st.session_state["target_case_id"] = None
                        st.rerun()

                    except Exception as e:
                        session.rollback()
                        st.error(f"保存エラー: {e}")

    session.close()


if __name__ == "__main__":
    main()
