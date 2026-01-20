# src/legal_system/ui/pages/91_公正証書遺言_ドラフト作成.py

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from io import BytesIO

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.services.automation.will_generator import WillDraftGenerator

def main():
    st.set_page_config(page_title="遺言ドラフト作成", page_icon="📜", layout="wide")
    st.title("📜 公正証書遺言 自動起案システム")

    col_input, col_action = st.columns([1, 1])
    
    with col_input:
        with st.container(border=True):
            st.subheader("1. 素材データのアップロード")
            uploaded_excel = st.file_uploader("① 遺言内容要旨 (Excel/CSV)", type=["xlsx", "csv"])
            
            st.markdown("---")
            use_default = st.checkbox("サーバー内の標準テンプレートを使用", value=True)
            uploaded_template = None
            if not use_default:
                uploaded_template = st.file_uploader("② 雛形テンプレート (Word)", type=["docx"])
            
            st.markdown("---")
            uploaded_images = st.file_uploader(
                "③ 不動産登記情報 (PDF/画像) ※任意", 
                type=["png", "jpg", "jpeg", "pdf"], 
                accept_multiple_files=True,
                help="PDFは自動で画像化・テキスト抽出され、余白をカットしてWordに貼られます。"
            )

    with col_action:
        st.subheader("2. 生成実行 & プレビュー")
        
        if uploaded_excel:
            try:
                if uploaded_excel.name.endswith('.xlsx'):
                    df_preview = pd.read_excel(uploaded_excel)
                else:
                    df_preview = pd.read_csv(uploaded_excel)
                
                df_preview = df_preview.replace(r'^\s*$', np.nan, regex=True).ffill()
                if 'No' in df_preview.columns:
                    df_preview = df_preview.dropna(subset=['No'])

                st.info(f"📋 要旨データ確認: {len(df_preview)} 行")
                st.dataframe(df_preview, height=200, use_container_width=True)
            except Exception as e:
                st.error(f"プレビューエラー: {e}")

            st.markdown("---")
            if st.button("🚀 AIドラフト生成を開始", type="primary", use_container_width=True):
                # テンプレート準備
                template_source = None
                if use_default:
                    default_path = os.path.join(ROOT_DIR, "data", "templates", "遺言公正証書文案テンプレート.docx")
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

                # ファイルリスト作成（生のまま渡す）
                registry_files = []
                if uploaded_images:
                    registry_files = uploaded_images

                # 生成実行
                generator = WillDraftGenerator()
                with st.spinner("🤖 AI思考 & 文書作成中..."):
                    try:
                        uploaded_excel.seek(0)
                        if hasattr(template_source, 'seek'): template_source.seek(0)
                        
                        doc_io, ai_data, csv_debug = generator.generate_draft(uploaded_excel, template_source, registry_files)
                        
                        st.success("✅ 生成完了！")
                        st.balloons()
                        
                        # --- デバッグ情報の表示 ---
                        with st.expander("🔍 生成結果の詳細を確認", expanded=True):
                            st.markdown("#### 生成された条文データ")
                            st.json(ai_data.model_dump())

                        st.download_button(
                            label="📥 Wordファイルをダウンロード",
                            data=doc_io,
                            file_name=f"遺言書ドラフト_{pd.Timestamp.now().strftime('%Y%m%d')}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            type="primary"
                        )
                        
                    except Exception as e:
                        st.error(f"エラー: {e}")
                        st.exception(e)

if __name__ == "__main__":
    main()