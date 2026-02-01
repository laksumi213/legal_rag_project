# src/legal_system/ui/pages/12_残高証明発行.py

import os
import sys
from datetime import datetime
from io import BytesIO

import streamlit as st
from pypdf import PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ==========================================
# 1. パス解決 & 初期設定
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager

# テンプレート保存ディレクトリ
TEMPLATES_DIR = os.path.join(ROOT_DIR, "data", "templates")

# ページ設定
st.set_page_config(layout="wide", page_title="残高証明発行", page_icon="📄")

# フォント設定
FONT_PATH = os.path.join(ROOT_DIR, "data", "fonts", "ipaexg.ttf")
try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont("IPAexG", FONT_PATH))
except Exception:
    pass

db = DatabaseManager()


# ==========================================
# 2. ヘルパー関数 (仮)
# ==========================================
# TODO: 実際にはdocument_generation_service.pyに移動
def generate_balance_certificate_request_pdf(
    case_id: int, financial_asset_id: int, file_hash: str
) -> BytesIO:
    st.warning("PDF生成ロジックはまだ実装されていません。")
    # ここにPDF生成ロジックを実装する
    # 仮の空PDFを返す
    output = PdfWriter()
    output.add_blank_page(width=612, height=792)
    output_stream = BytesIO()
    output.write(output_stream)
    output_stream.seek(0)
    return output_stream


# ==========================================
# 3. Streamlit UI
# ==========================================

st.title("📄 残高証明発行依頼書 生成")
st.write("データベースのデータを用いて金融機関宛の残高証明発行依頼書を生成します。")

# 案件選択
all_cases = db.get_all_cases()  # Assuming this method exists
case_options = {f"{c.case_number}: {c.client_name}": c.case_id for c in all_cases}
selected_case_label = st.selectbox("案件を選択", list(case_options.keys()))

selected_case_id = case_options[selected_case_label] if selected_case_label else None

if selected_case_id:
    st.subheader("預貯金口座の選択")
    financial_assets = db.get_financial_assets_by_case_id(
        selected_case_id
    )  # Assuming this method exists
    if financial_assets:
        asset_options = {
            f"{a.bank_ref.bank_name} - {a.branch_ref.branch_name} - {a.account_type_ref.type_name} ({a.account_number})": a.id
            for a in financial_assets
        }
        selected_asset_label = st.selectbox("口座を選択", list(asset_options.keys()))
        selected_financial_asset_id = (
            asset_options[selected_asset_label] if selected_asset_label else None
        )
    else:
        st.warning("この案件には預貯金口座情報が登録されていません。")
        selected_financial_asset_id = None

    st.subheader("PDFテンプレートの選択")
    template_files = db.get_all_files()  # Assuming this gets FileRegistry entries
    pdf_templates = {
        f["filename"]: f
        for f in template_files
        if f["filename"].lower().endswith(".pdf")
    }

    if pdf_templates:
        selected_template_name = st.selectbox(
            "テンプレートファイルを選択", list(pdf_templates.keys())
        )
        selected_template_hash = (
            pdf_templates[selected_template_name]["file_hash"]
            if selected_template_name
            else None
        )
    else:
        st.warning("登録済みのPDFテンプレートファイルがありません。")
        selected_template_hash = None

    if st.button("残高証明発行依頼書を生成", type="primary"):
        if selected_case_id and selected_financial_asset_id and selected_template_hash:
            with st.spinner("PDFを生成中..."):
                generated_pdf_bytes = generate_balance_certificate_request_pdf(
                    selected_case_id,
                    selected_financial_asset_id,
                    selected_template_hash,
                )
                st.download_button(
                    label="📥 生成されたPDFをダウンロード",
                    data=generated_pdf_bytes.getvalue(),
                    file_name=f"残高証明発行依頼書_{selected_case_label.split(':')[0].strip()}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
                st.success("PDFが生成されました。")
        else:
            st.error("案件、預貯金口座、テンプレートファイルを全て選択してください。")

else:
    st.info("案件を選択してください。")


if __name__ == "__main__":
    # main関数は不要（Streamlitが自動でスクリプトを実行するため）
    pass
