# src/legal_system/ui/pages/98_Llama実験室.py

import base64
import os
import sys
from io import BytesIO

import streamlit as st
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_bytes
from PIL import Image

# パス解決
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
sys.path.append(ROOT_DIR)

st.set_page_config(page_title="Llama Vision 実験室", page_icon="🦙", layout="wide")

def main():
    st.title("🦙 Llama(Local) Vision 実験室")
    st.markdown("""
    クラウドを使わず、**ローカルPC内のAI（Ollama）**で画像を読み取る実験ページです。
    個人情報を含むファイルでも安全にテストできます。
    
    ※ 事前にターミナルで `ollama pull llava` を実行して、視覚対応モデルを入れておく必要があります。
    """)

    # サイドバーでモデル選択
    model_name = st.sidebar.selectbox(
        "使用するVisionモデル",
        ["llava", "llama3.2-vision", "moondream"],
        index=0
    )

    # 1. ファイルアップロード
    uploaded_file = st.file_uploader(
        "帳票画像/PDFをアップロード", type=["pdf", "png", "jpg", "jpeg"]
    )

    if uploaded_file:
        pil_image = None
        
        # PDFか画像かで読み込み処理を分岐
        if uploaded_file.type == "application/pdf":
            try:
                with st.spinner("PDFを画像に変換中..."):
                    # 1ページ目のみ取得
                    images = convert_from_bytes(uploaded_file.read(), dpi=150, first_page=1, last_page=1)
                    pil_image = images[0]
            except Exception as e:
                st.error(f"PDF変換エラー: {e}")
                return
        else:
            pil_image = Image.open(uploaded_file)

        if pil_image:
            # 2. 画像プレビュー
            st.divider()
            col_img, col_result = st.columns([1, 1])
            
            with col_img:
                st.subheader("📄 対象画像")
                st.image(pil_image, use_container_width=True)

            # 3. 解析実行
            with col_result:
                st.subheader("🤖 Local AI解析結果")
                
                if st.button("🚀 Llama(Ollama)で読み取る", type="primary", use_container_width=True):
                    # 画像をBase64化
                    buffered = BytesIO()
                    # JPEGに変換して軽量化（ローカルLLMは重いため）
                    pil_image.convert("RGB").save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    
                    with st.spinner(f"ローカルAI ({model_name}) が画像を解析中... PCが重くなる可能性があります"):
                        try:
                            # Ollamaの初期化
                            llm = ChatOllama(
                                model=model_name,
                                temperature=0.0,
                                # JSONモードを強制しないほうがVisionモデルでは安定することがあるが、
                                # 構造化データが欲しいので指示で頑張らせる
                            )

                            # プロンプト作成
                            # ローカルモデルは日本語指示よりも英語指示の方が精度が出る傾向があるため、
                            # 内部プロンプトは英語にしつつ、出力は日本語JSONを要求するテクニックを使います。
                            prompt_text = """
                            You are an OCR assistant. Look at this document image and extract the following information into a JSON format.
                            If a field is not found, use an empty string "".
                            
                            Fields to extract:
                            - ClientName (顧客名)
                            - ClientNameKana (フリガナ)
                            - PhoneNumber (電話番号)
                            - Address (住所)
                            - SOL_CaseNumber (SOL案件番号)
                            - ReferralDate (紹介日)
                            - BranchName (紹介元支店名)
                            - RepName (紹介元担当者名)

                            Output must be valid JSON only. Do not add any explanation.
                            """

                            message = HumanMessage(content=[
                                {"type": "text", "text": prompt_text},
                                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_str}"}
                            ])

                            # 実行
                            response = llm.invoke([message])
                            
                            # 結果表示
                            st.success("解析完了")
                            st.write(response.content)
                            
                            # JSONパースを試みる（ローカルAIは余計な挨拶を入れることがあるため）
                            try:
                                import json
                                # 最初の { から 最後の } までを切り出す簡易抽出
                                content = response.content
                                start = content.find("{")
                                end = content.rfind("}") + 1
                                if start != -1 and end != 0:
                                    json_str = content[start:end]
                                    data = json.loads(json_str)
                                    st.json(data)
                            except:
                                st.caption("※完全なJSON形式ではありませんでしたが、上記テキストに含まれています。")

                        except Exception as e:
                            st.error(f"解析エラーが発生しました: {e}")
                            st.warning("考えられる原因: 指定したモデルが `ollama pull` されていない、またはPCのメモリ不足。")

if __name__ == "__main__":
    main()