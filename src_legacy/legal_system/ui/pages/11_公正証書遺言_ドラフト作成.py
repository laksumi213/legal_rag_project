# src/legal_system/ui/pages/11_公正証書遺言_ドラフト作成.py

import os
import sys
from io import BytesIO

import numpy as np
import pandas as pd
import streamlit as st

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from services.automation.will_generator import WillDraftGenerator


def main():
    st.set_page_config(page_title="遺言ドラフト作成", page_icon="📜", layout="wide")
    st.title("📜 公正証書遺言 自動起案システム")

    # --- セッションステート初期化 ---
    if "generated_data" not in st.session_state:
        st.session_state["generated_data"] = None

    col_input, col_action = st.columns([1, 1])

    with col_input:
        with st.container(border=True):
            st.subheader("1. 素材データのアップロード")
            uploaded_excel = st.file_uploader(
                "① 遺言内容要旨 (Excel/CSV)", type=["xlsx", "csv"]
            )

            st.markdown("---")
            use_default = st.checkbox("サーバー内の標準テンプレートを使用", value=True)
            uploaded_template = None
            if not use_default:
                uploaded_template = st.file_uploader(
                    "② 雛形テンプレート (Word)", type=["docx"]
                )

            st.markdown("---")
            uploaded_images = st.file_uploader(
                "③ 不動産登記情報 (PDF/画像) ※任意",
                type=["png", "jpg", "jpeg", "pdf"],
                accept_multiple_files=True,
                help="PDFは自動で画像化され、「別冊」として出力されます。",
            )

    with col_action:
        st.subheader("2. 生成実行 & プレビュー")

        if uploaded_excel:
            try:
                if uploaded_excel.name.endswith(".xlsx"):
                    df_preview = pd.read_excel(uploaded_excel)
                else:
                    df_preview = pd.read_csv(uploaded_excel)

                df_preview = df_preview.replace(r"^\s*$", np.nan, regex=True).ffill()
                if "No" in df_preview.columns:
                    df_preview = df_preview.dropna(subset=["No"])

                st.info(f"📋 要旨データ確認: {len(df_preview)} 行")
                st.dataframe(df_preview, height=200, use_container_width=True)
            except Exception as e:
                st.error(f"プレビューエラー: {e}")

            st.markdown("---")

            # --- 生成ボタン処理 ---
            if st.button(
                "🚀 AIドラフト生成を開始", type="primary", use_container_width=True
            ):
                template_source = None
                if use_default:
                    default_path = os.path.join(
                        ROOT_DIR,
                        "data",
                        "templates",
                        "遺言公正証書文案テンプレート.docx",
                    )
                    if os.path.exists(default_path):
                        with open(default_path, "rb") as f:
                            template_source = BytesIO(f.read())
                    else:
                        st.error(f"❌ 標準テンプレートなし: {default_path}")
                        st.stop()
                elif uploaded_template:
                    template_source = uploaded_template
                else:
                    st.error("テンプレートを指定してください")
                    st.stop()

                registry_files = uploaded_images if uploaded_images else []

                generator = WillDraftGenerator()
                with st.spinner("🤖 AI思考 & 文書作成中..."):
                    try:
                        uploaded_excel.seek(0)
                        if hasattr(template_source, "seek"):
                            template_source.seek(0)

                        # 生成実行
                        doc_io, reg_io, ai_data, csv_debug = generator.generate_draft(
                            uploaded_excel, template_source, registry_files
                        )

                        # ★結果をセッションステートに保存（これでボタンを押しても消えなくなる）
                        st.session_state["generated_data"] = {
                            "doc_io": doc_io,
                            "reg_io": reg_io,
                            "ai_data": ai_data,
                            "timestamp": pd.Timestamp.now().strftime("%Y%m%d"),
                        }

                        st.success("✅ 生成完了！")
                        st.balloons()

                    except Exception as e:
                        st.error(f"エラー: {e}")
                        st.exception(e)

        # --- ダウンロードエリア（セッションにデータがあれば常に表示） ---
        if st.session_state["generated_data"]:
            data = st.session_state["generated_data"]

            st.divider()
            st.markdown("### 📥 ダウンロード")

            # デバッグ情報
            with st.expander("🔍 生成結果の詳細を確認", expanded=False):
                st.json(data["ai_data"].model_dump())

            c_dl1, c_dl2 = st.columns(2)

            # 1. 遺言書本体
            c_dl1.download_button(
                label="📥 遺言書ドラフト (本体)",
                data=data["doc_io"],
                file_name=f"遺言書ドラフト_{data['timestamp']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True,
                key="dl_btn_main",  # キーを指定して競合回避
            )

            # 2. 登記情報別冊 (ある場合のみ)
            if data["reg_io"]:
                c_dl2.download_button(
                    label="📥 登記情報 (別冊)",
                    data=data["reg_io"],
                    file_name=f"登記情報別冊_{data['timestamp']}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="dl_btn_reg",
                )


if __name__ == "__main__":
    main()
