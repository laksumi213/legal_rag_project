# src/services/case_service.py
from typing import List

from sqlalchemy import desc, select
from sqlalchemy.orm import joinedload

from database.manager import DatabaseManager
from models.tables import Case


class CaseService:
    """案件（Case）に関するビジネスロジックを提供するサービス"""

    def __init__(self):
        self.db = DatabaseManager()

    def get_all_cases(self) -> List[Case]:
        """全案件を最新順に取得"""
        with self.db.get_session() as session:
            stmt = (
                select(Case)
                .options(joinedload(Case.status_ref))  # リレーションを事前ロード
                .order_by(desc(Case.created_at))
            )
            result = session.execute(stmt)
            return list(result.scalars().all())

    def get_dashboard_summary(self) -> dict:
        """ダッシュボード用の統計情報を取得"""
        with self.db.get_session() as session:
            # SQLAlchemy 2.0 style count
            total = session.query(Case).count()
            # ※本来は select(func.count()).select_from(Case) が2.0の厳密な書き方ですが、
            # 移行過渡期は query API も許容されます。

            # ダミーではなく実データを返す（データがない場合は0）
            return {
                "active": total,
                "completed": 0,  # ロジック未実装のため仮
                "warning": 0,
            }
