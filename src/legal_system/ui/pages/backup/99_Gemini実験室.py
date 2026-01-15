# src/legal_system/ui/pages/99_Gemini実験室.py

import base64
import os
import sys
from io import BytesIO

import streamlit as st
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pdf2image import convert_from_bytes
from PIL import Image

# パス解決
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
sys.path.append(ROOT_DIR)

st.set_page_config(page_title="Gemini実験室", page_icon="🧪", layout="wide")

def main():
    st.title("🧪 Gemini Vision 実験室 (シンプル読取版)")
    st.markdown("""
    OCRエンジンを使わず、**Geminiに直接「画像」を見せて**情報を読み取らせる実験ページです。
    
    ⚠️ **注意**
    マスキング機能はありません。
    **必ず「架空の人物」や「ダミーデータ」のPDF/画像のみを使用してください。**
    """)

    # APIキー確認
    if not os.getenv("GOOGLE_API_KEY"):
        st.error("❌ GOOGLE_API_KEY が設定されていません。")
        return

    # 1. ファイルアップロード
    uploaded_file = st.file_uploader(
        "帳票画像/PDFをアップロード (ダミーデータ限定)", type=["pdf", "png", "jpg", "jpeg"]
    )

    if uploaded_file:
        pil_image = None
        
        # PDFか画像かで読み込み処理を分岐
        if uploaded_file.type == "application/pdf":
            try:
                with st.spinner("PDFを画像に変換中..."):
                    # 1ページ目のみ取得
                    images = convert_from_bytes(uploaded_file.read(), dpi=200, first_page=1, last_page=1)
                    pil_image = images[0]
            except Exception as e:
                st.error(f"PDF変換エラー: {e}")
                st.info("Windowsの場合はPopplerがインストールされているか確認してください。")
                return
        else:
            pil_image = Image.open(uploaded_file)

        if pil_image:
            # 2. 画像プレビュー
            st.divider()
            col_img, col_result = st.columns([1, 1])
            
            with col_img:
                st.subheader("📄 アップロード画像")
                st.image(pil_image, use_container_width=True)

            # 3. 解析実行
            with col_result:
                st.subheader("🤖 AI解析結果")
                
                if st.button("🚀 Geminiで読み取る", type="primary", use_container_width=True):
                    # 画像をBase64化 (API送信のため)
                    buffered = BytesIO()
                    # 形式をJPEGに統一して軽量化
                    pil_image.convert("RGB").save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    
                    with st.spinner("Geminiが画像を解析中..."):
                        try:
                            # モデル初期化 (Gemini 1.5 Flash 推奨)
                            llm = ChatGoogleGenerativeAI(
                                model="gemini-2.5-flash", 
                                temperature=0.0
                            )

                            # プロンプト作成
                            prompt_text = """
                            この帳票画像を読み取り、以下の項目を抽出してJSON形式で出力してください。
                            項目が見つからない、または空欄の場合は空文字にしてください。

                            {
                                "顧客名": "",
                                "フリガナ": "",
                                "電話番号1": "",
                                "電話番号2": "",
                                "住所": "",
                                "SOL案件番号": "",
                                "紹介日": "",
                                "紹介元支店名": "",
                                "紹介元担当者名": ""
                            }
                            """

                            message = HumanMessage(content=[
                                {"type": "text", "text": prompt_text},
                                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_str}"}
                            ])

                            # 実行
                            response = llm.invoke([message])
                            
                            # 結果表示
                            st.success("解析完了")
                            st.code(response.content, language="json")

                        except Exception as e:
                            st.error(f"解析エラーが発生しました: {e}")

if __name__ == "__main__":
    main()