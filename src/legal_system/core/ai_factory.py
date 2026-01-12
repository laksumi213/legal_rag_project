# src/legal_system/core/ai_factory.py

import os
import platform
import random
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
    APIキーのローテーション機能を含みます。
    """

    @staticmethod
    def _get_api_key() -> str:
        """
        利用可能なAPIキーを取得します。
        Home.py等で既に環境変数がセットされていればそれを使用し、
        なければConfigリストからランダムに取得してセットします。
        """
        # 1. 既に環境変数にセットされている場合（優先）
        env_key = os.getenv("GOOGLE_API_KEY")
        if env_key:
            return env_key

        # 2. 未セットの場合、Configから取得してセットする (ローテーション)
        if Config.GOOGLE_API_KEYS:
            selected_key = random.choice(Config.GOOGLE_API_KEYS)
            os.environ["GOOGLE_API_KEY"] = selected_key
            return selected_key

        raise ValueError(
            "❌ 有効な Google API Key が見つかりません。.env を確認してください。"
        )

    @classmethod
    def get_llm(cls, mode: str = "cloud") -> Any:
        """
        指定されたモードに応じたLLMインスタンスを返します。

        Args:
            mode (str): "cloud" (Gemini) または "local" (Ollama)
        """
        if mode == "local":
            # --- ローカルLLM (Ollama) の設定 ---

            # OS判定によるモデル自動切り替え
            current_os = platform.system()
            if current_os == "Windows":
                # Windows: VRAMに余裕がある場合が多いと仮定し、8bモデル推奨
                # 事前に `ollama pull llama3.1` が必要
                model_name = "llama3.1"
                print(f"🖥️ Detected Windows. Using Local LLM: {model_name}")
            else:
                # Mac / Linux: Apple Silicon等での高速動作重視で軽量モデル推奨
                # 事前に `ollama pull llama3.2:3b` が必要
                model_name = "llama3.2:3b"
                # model_name = "llama3.1"
                print(f"🍎 Detected Mac/Linux. Using Local LLM: {model_name}")

            return ChatOllama(
                model=model_name,
                temperature=0.0,
                # JSONモードを有効化（構造化データ抽出のため）
                format="json",
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
        """
        埋め込みモデル（Embeddings）を返します。
        """
        api_key = cls._get_api_key()
        return GoogleGenerativeAIEmbeddings(
            model=Config.EMBEDDING_MODEL, google_api_key=api_key
        )

    @classmethod
    def get_vector_store(cls) -> Chroma:
        """
        永続化されたChromaベクトルストアのインスタンスを返します。
        """
        embeddings = cls.get_embeddings()

        # ディレクトリ作成 (念のため)
        if not Config.VECTOR_STORE_PATH.exists():
            os.makedirs(Config.VECTOR_STORE_PATH, exist_ok=True)

        return Chroma(
            persist_directory=str(Config.VECTOR_STORE_PATH),
            embedding_function=embeddings,
        )
