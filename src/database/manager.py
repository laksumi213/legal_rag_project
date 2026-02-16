# src/database/manager.py
import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from core.config import Config
from models.tables import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    SQLAlchemy 2.0 DB管理クラス。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Configから動的にURLを取得
        db_url = Config.get_database_url()

        self.engine = create_engine(db_url, pool_pre_ping=True, echo=False)
        self.session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        self.ScopedSession = scoped_session(self.session_factory)

    def create_tables(self):
        """テーブル作成（開発用）"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("✅ データベーステーブルの初期化完了")
        except Exception as e:
            logger.error(f"❌ テーブル作成エラー: {e}")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        session = self.ScopedSession()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
