# file: src/legal_system/core/config.py

import os
import random
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# .env ファイルの読み込み
load_dotenv()

# ==========================================
# 1. パス設定 (モジュールレベル定数)
# ==========================================
BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"

# DB関連パス
DB_FILE_SQLITE = DATA_DIR / "db" / "sql" / "legal_system.db"
DB_DIR_CHROMA = DATA_DIR / "db" / "chroma" / "local_rag_db"

# データ一時保存先
DATA_DIR_TEMPLATES = DATA_DIR / "templates"
VECTOR_STORE_PATH = DB_DIR_CHROMA

# RAG関連パス
RULES_DIR = DATA_DIR / "rules"
BANK_MASTER_PATH = RULES_DIR / "bank_master.csv"
COMPANY_RULES_PATH = RULES_DIR / "company_rules.txt"


# ==========================================
# 2. 設定管理クラス (Config)
# ==========================================
class Config:
    """
    システム全体の設定定数を管理するクラス。
    """

    # --- パス設定 ---
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    TEMPLATES_DIR = DATA_DIR_TEMPLATES

    # RAG関連パス
    BANK_MASTER_PATH = BANK_MASTER_PATH
    COMPANY_RULES_PATH = COMPANY_RULES_PATH
    VECTOR_STORE_PATH = VECTOR_STORE_PATH

    # --- データベース設定 (PostgreSQL) ---
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "legal_db")

    DATABASE_URL = (
        f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # --- AIプロバイダー設定 (New) ---
    # "studio" (API Key) or "vertex" (Google Cloud)
    AI_PROVIDER = os.getenv("AI_PROVIDER", "studio").lower()

    # --- Vertex AI 設定 ---
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_REGION = os.getenv("GOOGLE_CLOUD_REGION", "asia-northeast1")

    # --- モデル設定 ---
    # Vertex利用時はPublisher Model IDとして扱われる
    GOOGLE_MODEL_NAME = "gemini-2.5-flash-lite"
    MODEL_NAME = "gemini-2.5-flash-lite"
    
    # Embedding Model
    # Vertex利用時は "text-embedding-004" 等が推奨されるが、ここでは互換性のため一旦共通化
    EMBEDDING_MODEL = "models/embedding-001"
    
    TEMPERATURE = 0.0

    # APIキー管理 (Studio用)
    _keys_str = os.getenv("GOOGLE_API_KEYS", "")
    GOOGLE_API_KEYS: List[str] = [k.strip() for k in _keys_str.split(",") if k.strip()]

    if not GOOGLE_API_KEYS and os.getenv("GOOGLE_API_KEY"):
        GOOGLE_API_KEYS = [os.getenv("GOOGLE_API_KEY")]

    @classmethod
    def validate_paths(cls) -> None:
        """必須ディレクトリの存在確認"""
        if not cls.DATA_DIR.exists():
            os.makedirs(cls.DATA_DIR, exist_ok=True)
        if not cls.TEMPLATES_DIR.exists():
            os.makedirs(cls.TEMPLATES_DIR, exist_ok=True)
        
    @classmethod
    def is_vertex_enabled(cls) -> bool:
        return cls.AI_PROVIDER == "vertex"


# ==========================================
# 3. キー管理クラス (KeyManager)
# ==========================================
class KeyManager:
    @staticmethod
    def get_next_key() -> str:
        # Vertexの場合はキー不要（ADC利用）だが、Config互換性のために実装維持
        if Config.is_vertex_enabled():
            return "vertex-managed"
            
        keys = Config.GOOGLE_API_KEYS
        if not keys:
            env_key = os.getenv("GOOGLE_API_KEY")
            if env_key:
                return env_key
            raise ValueError("❌ 有効な Google API Key が見つかりません。")
        return random.choice(keys)