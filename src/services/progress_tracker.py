# src/services/progress_tracker.py

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    Case,
    Deceased,
    FinancialAsset,
    RealEstateAsset,
    Task,
)

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    案件の進捗状況を計算・可視化するサービス
    """

    def __init__(self):
        self.db = DatabaseManager()

    def calculate_case_progress(self, case_id: int) -> Dict:
        """
        案件の進捗率を計算

        Returns:
            {
                "overall": 65,  # 全体進捗率
                "tasks": 70,    # タスク進捗率
                "banks": 80,    # 銀行解約進捗率
                "koseki": 50,   # 戸籍収集進捗率
                "real_estate": 30,  # 不動産登記進捗率
                "details": {
                    "total_tasks": 10,
                    "completed_tasks": 7,
                    "total_banks": 5,
                    "completed_banks": 4,
                    ...
                }
            }
        """
        session = self.db._get_session()
        try:
            case = (
                session.query(Case)
                .options(
                    joinedload(Case.tasks),
                    joinedload(Case.financial_assets),
                    joinedload(Case.real_estates),
                    joinedload(Case.deceased_ref).joinedload(Deceased.family_registers),
                )
                .get(case_id)
            )

            if not case:
                return {"error": "案件が見つかりません"}

            # 1. タスク進捗率（重み付き）
            tasks_progress, tasks_details = self._calculate_tasks_progress(case.tasks)

            # 2. 銀行解約進捗率
            banks_progress, banks_details = self._calculate_banks_progress(
                case.financial_assets
            )

            # 3. 戸籍収集進捗率
            koseki_progress, koseki_details = self._calculate_koseki_progress(
                case.deceased_ref.family_registers if case.deceased_ref else []
            )

            # 4. 不動産登記進捗率
            real_estate_progress, real_estate_details = (
                self._calculate_real_estate_progress(case.real_estates)
            )

            # 5. 全体進捗率（重み付け平均）
            # タスク: 30%, 銀行: 40%, 戸籍: 20%, 不動産: 10%
            weights = {
                "tasks": 0.30,
                "banks": 0.40,
                "koseki": 0.20,
                "real_estate": 0.10,
            }

            overall = (
                tasks_progress * weights["tasks"]
                + banks_progress * weights["banks"]
                + koseki_progress * weights["koseki"]
                + real_estate_progress * weights["real_estate"]
            )

            return {
                "overall": round(overall, 1),
                "tasks": round(tasks_progress, 1),
                "banks": round(banks_progress, 1),
                "koseki": round(koseki_progress, 1),
                "real_estate": round(real_estate_progress, 1),
                "details": {
                    **tasks_details,
                    **banks_details,
                    **koseki_details,
                    **real_estate_details,
                },
            }

        except Exception as e:
            logger.error(f"Progress calculation error: {e}")
            return {"error": str(e)}
        finally:
            session.close()

    def _calculate_tasks_progress(self, tasks: List[Task]) -> Tuple[float, Dict]:
        """タスク進捗率を計算（重み付き）"""
        if not tasks:
            return 100.0, {
                "total_tasks": 0,
                "completed_tasks": 0,
                "weighted_progress": 100.0,
            }

        total_weight = sum(task.weight for task in tasks)
        completed_weight = sum(task.weight for task in tasks if task.is_completed)

        progress = (completed_weight / total_weight * 100) if total_weight > 0 else 0

        return progress, {
            "total_tasks": len(tasks),
            "completed_tasks": sum(1 for task in tasks if task.is_completed),
            "total_weight": total_weight,
            "completed_weight": completed_weight,
        }

    def _calculate_banks_progress(
        self, assets: List[FinancialAsset]
    ) -> Tuple[float, Dict]:
        """銀行解約進捗率を計算"""
        if not assets:
            return 100.0, {"total_banks": 0, "completed_banks": 0}

        # ステータスが「解約済み」「完了」などの場合を完了とみなす
        completed_statuses = ["解約済み", "完了", "COMPLETED", "CLOSED"]
        completed = sum(
            1
            for asset in assets
            if asset.status and any(s in asset.status for s in completed_statuses)
        )

        progress = (completed / len(assets) * 100) if assets else 0

        return progress, {
            "total_banks": len(assets),
            "completed_banks": completed,
            "pending_banks": len(assets) - completed,
        }

    def _calculate_koseki_progress(self, registers: List) -> Tuple[float, Dict]:
        """戸籍収集進捗率を計算"""
        if not registers:
            return 0.0, {"total_koseki": 0, "has_continuity": False}

        # 戸籍の連続性チェック（簡易版）
        # 出生から死亡まで揃っているかを判定
        has_birth = any(r.doc_type and "出生" in r.doc_type for r in registers)
        has_death = any(
            r.doc_type and ("除籍" in r.doc_type or "死亡" in r.doc_type)
            for r in registers
        )

        # 連続性があれば100%、なければ登録数に応じて段階的に
        if has_birth and has_death and len(registers) >= 3:
            progress = 100.0
            has_continuity = True
        elif len(registers) >= 2:
            progress = 70.0
            has_continuity = False
        elif len(registers) >= 1:
            progress = 40.0
            has_continuity = False
        else:
            progress = 0.0
            has_continuity = False

        return progress, {
            "total_koseki": len(registers),
            "has_continuity": has_continuity,
            "has_birth": has_birth,
            "has_death": has_death,
        }

    def _calculate_real_estate_progress(
        self, estates: List[RealEstateAsset]
    ) -> Tuple[float, Dict]:
        """不動産登記進捗率を計算"""
        if not estates:
            return 100.0, {"total_estates": 0, "completed_estates": 0}

        # 登記情報が取得済みかどうかで判定
        completed = sum(
            1 for estate in estates if estate.registry_info_acquired_date is not None
        )

        progress = (completed / len(estates) * 100) if estates else 0

        return progress, {
            "total_estates": len(estates),
            "completed_estates": completed,
            "pending_estates": len(estates) - completed,
        }

    def detect_sla_violations(self, days_threshold: int = 90) -> List[Dict]:
        """
        SLA違反案件を検出

        Args:
            days_threshold: 契約日からの経過日数閾値（デフォルト: 90日）

        Returns:
            [
                {
                    "case_id": 123,
                    "case_number": "2024-001",
                    "client_name": "山田太郎",
                    "contract_date": "2023-10-01",
                    "days_elapsed": 95,
                    "reason": "契約日から95日経過",
                    "progress": 45.5,
                    "overdue_tasks": 3
                },
                ...
            ]
        """
        session = self.db._get_session()
        try:
            # 契約日から指定日数以上経過している案件を取得
            threshold_date = datetime.now() - timedelta(days=days_threshold)

            cases = (
                session.query(Case)
                .options(joinedload(Case.tasks))
                .filter(
                    and_(
                        Case.contract_date.isnot(None),
                        Case.contract_date <= threshold_date,
                        Case.current_status_id.notin_([5, 6]),  # 完了・キャンセル以外
                    )
                )
                .all()
            )

            violations = []

            for case in cases:
                days_elapsed = (datetime.now().date() - case.contract_date).days

                # 進捗率を計算
                progress_data = self.calculate_case_progress(case.case_id)
                overall_progress = progress_data.get("overall", 0)

                # 期限超過タスクをカウント
                overdue_tasks = sum(
                    1
                    for task in case.tasks
                    if not task.is_completed
                    and task.due_date
                    and task.due_date < datetime.now()
                )

                violations.append(
                    {
                        "case_id": case.case_id,
                        "case_number": case.case_number,
                        "client_name": case.client_name,
                        "contract_date": case.contract_date.strftime("%Y-%m-%d")
                        if case.contract_date
                        else None,
                        "days_elapsed": days_elapsed,
                        "reason": f"契約日から{days_elapsed}日経過",
                        "progress": overall_progress,
                        "overdue_tasks": overdue_tasks,
                    }
                )

            # 経過日数でソート（降順）
            violations.sort(key=lambda x: x["days_elapsed"], reverse=True)

            return violations

        except Exception as e:
            logger.error(f"SLA violation detection error: {e}")
            return []
        finally:
            session.close()

    def get_bottleneck_analysis(self) -> Dict:
        """
        ボトルネック分析

        Returns:
            {
                "most_delayed_stage": "銀行解約",
                "average_completion_time": {
                    "tasks": 15.5,  # 日数
                    "banks": 30.2,
                    "koseki": 20.1
                },
                "stuck_cases": [
                    {"case_id": 123, "stage": "銀行解約", "days_stuck": 45},
                    ...
                ]
            }
        """
        session = self.db._get_session()
        try:
            # 全案件の進捗データを取得
            cases = (
                session.query(Case)
                .filter(
                    Case.current_status_id.notin_([5, 6])  # 完了・キャンセル以外
                )
                .all()
            )

            stage_delays = {"tasks": [], "banks": [], "koseki": [], "real_estate": []}

            stuck_cases = []

            for case in cases:
                progress = self.calculate_case_progress(case.case_id)

                # 各ステージの進捗が50%未満の場合、遅延とみなす
                if progress.get("tasks", 100) < 50:
                    stage_delays["tasks"].append(case.case_id)
                    if case.contract_date:
                        days = (datetime.now().date() - case.contract_date).days
                        stuck_cases.append(
                            {
                                "case_id": case.case_id,
                                "case_number": case.case_number,
                                "stage": "タスク",
                                "days_stuck": days,
                                "progress": progress.get("tasks", 0),
                            }
                        )

                if progress.get("banks", 100) < 50:
                    stage_delays["banks"].append(case.case_id)
                    if case.contract_date:
                        days = (datetime.now().date() - case.contract_date).days
                        stuck_cases.append(
                            {
                                "case_id": case.case_id,
                                "case_number": case.case_number,
                                "stage": "銀行解約",
                                "days_stuck": days,
                                "progress": progress.get("banks", 0),
                            }
                        )

                if progress.get("koseki", 100) < 50:
                    stage_delays["koseki"].append(case.case_id)

                if progress.get("real_estate", 100) < 50:
                    stage_delays["real_estate"].append(case.case_id)

            # 最も遅延が多いステージを特定
            most_delayed_stage = max(stage_delays.items(), key=lambda x: len(x[1]))

            stage_names = {
                "tasks": "タスク",
                "banks": "銀行解約",
                "koseki": "戸籍収集",
                "real_estate": "不動産登記",
            }

            # 停滞案件を日数でソート
            stuck_cases.sort(key=lambda x: x["days_stuck"], reverse=True)

            return {
                "most_delayed_stage": stage_names.get(most_delayed_stage[0], "不明"),
                "delayed_count_by_stage": {
                    stage_names[k]: len(v) for k, v in stage_delays.items()
                },
                "stuck_cases": stuck_cases[:10],  # 上位10件
            }

        except Exception as e:
            logger.error(f"Bottleneck analysis error: {e}")
            return {"error": str(e)}
        finally:
            session.close()

    def get_all_cases_summary(self) -> List[Dict]:
        """
        全案件の進捗サマリーを取得

        Returns:
            [
                {
                    "case_id": 123,
                    "case_number": "2024-001",
                    "client_name": "山田太郎",
                    "progress": 65.5,
                    "status": "進行中",
                    "days_since_contract": 45,
                    "is_overdue": False
                },
                ...
            ]
        """
        session = self.db._get_session()
        try:
            cases = (
                session.query(Case)
                .options(joinedload(Case.status_ref))
                .filter(
                    Case.current_status_id.notin_([5, 6])  # 完了・キャンセル以外
                )
                .all()
            )

            summary = []

            for case in cases:
                progress_data = self.calculate_case_progress(case.case_id)

                days_since_contract = None
                is_overdue = False

                if case.contract_date:
                    days_since_contract = (
                        datetime.now().date() - case.contract_date
                    ).days
                    is_overdue = days_since_contract > 90  # 90日超過でSLA違反

                summary.append(
                    {
                        "case_id": case.case_id,
                        "case_number": case.case_number,
                        "client_name": case.client_name,
                        "progress": progress_data.get("overall", 0),
                        "status": case.status_ref.status_name
                        if case.status_ref
                        else "不明",
                        "days_since_contract": days_since_contract,
                        "is_overdue": is_overdue,
                        "contract_date": case.contract_date.strftime("%Y-%m-%d")
                        if case.contract_date
                        else None,
                    }
                )

            # 進捗率でソート（昇順 = 遅れている案件が上位）
            summary.sort(key=lambda x: x["progress"])

            return summary

        except Exception as e:
            logger.error(f"Cases summary error: {e}")
            return []
        finally:
            session.close()
