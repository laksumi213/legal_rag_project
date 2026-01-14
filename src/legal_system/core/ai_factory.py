# src/legal_system/core/ai_factory.py

import os
import platform
import random
import requests
from typing import Any

from langchain_chroma import Chroma

# LangChain Community (Ollama用)
from langchain_community.chat_models import ChatOllama

# Google Generative AI
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from .config import Config


class AIFactory:
    """
    AIモデル（LLM）、Embeddings、VectorStoreのインスタンス生成を一元管理するファクトリークラス。
    APIキーのローテーション機能およびOllamaの接続チェックを含みます。
    """

    @staticmethod
    def _get_api_key() -> str:
        """利用可能なAPIキーを取得します。"""
        # 1. 環境変数から優先取得
        env_key = os.getenv("GOOGLE_API_KEY")
        if env_key:
            return env_key

        # 2. Configからローテーション取得
        if Config.GOOGLE_API_KEYS:
            selected_key = random.choice(Config.GOOGLE_API_KEYS)
            os.environ["GOOGLE_API_KEY"] = selected_key
            return selected_key

        raise ValueError(
            "❌ 有効な Google API Key が見つかりません。.env を確認してください。"
        )

    @staticmethod
    def _check_ollama_server(base_url: str) -> bool:
        """
        Ollamaサーバーが起動しているか、指定されたURLで疎通確認を行う。
        """
        try:
            # タグ一覧取得APIを叩いて生存確認 (タイムアウト2秒)
            response = requests.get(f"{base_url}/api/tags", timeout=2.0)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @classmethod
    def get_llm(cls, mode: str = "cloud") -> Any:
        if mode == "local":
            base_url = "http://host.docker.internal:11434"

            if not cls._check_ollama_server(base_url):
                raise ConnectionError(f"❌ Ollamaサーバーに接続できません。")

            # 【修正】メモリ不足を回避するため、軽量な 1b モデルに固定
            # ※ Llama 3.1:8b は約 5GB のメモリを消費しますが、3.2:1b は約 1.5GB で動きます。
            model_name = "llama3.2:1b" 
            
            print(f"🤖 メモリ節約モード: {model_name} を使用します。")

            return ChatOllama(
                base_url=base_url,
                model=model_name,
                temperature=0.0,
                format="json",
                timeout=120,
            )
        
        else:
            # --- クラウドLLM (Google Gemini) の設定 ---
            api_key = cls._get_api_key()

            return ChatGoogleGenerativeAI(
                model=Config.GOOGLE_MODEL_NAME,
                google_api_key=api_key,
                temperature=Config.TEMPERATURE,
                convert_system_message_to_human=True,
            )

    @classmethod
    def get_embeddings(cls) -> Any:
        """埋め込みモデル（Embeddings）を返します。"""
        api_key = cls._get_api_key()
        return GoogleGenerativeAIEmbeddings(
            model=Config.EMBEDDING_MODEL, google_api_key=api_key
        )

    @classmethod
    def get_vector_store(cls) -> Chroma:
        """永続化されたChromaベクトルストアのインスタンスを返します。"""
        embeddings = cls.get_embeddings()

        # ディレクトリ作成 (念のため)
        if not Config.VECTOR_STORE_PATH.exists():
            os.makedirs(Config.VECTOR_STORE_PATH, exist_ok=True)

        return Chroma(
            persist_directory=str(Config.VECTOR_STORE_PATH),
            embedding_function=embeddings,
        )