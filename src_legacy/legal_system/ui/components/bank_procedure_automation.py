import os
import sys
from datetime import date

import streamlit as st

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
sys.path.append(ROOT_DIR)

from legal_system.services.bank_procedure_service import BankProcedureService
from legal_system.ui.utils.js_helper import enable_keyboard_shortcuts

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case


def render_bank_procedure_automation() -> None:
    st.title("🏦 銀行手続き自動化")
    st.markdown("---")

    enable_keyboard_shortcuts(search_keyword="案件番号")

    if (
        "selected_case_id" not in st.session_state
        or not st.session_state.selected_case_id
    ):
        st.warning("⚠️ 案件が選択されていません。案件検索から案件を選択してください。")
        return

    case_id = int(st.session_state.selected_case_id)

    db = DatabaseManager()
    session = db._get_session()
    try:
        case = session.query(Case).get(case_id)
        if not case:
            st.error("案件が見つかりません。")
            return

        st.info(f"📋 案件番号: **{case.case_number}** | 依頼者: **{case.client_name}**")

        assets = db.get_financial_assets_by_case_id(case_id)
        if not assets:
            st.warning(
                "この案件には預貯金口座が登録されていません。（メニュー: 銀行口座 登録）"
            )
            return

        asset_options = {
            f"{a.bank_ref.bank_name if a.bank_ref else ''} - {a.branch_ref.branch_name if a.branch_ref else ''} - {a.account_type_ref.type_name if a.account_type_ref else ''} ({a.account_number or ''})": a.id
            for a in assets
        }
        selected_asset_label = st.selectbox("口座を選択", list(asset_options.keys()))
        selected_financial_asset_id = asset_options[selected_asset_label]

        col1, col2 = st.columns([1, 1])
        with col1:
            target_bank = st.selectbox(
                "対象銀行",
                ["みずほ銀行", "ゆうちょ銀行", "三菱UFJ銀行", "JA", "三井住友銀行"],
                index=0,
            )
        with col2:
            procedure_type = st.selectbox(
                "対象機能",
                ["残高証明書", "解約申請（相続届/口座凍結）"],
                index=0,
            )

        created_on = st.date_input("作成日", value=date.today())

        templates_dir = os.path.join(ROOT_DIR, "data", "templates")
        template_files = []
        if os.path.isdir(templates_dir):
            template_files = [
                os.path.join(templates_dir, f)
                for f in os.listdir(templates_dir)
                if f.lower().endswith(".pdf")
            ]
        template_files = sorted(template_files)

        template_label_to_path = {os.path.basename(p): p for p in template_files}

        selected_template_name = st.selectbox(
            "テンプレPDF",
            list(template_label_to_path.keys())
            if template_label_to_path
            else ["(テンプレなし)"],
        )
        template_path = template_label_to_path.get(selected_template_name)

        st.divider()

        if st.button("▶ 実行", type="primary"):
            if procedure_type != "残高証明書":
                st.warning("解約申請（Selenium）は次の実装ステップで対応します。")
                return

            if not template_path:
                st.error("テンプレPDFを選択してください。")
                return

            svc = BankProcedureService(db=db)
            try:
                if target_bank == "みずほ銀行":
                    result = svc.generate_mizuho_balance_certificate_pdf(
                        case_id=case_id,
                        financial_asset_id=selected_financial_asset_id,
                        template_path=template_path,
                        created_on=created_on,
                    )
                elif target_bank == "ゆうちょ銀行":
                    result = svc.generate_yucho_balance_certificate_pdf(
                        case_id=case_id,
                        financial_asset_id=selected_financial_asset_id,
                        template_path=template_path,
                        created_on=created_on,
                    )
                elif target_bank == "三菱UFJ銀行":
                    result = svc.generate_mufg_balance_certificate_pdf(
                        case_id=case_id,
                        financial_asset_id=selected_financial_asset_id,
                        template_path=template_path,
                        created_on=created_on,
                    )
                elif target_bank == "JA":
                    result = svc.generate_ja_balance_certificate_pdf(
                        case_id=case_id,
                        financial_asset_id=selected_financial_asset_id,
                        template_path=template_path,
                        created_on=created_on,
                    )
                elif target_bank == "三井住友銀行":
                    st.error("三井住友銀行は参照実装が無いため、追加資料提示待ちです。")
                    return
                else:
                    st.error("この銀行の残高証明PDFは未実装です。")
                    return

                st.download_button(
                    label="📥 生成PDFをダウンロード",
                    data=result.pdf_bytes,
                    file_name=result.filename,
                    mime="application/pdf",
                    use_container_width=True,
                )

                for k in [
                    "bank_proc_target_bank",
                    "bank_proc_procedure_type",
                    "bank_proc_asset",
                    "bank_proc_template",
                ]:
                    if k in st.session_state:
                        del st.session_state[k]

                st.success("完了しました。")
                st.rerun()
            except Exception as e:
                st.error(f"実行中にエラーが発生しました: {e}")
    finally:
        session.close()
