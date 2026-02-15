# src/database/manager.py

from contextlib import contextmanager
from typing import Generator, List

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from core.config import Config
from models.tables import Base, Case


class DatabaseManager:
    def __init__(self, db_url: str = Config.DATABASE_URL):
        self.engine: Engine = create_engine(
            db_url, pool_size=10, max_overflow=20, pool_pre_ping=True, echo=False
        )

        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.ScopedSession = scoped_session(self.session_factory)

    def create_tables(self) -> None:
        Base.metadata.create_all(self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        session = self.ScopedSession()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            self.ScopedSession.remove()

    def fetch_all_cases_sync(self) -> List[Case]:
        with self.get_session() as session:
            statement = select(Case).order_by(Case.case_id.desc())
            result = session.execute(statement)
            return list(result.scalars().all())
