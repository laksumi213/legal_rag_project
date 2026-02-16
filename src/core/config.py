# src/core/config.py
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# .envの読み込み
load_dotenv()


class Config:
    """アプリケーション設定管理クラス"""

    @staticmethod
    def get_base_path() -> Path:
        """PyInstaller対応のベースパス取得"""
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(__file__).resolve().parents[2]

    # --- 基本パス ---
    BASE_DIR = get_base_path()
    DATA_DIR = BASE_DIR / "data"
    DB_SQLITE_PATH = DATA_DIR / "db" / "sql" / "legal_system.db"

    # --- アプリ設定 ---
    APP_TITLE = "遺産整理・遺言作成支援システム"

    # --- データベース設定（環境変数から取得） ---
    # クラス変数として定義し、後続のメソッドで参照可能にする
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "legal_db")

    # DBタイプ（デフォルトを postgres に設定）
    DB_TYPE = os.getenv("DB_TYPE", "postgres")

    @classmethod
    def get_database_url(cls) -> str:
        """
        DB接続文字列を動的に生成します。
        NameErrorを避けるため、cls経由でクラス変数にアクセスします。
        """
        if cls.DB_TYPE == "postgres":
            # MacローカルからDocker内のPostgresへ接続する設定
            return (
                f"postgresql+psycopg2://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}"
                f"@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
            )
        else:
            # SQLiteフォールバック
            if not cls.DB_SQLITE_PATH.parent.exists():
                cls.DB_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{cls.DB_SQLITE_PATH}"

    # DatabaseManager等から Config.DATABASE_URL として参照できるようにプロパティ化
    # (初期化時に一度だけメソッドを呼び出す)
    DATABASE_URL = ""  # プレースホルダー

    @classmethod
    def validate_environment(cls):
        """必須ディレクトリの存在確認"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)


# クラス定義の外側でURLを確定（DatabaseManagerが直接参照できるようにするため）
Config.DATABASE_URL = Config.get_database_url()
