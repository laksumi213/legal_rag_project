import os
import streamlit as st
from typing import List, Optional

# LangChain関連
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.language_models import BaseChatModel

# 設定読み込み
from .config import (
    GOOGLE_MODEL_NAME, 
    OLLAMA_MODEL_NAME, 
    OLLAMA_BASE_URL, 
    EMBEDDING_MODEL_NAME,
    DB_DIR_CHROMA
)

class AIFactory:
    """
    AIモデル(LLM)と検索エンジン(VectorStore)の生成を担当するファクトリクラス
    Cloud(Gemini)とLocal(Ollama)の切り替えロジックを集約。
    """

    @staticmethod
    @st.cache_resource
    def get_vector_store():
        """
        VectorStore(Chroma)の初期化。
        Cloud/Localモードに関わらず、Embeddingは常にローカル(HuggingFace)で行う。
        """
        # 埋め込みモデルの準備 (CPU実行)
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"}
        )

        # ディレクトリ作成
        DB_DIR_CHROMA.mkdir(parents=True, exist_ok=True)

        # VectorStoreロード
        vector_store = Chroma(
            persist_directory=str(DB_DIR_CHROMA),
            embedding_function=embeddings,
            collection_name="agent_documents"
        )
        return vector_store

    @staticmethod
    def get_llm(mode: str) -> Optional[BaseChatModel]:
        """
        指定されたモードに基づいて適切なLLMインスタンスを返す。
        
        Args:
            mode (str): 'cloud' (Gemini) または 'local' (Ollama)
            
        Returns:
            BaseChatModel: LangChainのChatModelインスタンス
        """
        
        if mode == "cloud":
            # --- Cloud (Gemini) ---
            # 環境変数からAPIキーリストを取得 (カンマ区切り対応)
            keys_str = os.getenv("GOOGLE_API_KEYS", "")
            api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]

            if not api_keys:
                st.error("⚠️ .env に GOOGLE_API_KEYS が設定されていません。")
                return None

            # 各APIキーごとにLLMインスタンスを作成
            llm_instances = [
                ChatGoogleGenerativeAI(
                    model=GOOGLE_MODEL_NAME,
                    google_api_key=k,
                    temperature=0,  # 実務用のためランダム性を排除
                    convert_system_message_to_human=True,
                    max_retries=1   # フォールバックを早めるためリトライ回数は減らす
                )
                for k in api_keys
            ]

            # フォールバックチェーンの構築
            # 1つ目のキーがだめなら2つ目...という動作を実現
            if len(llm_instances) > 1:
                llm_cloud = llm_instances[0].with_fallbacks(llm_instances[1:])
            else:
                llm_cloud = llm_instances[0]
                
            return llm_cloud

        else:
            # --- Local (Ollama) ---
            # 機密情報対応モード
            return ChatOllama(
                model=OLLAMA_MODEL_NAME,
                temperature=0,
                base_url=OLLAMA_BASE_URL
            )
