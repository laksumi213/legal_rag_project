# src/core/config.py

import os
import sys
from pathlib import Path


class Config:
    """
    アプリケーションのパス解決と環境設定を管理。
    PyInstaller等のパッケージ化環境 (sys._MEIPASS) に対応。
    """

    @staticmethod
    def get_base_path() -> Path:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(__file__).resolve().parents[2]

    # --- 基本ディレクトリ ---
    BASE_DIR: Path = get_base_path()
    DATA_DIR: Path = BASE_DIR / "data"
    LOG_DIR: Path = BASE_DIR / "logs"

    # --- データベース設定 ---
    DB_USER = os.getenv("POSTGRES_USER", "postgres")
    DB_PASS = os.getenv("POSTGRES_PASSWORD", "password")
    DB_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "legal_db")

    DATABASE_URL: str = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # --- UI設定 ---
    APP_TITLE: str = "遺産承継・遺言作成支援システム"
    PRIMARY_COLOR: str = "#d33682"

    @classmethod
    def validate_environment(cls):
        """起動時に必要なディレクトリを確認"""
        os.makedirs(cls.LOG_DIR, exist_ok=True)
        os.makedirs(cls.DATA_DIR, exist_ok=True)
