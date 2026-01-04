# src/legal_system/core/ai_factory.py

import os
import random
from typing import Any

from langchain_chroma import Chroma

# LangChain / Google Generative AI
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# ★修正: 変数直接ではなく Config クラスをインポートします
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
        """
        api_key = cls._get_api_key()

        # ★修正: Config.GOOGLE_MODEL_NAME としてクラス変数にアクセス
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
        # ★修正: Config.EMBEDDING_MODEL を使用
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
