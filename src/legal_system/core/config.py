# src/legal_system/core/config.py

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
# プロジェクトルートの特定
# このファイル(config.py)は src/legal_system/core/ にあるため
# parents[0]=core, parents[1]=legal_system, parents[2]=src, parents[3]=ROOT
BASE_DIR = Path(__file__).resolve().parents[3]

# データディレクトリ (data/)
DATA_DIR = BASE_DIR / "data"

# データベース保存先
DB_DIR_CHROMA = DATA_DIR / "db" / "chroma" / "local_rag_db"
DB_FILE_SQLITE = DATA_DIR / "db" / "sql" / "legal_system.db"

# データ一時保存先
DATA_DIR_TEMPLATES = DATA_DIR / "templates"
VECTOR_STORE_PATH = DB_DIR_CHROMA

# 銀行RAGシステム用パス設定
RULES_DIR = DATA_DIR / "rules"
BANK_MASTER_PATH = RULES_DIR / "bank_master.csv"
COMPANY_RULES_PATH = RULES_DIR / "company_rules.txt"


# ==========================================
# 2. 設定管理クラス (Config)
# ==========================================
class Config:
    """
    システム全体の設定定数を管理するクラス。
    すべての設定値はこのクラスを経由してアクセスします (例: Config.GOOGLE_MODEL_NAME)。
    """

    # --- パス設定のラップ (ここがエラー原因でした) ---
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR

    # ★追加: DatabaseManagerが参照するための定義
    DB_FILE_SQLITE = DB_FILE_SQLITE

    # その他パス
    BANK_MASTER_PATH = BANK_MASTER_PATH
    COMPANY_RULES_PATH = COMPANY_RULES_PATH
    VECTOR_STORE_PATH = VECTOR_STORE_PATH
    TEMPLATES_DIR = DATA_DIR_TEMPLATES

    # --- AIモデル設定 ---
    # Gemini モデル名
    GOOGLE_MODEL_NAME = "models/gemini-2.5-flash-lite"

    # RAG用設定
    MODEL_NAME = "gemini-2.5-flash-lite"  # engines.py互換用
    EMBEDDING_MODEL = "models/embedding-001"
    TEMPERATURE = 0.0

    # APIキー管理
    _keys_str = os.getenv("GOOGLE_API_KEYS", "")
    GOOGLE_API_KEYS: List[str] = [k.strip() for k in _keys_str.split(",") if k.strip()]

    # リストが空で、単一のキーがある場合はそれを使用
    if not GOOGLE_API_KEYS and os.getenv("GOOGLE_API_KEY"):
        GOOGLE_API_KEYS = [os.getenv("GOOGLE_API_KEY")]

    @classmethod
    def validate_paths(cls) -> None:
        """必須ファイルの存在確認"""
        # ディレクトリ作成
        if not cls.DATA_DIR.exists():
            os.makedirs(cls.DATA_DIR, exist_ok=True)
        if not cls.TEMPLATES_DIR.exists():
            os.makedirs(cls.TEMPLATES_DIR, exist_ok=True)

        # ファイルチェック（存在しなくても起動はさせるがログに残す等）
        missing = []
        if (
            not cls.BANK_MASTER_PATH.exists()
            and cls.BANK_MASTER_PATH.name != "bank_master.csv"
        ):
            missing.append(str(cls.BANK_MASTER_PATH))

        if missing:
            print(f"⚠️ 一部の設定ファイルが見つかりません: {missing}")


# ==========================================
# 3. キー管理クラス (KeyManager)
# ==========================================
class KeyManager:
    """
    APIキーの取得とローテーションを管理するクラス
    Engines.py 等から呼び出されます。
    """

    @staticmethod
    def get_next_key() -> str:
        """
        利用可能なAPIキーを Config から取得して返します。
        複数ある場合はランダムに選択します（簡易ローテーション）。
        """
        keys = Config.GOOGLE_API_KEYS

        if not keys:
            # 環境変数を再確認
            env_key = os.getenv("GOOGLE_API_KEY")
            if env_key:
                return env_key
            raise ValueError(
                "❌ 有効な Google API Key が見つかりません。.env または環境変数を確認してください。"
            )

        return random.choice(keys)
