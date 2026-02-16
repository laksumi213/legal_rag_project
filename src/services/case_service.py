# src/services/case_service.py
import logging
from typing import Dict, List, Optional

from sqlalchemy import desc, func, select
from sqlalchemy.orm import joinedload

from database.manager import DatabaseManager
from models.tables import Case, FinancialAsset

logger = logging.getLogger(__name__)


class CaseService:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def get_dashboard_summary(self) -> Dict[str, int]:
        with self.db_manager.get_session() as session:
            try:
                total_cases = (
                    session.scalar(select(func.count()).select_from(Case)) or 0
                )
                completed_cases = (
                    session.scalar(
                        select(func.count())
                        .select_from(Case)
                        .filter(Case.current_status_id == 5)
                    )
                    or 0
                )
                return {
                    "active": total_cases - completed_cases,
                    "completed": completed_cases,
                    "warning": 0,
                    "total": total_cases,
                }
            except Exception as e:
                logger.error(f"Dashboard summary error: {e}")
                return {"active": 0, "completed": 0, "warning": 0, "total": 0}

    def get_all_cases(self, limit: int = 50) -> List[Case]:
        with self.db_manager.get_session() as session:
            stmt = (
                select(Case)
                .options(joinedload(Case.status_ref), joinedload(Case.deceased_ref))
                .order_by(desc(Case.created_at))
                .limit(limit)
            )
            return list(session.execute(stmt).scalars().all())

    def get_case_detail(self, case_id: int) -> Optional[Case]:
        """
        案件の詳細情報（被相続人、金融資産、銀行マスタ含む）を取得する。
        """
        with self.db_manager.get_session() as session:
            stmt = (
                select(Case)
                .options(
                    joinedload(Case.deceased_ref),
                    joinedload(Case.financial_assets).joinedload(
                        FinancialAsset.bank_ref
                    ),
                    joinedload(Case.financial_assets).joinedload(
                        FinancialAsset.branch_ref
                    ),
                    joinedload(Case.financial_assets).joinedload(
                        FinancialAsset.account_type_ref
                    ),
                )
                .filter(Case.case_id == case_id)
            )
            return session.execute(stmt).scalar_one_or_none()
