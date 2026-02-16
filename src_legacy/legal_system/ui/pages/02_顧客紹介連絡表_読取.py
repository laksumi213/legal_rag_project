# src/legal_system/ui/pages/02_顧客紹介連絡表_読取.py

import base64
import json
import os
import sys
import time
from datetime import datetime
from io import BytesIO

import streamlit as st
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_bytes
from PIL import Image
from sqlalchemy.orm import joinedload

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
)
if project_root not in sys.path:
    sys.path.append(project_root)

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    Address,
    Case,
    Contact,
    Deceased,
    H_AddressHistory,
    H_ContactLink,
    Heir,
)
from services.dispatch_service import (
    determine_base_from_branch,
    generate_kintone_json_payload,
)

from services.deceased_service import (
    add_heir,  # ★追加: 相続人追加用
    # ★追加: 住所取得
    find_cases_by_attributes,  # ★追加: 検索用サービス
    get_next_provisional_number,
    search_zip_by_address_api,
)

st.set_page_config(page_title="書類読取エージェント", page_icon="📄", layout="wide")


def katakana_to_hiragana(katakana_str: str) -> str:
    """
    カタカナ文字列をひらがな文字列に変換する
    """
    if not isinstance(katakana_str, str):
        return ""

    hiragana_chars = []
    for char in katakana_str:
        code_point = ord(char)
        # カタカナの範囲内かチェック (Unicode)
        if 0x30A1 <= code_point <= 0x30F6:
            # 0x60を引くとひらがなになる
            hiragana_chars.append(chr(code_point - 0x60))
        else:
            # カタカナ以外はそのまま追加
            hiragana_chars.append(char)
    return "".join(hiragana_chars)


def _clean_kanji_name_by_kana(kanji_name: str, kana_name: str) -> str:
    """
    カナ名に基づいて漢字名内の不要なスペースを修正する。
    例: "村 木　千枝子", "ムラキ チエコ" -> "村木　千枝子"
    """
    if not kanji_name or not kana_name:
        return kanji_name

    kanji_name = kanji_name.strip()
    # カナ名から全角・半角スペースを除去し、姓名の境目を探す補助とする
    clean_kana = kana_name.strip().replace("　", "").replace(" ", "")

    # 漢字名から全てのスペースを除去した形を準備
    kanji_no_space = kanji_name.replace(" ", "").replace("　", "")

    # 姓と名の間に全角スペースがある場合を想定して分割
    # 例: "村 木　千枝子" -> ["村 木", "千枝子"]
    # この時「村 木」を「村木」にしたい

    # 最後に現れる全角または半角スペースを区切り文字として、姓と名を分ける
    last_space_idx_zen = kanji_name.rfind("　")
    last_space_idx_han = kanji_name.rfind(" ")

    split_idx = -1
    if last_space_idx_zen != -1 and last_space_idx_han != -1:
        split_idx = max(last_space_idx_zen, last_space_idx_han)
    elif last_space_idx_zen != -1:
        split_idx = last_space_idx_zen
    elif last_space_idx_han != -1:
        split_idx = last_space_idx_han

    if split_idx != -1:
        family_name_part = kanji_name[:split_idx].replace(" ", "").replace("　", "")
        given_name_part = kanji_name[split_idx + 1 :].strip()

        # 再度結合時に全角スペースを挟む
        return f"{family_name_part}　{given_name_part}"
    else:
        # スペースが見つからない場合は、全てのスペースを除去して返す
        return kanji_no_space


def analyze_document_gemini(file_bytes: bytes, mime_type: str) -> dict:
    """
    Gemini Visionで画像を解析し、書類タイプに応じたJSONを返す
    対応: 顧客紹介連絡表, 推定相続人連絡先一覧
    """
    img_b64 = base64.b64encode(file_bytes).decode("utf-8")
    image_url = f"data:{mime_type};base64,{img_b64}"

    llm = AIFactory.get_llm("cloud", temperature=0.0)

    prompt_text = """
    あなたは日本の行政手続きに精通した「シニア・データ入力オペレーター」です。
    提供された画像を解析し、それが「A: 顧客紹介連絡表」か「B: 推定相続人連絡先一覧」かを判断した上で、必要な情報を抽出してください。

    【共通ルール】
    - 出力は純粋なJSONのみとし、Markdownコードブロック等は含めないでください。
    - 値がない場合は空文字 "" を出力してください。
    - 氏名は姓と名の間に全角スペースを入れてください（例: "山田　太郎"）。

    ---
    ### パターンA: 顧客紹介連絡表 (SMBC日興証券など)
    特徴: 「紹介元」「部店」「同意書取得日」などの記載がある。
    
    【抽出項目】
    - doc_type: "referral"
    - search_key_name: 顧客名（氏名）
    - client_name: 顧客名
    - client_name_kana: 顧客フリガナ
    - client_phone: 顧客電話番号
    - client_address_full: 顧客住所（郵便番号除く）
    - referral_sec_branch_name: 紹介元支店名
    - referral_sec_rep_name: 紹介元担当者名
    - referral_sec_phone: 紹介元電話番号（内線・直通）
    - sol_case_number: SOL案件番号
    - introduction_date: 紹介日 (YYYY-MM-DD)

    ---
    ### パターンB: 推定相続人連絡先一覧
    特徴: 「遺言者様に関する情報」や、表形式の相続人リストがある。

    【抽出項目】
    - doc_type: "heir_list"
    - search_key_name: 遺言者名（または被相続人名）
    - testator_name: 遺言者名
    - heirs: [
        {
            "name": "氏名",
            "kana": "フリガナ",
            "relationship": "続柄",
            "address": "住所",
            "phone": "電話番号",
            "dob": "生年月日(YYYY-MM-DD)"
        },
        ...
    ]

    【出力JSONスキーマの例】
    {
        "doc_type": "referral" OR "heir_list",
        "search_key_name": "山田　太郎",
        ... (各パターンの項目)
    }
    """

    try:
        msg = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": image_url},
            ]
        )
        response = llm.invoke([msg])
        content = response.content.replace("```json", "").replace("```", "").strip()
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(content[start:end])
        return {}
    except Exception as e:
        st.error(f"AI解析エラー: {e}")
        return {}


def register_new_referral_case(session, data: dict):
    """紹介連絡表からの新規案件登録処理"""
    # 1. 仮番号発番
    temp_no = get_next_provisional_number(session)

    # 2. 拠点自動判定
    branch_name = data.get("referral_sec_branch_name", "")
    assigned_base = determine_base_from_branch(branch_name)

    # 3. 住所分割 (簡易)
    addr_raw = data.get("client_address_full", "")
    zip_code = search_zip_by_address_api(addr_raw)

    # DB登録処理
    new_case = Case(
        case_number=temp_no,
        client_name=str(data.get("client_name") or "").strip(),
        client_name_kana=str(data.get("client_name_kana") or "").strip(),
        referral_sec_branch_name=branch_name,
        referral_sec_rep_name=data.get("referral_sec_rep_name", ""),
        referral_sec_phone=data.get("referral_sec_phone", ""),
        sol_case_number=data.get("sol_case_number", ""),
        created_at=datetime.now(),
    )
    session.add(new_case)
    session.flush()

    # 関連データ作成
    dec = Deceased(case_id=new_case.case_id, name_last="", name_first="")
    session.add(dec)
    session.flush()

    # Split client_name into last and first for the heir
    client_full_name = new_case.client_name
    client_full_kana = new_case.client_name_kana

    # Try splitting by full-width space first, then half-width space
    name_parts = client_full_name.replace(" ", "　").split("　", 1)
    heir_last_name = name_parts[0] if name_parts else ""
    heir_first_name = name_parts[1] if len(name_parts) > 1 else ""

    kana_parts = client_full_kana.replace(" ", "　").split("　", 1)
    heir_last_kana = kana_parts[0] if kana_parts else ""
    heir_first_kana = kana_parts[1] if len(kana_parts) > 1 else ""

    heir = Heir(
        deceased_id=dec.id,
        name_last=heir_last_name,
        name_first=heir_first_name,
        name_last_kana=heir_last_kana,
        name_first_kana=heir_first_kana,
        is_contracting_party=True,
    )
    session.add(heir)
    session.flush()

    addr = Address(zip_code=zip_code, prefecture="", street_address=addr_raw)
    session.add(addr)
    session.flush()

    session.add(
        H_AddressHistory(
            heir_id=heir.id,
            address_id=addr.id,
            is_current_address=True,
        )
    )

    # 電話番号
    if data.get("client_phone"):
        ct = Contact(value=data.get("client_phone"), type="PHONE")
        session.add(ct)
        session.flush()
        session.add(H_ContactLink(heir_id=heir.id, contact_id=ct.id))

    session.commit()

    return {
        "case": new_case,
        "dec": dec,
        "heir": heir,
        "addr": addr,
        "base": assigned_base,
        "temp_no": temp_no,
    }


def merge_heirs_to_existing_case(session, case_id: int, heirs_data: list) -> int:
    """既存案件に相続人リストを追加する処理"""
    case = session.query(Case).options(joinedload(Case.deceased_ref)).get(case_id)
    if not case or not case.deceased_ref:
        return 0

    deceased_id = case.deceased_ref.id
    added_count = 0

    # 既存チェック用
    existing_heirs = session.query(Heir).filter_by(deceased_id=deceased_id).all()
    existing_names = {
        f"{h.name_last}{h.name_first}".replace(" ", "").replace("　", "")
        for h in existing_heirs
    }

    for h_data in heirs_data:
        raw_name = h_data.get("name", "")
        clean_name = raw_name.replace(" ", "").replace("　", "")

        if not clean_name or clean_name in existing_names:
            continue

        # 登録実行 (住所などは簡易登録)
        # add_heir ヘルパーを使用
        try:
            # 住所分割
            addr_val = h_data.get("address", "")
            zip_val = search_zip_by_address_api(addr_val)

            # 生年月日
            dob_val = h_data.get("dob")

            # 連絡先
            phone_val = h_data.get("phone")
            contacts = [{"value": phone_val}] if phone_val else []

            add_heir(
                deceased_id=deceased_id,
                name=raw_name,
                rel=h_data.get("relationship", ""),
                # カナ名を姓と名に分割して渡す
                kana_full=str(h_data.get("kana") or "")
                .strip()
                .replace(" ", "　"),  # Ensure it's a string
                kana_parts=kana_full.split("　", 1),
                kana_last=kana_parts[0] if kana_parts else "",
                kana_first=kana_parts[1] if len(kana_parts) > 1 else "",
                dob=dob_val,
                # 住所
                zip_code=zip_val,
                pref="",
                street=addr_val,  # streetに全住所を入れる
                # 連絡先
                phone_contacts=contacts,
            )
            added_count += 1
            existing_names.add(clean_name)

        except Exception as e:
            st.error(f"登録エラー ({raw_name}): {e}")

    return added_count


def main():
    st.title("📄 書類読取 & 案件登録エージェント")
    st.caption(
        "「顧客紹介連絡表」の新規登録、または「推定相続人連絡先一覧」の既存案件への紐付けを行います。"
    )

    # --- セッションステート初期化 ---
    if "ocr_result" not in st.session_state:
        st.session_state["ocr_result"] = None
    if "candidate_cases" not in st.session_state:
        st.session_state["candidate_cases"] = []
    if "target_case_id" not in st.session_state:
        st.session_state["target_case_id"] = None
    if "process_mode" not in st.session_state:
        st.session_state["process_mode"] = None  # 'NEW' or 'MERGE'

    # --- ファイルアップロード ---
    uploaded_file = st.file_uploader(
        "書類 (PDF/画像) をアップロード",
        type=["pdf", "png", "jpg", "jpeg"],
        key="uploader_main",
    )

    if not uploaded_file:
        # リセット
        st.session_state["ocr_result"] = None
        st.session_state["candidate_cases"] = []
        return

    # ファイル処理
    file_bytes = uploaded_file.getvalue()
    mime_type = uploaded_file.type
    display_img = None

    if mime_type == "application/pdf":
        images = convert_from_bytes(file_bytes, dpi=200, first_page=1, last_page=1)
        if images:
            display_img = images[0]
            buf = BytesIO()
            display_img.save(buf, format="JPEG")
            # 解析用にはJPEGバイナリを使用
            target_bytes = buf.getvalue()
            mime_type = "image/jpeg"
        else:
            st.error("PDFの読み込みに失敗しました")
            return
    else:
        display_img = Image.open(BytesIO(file_bytes))
        target_bytes = file_bytes

    # --- レイアウト ---
    col_l, col_r = st.columns([1, 1.2])

    with col_l:
        st.image(display_img, caption="プレビュー", use_container_width=True)

    with col_r:
        # 1. 解析実行ボタン
        # 1. AI解析の自動実行
        if st.session_state["ocr_result"] is None and uploaded_file is not None:
            with st.spinner("Geminiが内容を読み取っています..."):
                res = analyze_document_gemini(target_bytes, mime_type)
                st.session_state["ocr_result"] = res

                # 自動検索実行
                search_key = res.get("search_key_name", "").strip()
                if search_key:
                    # 顧客名 or 被相続人名 で検索
                    hits = find_cases_by_attributes(client_name=search_key)
                    if not hits:
                        hits = find_cases_by_attributes(deceased_name=search_key)
                    st.session_state["candidate_cases"] = hits

                st.rerun()
            st.info(
                "⬆️ ファイルをアップロードしてAI解析が自動開始されました。"
            )  # Added info message

        # 2. 解析後のフロー
        if st.session_state["ocr_result"]:
            data = st.session_state["ocr_result"]
            doc_type = data.get("doc_type", "unknown")

            # 抽出された漢字氏名とフリガナをクリーンアップ
            if "client_name" in data and "client_name_kana" in data:
                data["client_name"] = _clean_kanji_name_by_kana(
                    data["client_name"], data["client_name_kana"]
                )
            if (
                "search_key_name" in data and "client_name_kana" in data
            ):  # search_key_nameも同様に修正
                data["search_key_name"] = _clean_kanji_name_by_kana(
                    data["search_key_name"], data["client_name_kana"]
                )

            # 相続人リストがある場合も個別の氏名をクリーンアップ
            if doc_type == "heir_list" and "heirs" in data:
                for heir in data["heirs"]:
                    if "name" in heir and "kana" in heir:
                        heir["name"] = _clean_kanji_name_by_kana(
                            heir["name"], heir["kana"]
                        )

            search_key = data.get("search_key_name", "不明")

            st.success(f"✅ 読取完了: {search_key} 様 ({doc_type})")

            # --- 案件選択フェーズ ---
            candidates = st.session_state["candidate_cases"]
            db = DatabaseManager()
            session = db._get_session()

            target_id = st.session_state["target_case_id"]
            mode = st.session_state["process_mode"]

            if target_id is None and mode is None:
                st.subheader("🔍 処理対象の選択")

                if candidates:
                    st.info(f"💡 既存の案件候補が {len(candidates)} 件見つかりました。")

                    # 選択肢の作成
                    options = {
                        f"【{c['case_number']}】 依頼者:{c['client_name']} (被相続人:{c['deceased_name']})": c[
                            "case_id"
                        ]
                        for c in candidates
                    }
                    options["🆕 新規案件として登録する"] = "NEW"

                    selected_label = st.radio("アクションを選択", list(options.keys()))

                    if st.button("決定", type="primary"):
                        val = options[selected_label]
                        if val == "NEW":
                            st.session_state["process_mode"] = "NEW"
                        else:
                            st.session_state["process_mode"] = "MERGE"
                            st.session_state["target_case_id"] = val
                        st.rerun()
                else:
                    st.warning("該当する既存案件は見つかりませんでした。")
                    if st.button("🆕 新規案件として登録する", type="primary"):
                        st.session_state["process_mode"] = "NEW"
                        st.rerun()

            # --- 処理実行フェーズ ---
            elif mode == "MERGE":
                # 既存案件への紐付け (主に相続人リスト追加)
                case = session.query(Case).get(target_id)

                if case:
                    st.info(f"📂 紐付け先: **{case.case_number} {case.client_name}**")
                else:
                    st.error(
                        f"エラー: 選択された案件 (ID: {target_id}) が見つかりませんでした。"
                    )
                    if st.button("最初に戻る"):
                        st.session_state.clear()
                        st.rerun()
                    st.stop()

                if doc_type == "heir_list":
                    heirs = data.get("heirs", [])
                    st.write(f"検出された相続人: {len(heirs)} 名")
                    st.dataframe(heirs)

                    if st.button("💾 この案件に相続人を追加登録"):
                        count = merge_heirs_to_existing_case(session, target_id, heirs)
                        if count > 0:
                            st.success(f"{count} 名の相続人を追加しました！")
                        else:
                            st.info(
                                "追加対象はありませんでした（重複またはデータなし）。"
                            )

                        time.sleep(2)
                        # クリアして戻る
                        st.session_state.clear()
                        st.rerun()
                else:
                    st.warning(
                        "この書類タイプは既存案件へのマージに対応していません（開発中）。"
                    )
                    if st.button("最初に戻る"):
                        st.session_state.clear()
                        st.rerun()

            elif mode == "NEW":
                # 新規登録 (主に紹介連絡表)
                st.subheader("📝 新規案件登録")

                with st.form("new_reg_form"):
                    # フォーム内容はAI結果で埋める
                    c1, c2 = st.columns(2)
                    name = c1.text_input("顧客名", value=data.get("client_name", ""))
                    kana = c2.text_input(
                        "フリガナ", value=data.get("client_name_kana", "")
                    )

                    addr = st.text_input(
                        "住所", value=data.get("client_address_full", "")
                    )

                    r1, r2 = st.columns(2)
                    br = r1.text_input(
                        "紹介元支店", value=data.get("referral_sec_branch_name", "")
                    )
                    rep = r2.text_input(
                        "紹介元担当者", value=data.get("referral_sec_rep_name", "")
                    )

                    sol = st.text_input(
                        "SOL案件No", value=data.get("sol_case_number", "")
                    )

                    if st.form_submit_button("✅ 登録＆Kintoneデータ生成"):
                        # データを補正して登録関数へ
                        reg_data = data.copy()
                        reg_data["client_name"] = name
                        reg_data["client_name_kana"] = katakana_to_hiragana(
                            kana
                        )  # ★カタカナをひらがなに変換
                        reg_data["client_address_full"] = addr
                        reg_data["referral_sec_branch_name"] = br
                        reg_data["referral_sec_rep_name"] = rep
                        reg_data["sol_case_number"] = sol

                        res = register_new_referral_case(session, reg_data)

                        st.session_state["registered_case_data"] = res
                        st.success(f"登録しました！ 仮番号: {res['temp_no']}")
                        st.rerun()

        # 3. 完了後の表示 (Kintone JSON)
        if "registered_case_data" in st.session_state:
            res = st.session_state["registered_case_data"]
            st.divider()
            st.subheader("📋 Kintone登録用データ")

            # Kintone生成の前に、Detached状態のオブジェクトを現在のセッションにマージする
            case_obj = session.merge(res["case"])
            dec_obj = session.merge(res["dec"]) if res["dec"] else None
            heir_obj = session.merge(res["heir"]) if res["heir"] else None
            addr_obj = session.merge(res["addr"]) if res["addr"] else None

            kintone_json = generate_kintone_json_payload(
                case_obj, dec_obj, heir_obj, addr_obj
            )
            st.code(
                json.dumps(kintone_json, ensure_ascii=False, indent=2), language="json"
            )

            if st.button("次の書類を読み込む"):
                st.session_state.clear()
                st.rerun()
            session.close()


if __name__ == "__main__":
    main()
