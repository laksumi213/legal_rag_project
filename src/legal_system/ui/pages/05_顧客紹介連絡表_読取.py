# src/legal_system/ui/pages/05_顧客紹介連絡表_読取.py

import os
import re
import sys
from datetime import datetime

import streamlit as st
from pdf2image import convert_from_bytes

# パス解決
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.core.ocr_engine import analyze_referral_contact_sheet
from legal_system.models.tables import Address, Case, CaseContactPoint, Contact

st.set_page_config(page_title="顧客紹介連絡表 読取", page_icon="🤝", layout="wide")


def get_next_case_number(session) -> str:
    cases = session.query(Case.case_number).all()
    max_num = 0
    pattern = re.compile(r"^G?(\d{4})$")
    for (c_num,) in cases:
        if c_num:
            match = pattern.match(c_num)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
    return f"{max_num + 1:04d}"


def split_address(full_address: str):
    if not full_address:
        return "", ""
    match = re.match(r"(...??[都道府県])(.*)", full_address)
    if match:
        return match.group(1), match.group(2)
    return "", full_address


def main():
    st.title("🤝 顧客紹介連絡表 読取・登録")

    db = DatabaseManager()
    session = db._get_session()

    with st.container(border=True):
        col_file, col_mode = st.columns([1.5, 1])
        with col_file:
            uploaded_file = st.file_uploader(
                "📂 顧客紹介連絡表(PDF)をアップロード", type=["pdf"]
            )
        with col_mode:
            st.write("⚙️ **登録モード**")
            mode = st.radio(
                "登録モード",
                ["🆕 新規案件登録 (仮)", "📂 既存案件に追加"],
                label_visibility="collapsed",
            )

    current_case_id = None
    next_num_str = None

    if mode == "🆕 新規案件登録 (仮)":
        next_num_str = get_next_case_number(session)
        st.info(f"💡 新規案件として登録します。自動採番: **{next_num_str}**")
    else:
        cases = session.query(Case).order_by(Case.case_number).all()
        if not cases:
            st.warning("登録済みの案件がありません。")
        else:
            case_opts = {f"{c.case_number}: {c.client_name}": c.case_id for c in cases}
            selected_case_label = st.selectbox(
                "追加する既存案件を選択", list(case_opts.keys())
            )
            if selected_case_label:
                current_case_id = case_opts[selected_case_label]

    if not uploaded_file:
        session.close()
        return

    # 画像変換
    file_bytes = uploaded_file.read()
    display_img = None
    try:
        images = convert_from_bytes(file_bytes, dpi=200, fmt="jpeg")
        display_img = images[0]
    except Exception as e:
        st.error(f"画像変換エラー: {e}")
        session.close()
        return

    # --- 解析実行 ---
    if st.session_state.get("last_uploaded_referral") != uploaded_file.name:
        st.session_state["referral_ocr_result"] = None
        st.session_state["last_uploaded_referral"] = uploaded_file.name

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        analyze_btn = st.button(
            "🔍 AI解析実行 (Local)", type="primary", use_container_width=True
        )

    if analyze_btn:
        with st.spinner("🤖 ローカルAIが画像を解析中... (Ollama)"):
            result = analyze_referral_contact_sheet(file_bytes)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state["referral_ocr_result"] = result
                st.toast("✅ 解析完了！", icon="🎉")

                # ▼▼▼ デバッグ画像表示エリア (更新) ▼▼▼
                with st.expander("🛠️ 解析デバッグ (AIが見た画像範囲)", expanded=True):
                    # 画像が戻り値に含まれていれば表示
                    if "_debug_images" in result:
                        imgs = result["_debug_images"]
                        st.caption("📷 **1. 顧客情報エリア (Top 20%〜45%)**")
                        st.image(imgs["top"], use_container_width=True)

                        st.caption("📷 **2. 担当者・SOLエリア (Bottom Split)**")
                        d1, d2 = st.columns(2)
                        d1.image(
                            imgs["left"],
                            caption="左下: 担当者/支店",
                            use_container_width=True,
                        )
                        d2.image(
                            imgs["right"],
                            caption="右下: SOL番号",
                            use_container_width=True,
                        )

                    st.caption("📝 読み取れたテキスト")
                    st.text_area(
                        "", value=result.get("_debug_raw_text", ""), height=150
                    )
                # ▲▲▲ ここまで ▲▲▲

    st.divider()

    # --- 編集フォーム ---
    col_img, col_data = st.columns([1, 1.2])
    with col_img:
        st.subheader("📄 原本プレビュー")
        st.image(display_img, use_container_width=True)

    with col_data:
        st.subheader("📝 データ確認・編集")
        ocr_data = st.session_state.get("referral_ocr_result", {})

        db_vals = {
            "name": "",
            "kana": "",
            "addr": "",
            "phone1": "",
            "phone2": "",
            "sol": "",
            "branch": "",
            "rep": "",
        }
        if mode == "📂 既存案件に追加" and current_case_id:
            ex = session.query(Case).filter_by(case_id=current_case_id).first()
            if ex:
                db_vals.update(
                    {
                        "name": ex.client_name,
                        "kana": ex.client_name_kana,
                        "phone1": ex.client_phone,
                        "phone2": ex.client_phone_2,
                        "addr": ex.client_address,
                        "sol": ex.sol_case_number,
                        "branch": ex.referral_sec_branch_name,
                        "rep": ex.referral_sec_rep_name,
                    }
                )

        def get_val(ocr_key, db_key=None):
            if ocr_data and ocr_data.get(ocr_key):
                return ocr_data[ocr_key]
            if db_key and db_vals.get(db_key):
                return str(db_vals[db_key])
            return ""

        with st.form("referral_reg_form"):
            st.markdown("##### 👤 顧客情報")
            if mode == "🆕 新規案件登録 (仮)":
                st.text_input("案件番号", value=next_num_str, disabled=True)

            c_name, c_kana = st.columns(2)
            new_name = c_name.text_input(
                "顧客名 (必須)", value=get_val("client_name", "name")
            )
            new_kana = c_kana.text_input(
                "フリガナ", value=get_val("client_name_kana", "kana")
            )

            c_ph1, c_ph2 = st.columns(2)
            new_phone1 = c_ph1.text_input(
                "電話番号1 (携帯)", value=get_val("client_phone", "phone1")
            )
            new_phone2 = c_ph2.text_input(
                "電話番号2 (固定等)", value=get_val("client_phone_2", "phone2")
            )

            new_addr = st.text_input("住所", value=get_val("client_address", "addr"))

            st.markdown("---")
            st.markdown("##### 🏢 紹介元・担当者")

            c1, c2 = st.columns(2)
            new_sol = c1.text_input(
                "SOL案件番号", value=get_val("sol_case_number", "sol")
            )
            new_intro = c2.text_input(
                "紹介日", value=get_val("introduction_date"), help="YYYY-MM-DD"
            )

            c3, c4 = st.columns(2)
            new_branch = c3.text_input(
                "支店名", value=get_val("referral_sec_branch_name", "branch")
            )
            new_rep = c4.text_input(
                "担当者名", value=get_val("referral_sec_rep_name", "rep")
            )

            new_consent = st.text_input("同意書 受領日", value=get_val("consent_date"))

            submitted = st.form_submit_button(
                "💾 保存する", type="primary", use_container_width=True
            )

            if submitted:
                if not new_name:
                    st.error("❌ 顧客名を入力してください。")
                elif mode == "📂 既存案件に追加" and not current_case_id:
                    st.error("❌ 案件を選択してください。")
                else:
                    try:
                        tgt = None
                        if mode == "🆕 新規案件登録 (仮)":
                            if (
                                session.query(Case)
                                .filter_by(case_number=next_num_str)
                                .first()
                            ):
                                raise Exception("Duplicate")
                            tgt = Case(
                                case_number=next_num_str,
                                client_name=new_name,
                                created_at=datetime.now(),
                            )
                            session.add(tgt)
                            session.flush()
                        else:
                            tgt = (
                                session.query(Case)
                                .filter_by(case_id=current_case_id)
                                .first()
                            )

                        tgt.client_name = new_name
                        tgt.client_name_kana = new_kana
                        tgt.client_address = new_addr
                        tgt.client_phone = new_phone1
                        tgt.client_phone_2 = new_phone2

                        tgt.sol_case_number = new_sol
                        tgt.referral_sec_branch_name = new_branch
                        tgt.referral_sec_rep_name = new_rep

                        def parse_dt(d):
                            if not d:
                                return None
                            for f in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"]:
                                try:
                                    return datetime.strptime(d, f).date()
                                except:
                                    continue
                            return None

                        if new_intro:
                            tgt.introduction_date = parse_dt(new_intro)
                        if new_consent:
                            tgt.consent_date = parse_dt(new_consent)

                        # 正規化同期
                        cp = None
                        if tgt.contact_points:
                            cp = next(
                                (x for x in tgt.contact_points if x.is_primary_contact),
                                tgt.contact_points[0],
                            )

                        if not cp:
                            cp = CaseContactPoint(
                                case_id=tgt.case_id, is_primary_contact=True
                            )
                            session.add(cp)
                            session.flush()

                        cp.contact_person_name = new_name

                        if new_addr:
                            pref, rest = split_address(new_addr)
                            if cp.address_ref:
                                cp.address_ref.prefecture = pref
                                cp.address_ref.street_address = rest
                            else:
                                a_obj = Address(prefecture=pref, street_address=rest)
                                session.add(a_obj)
                                session.flush()
                                cp.address_id = a_obj.id

                        if new_phone1:
                            if cp.contact_ref:
                                cp.contact_ref.value = new_phone1
                            else:
                                c_obj = Contact(type="PHONE", value=new_phone1)
                                session.add(c_obj)
                                session.flush()
                                cp.contact_id = c_obj.id

                        session.commit()
                        st.success(f"✅ {tgt.client_name} 様の情報を保存しました！")
                        st.balloons()

                    except Exception as e:
                        session.rollback()
                        st.error(f"保存エラー: {e}")

    session.close()


if __name__ == "__main__":
    main()
