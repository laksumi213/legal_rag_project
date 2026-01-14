# src/legal_system/ui/pages/05_顧客紹介連絡表_読取.py

import os
import re
import sys
from datetime import datetime
import streamlit as st
from pdf2image import convert_from_bytes

ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case
from legal_system.core.pdf_processor import analyze_referral_pdf

st.set_page_config(page_title="顧客紹介連絡表 読取", page_icon="🤝", layout="wide")

def get_next_case_number(session) -> str:
    """G番号をDBから取得して自動採番"""
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
    return f"G{max_num + 1:04d}"

def main():
    st.title("🤝 顧客紹介連絡表 読取・登録")
    st.caption("紹介連絡表(PDF)から顧客情報・紹介元情報を自動抽出します。")

    db = DatabaseManager()
    session = db._get_session()

    # 1. アップロードエリア
    with st.container(border=True):
        col_file, col_mode = st.columns([1.5, 1])
        with col_file:
            uploaded_file = st.file_uploader("📂 PDFをアップロード", type=["pdf"])
        with col_mode:
            st.write("⚙️ **登録モード**")
            mode = st.radio("選択", ["🆕 新規登録", "📂 既存案件に追加"], label_visibility="collapsed")

    if not uploaded_file:
        session.close()
        return

    # 2. プレビュー画像の生成
    file_bytes = uploaded_file.read()
    display_img = None
    try:
        images = convert_from_bytes(file_bytes, dpi=150, first_page=1, last_page=1)
        display_img = images[0]
    except:
        pass

    # 3. 解析実行
    if st.session_state.get("current_file") != uploaded_file.name:
        st.session_state["ocr_res"] = None
        st.session_state["current_file"] = uploaded_file.name

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button("🔍 解析を実行する", type="primary", use_container_width=True):
            with st.spinner("解析中... (値が空の場合はOCRを自動実行します)"):
                res = analyze_referral_pdf(file_bytes)
                st.session_state["ocr_res"] = res
                
                debug_mode = res.get("_debug_mode", "")
                if "OCR" in debug_mode:
                    st.toast("📷 画像解析(OCR)を実行しました", icon="⚠️")
                else:
                    st.toast("✨ テキストデータを読み取りました", icon="✅")

    # 4. 結果表示 & 編集フォーム
    st.divider()
    ocr_data = st.session_state.get("ocr_res", {})

    # 2カラムレイアウト: 左に画像、右にフォーム
    col_img, col_form = st.columns([1, 1.2])

    # --- 左カラム: プレビュー ---
    with col_img:
        st.subheader("📄 原本プレビュー")
        if display_img:
            st.image(display_img, use_container_width=True)
        else:
            st.info("プレビューを表示できません")

    # --- 右カラム: 入力フォーム ---
    with col_form:
        st.subheader("📝 データ確認・登録")
        
        # デバッグ用
        if ocr_data:
            with st.expander("🛠️ 解析テキストデータ (Debug)"):
                st.text(ocr_data.get("_debug_raw_text", ""))
                st.caption(f"Mode: {ocr_data.get('_debug_mode')}")

        with st.form("referral_form"):
            col1, col2 = st.columns(2)
            
            # 案件番号
            case_no = get_next_case_number(session) if mode == "🆕 新規登録" else ""
            col1.text_input("案件番号(G番号)", value=case_no, disabled=True)
            
            # 氏名関連
            name = col1.text_input("顧客名", value=ocr_data.get("client_name", ""))
            kana = col2.text_input("フリガナ", value=ocr_data.get("client_name_kana", ""))
            
            # 連絡先
            phone1 = col1.text_input("電話番号1", value=ocr_data.get("client_phone_1", ""))
            phone2 = col2.text_input("電話番号2", value=ocr_data.get("client_phone_2", ""))
            addr = st.text_input("住所", value=ocr_data.get("client_address", ""))
            
            st.markdown("---")
            # 紹介元
            c1, c2, c3 = st.columns(3)
            sol = c1.text_input("SOL案件番号", value=ocr_data.get("sol_case_number", ""))
            branch = c2.text_input("支店名", value=ocr_data.get("referral_sec_branch_name", ""))
            rep = c3.text_input("担当者名", value=ocr_data.get("referral_sec_rep_name", ""))
            
            intro_date = st.text_input("紹介日", value=ocr_data.get("introduction_date", ""))

            if st.form_submit_button("💾 データベースに保存", type="primary"):
                try:
                    if mode == "🆕 新規登録":
                        new_case = Case(
                            case_number=case_no,
                            client_name=name,
                            client_name_kana=kana,
                            client_phone=phone1,
                            client_phone_2=phone2,
                            client_address=addr,
                            sol_case_number=sol,
                            referral_sec_branch_name=branch,
                            referral_sec_rep_name=rep,
                            created_at=datetime.now()
                        )
                        session.add(new_case)
                        session.commit()
                        st.success(f"案件 {case_no} を登録しました")
                        st.balloons()
                    else:
                        st.info("既存案件への追加ロジックは必要に応じて実装してください。")
                except Exception as e:
                    session.rollback()
                    st.error(f"エラー: {e}")

    session.close()

if __name__ == "__main__":
    main()