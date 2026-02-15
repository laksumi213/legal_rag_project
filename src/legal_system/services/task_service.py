# src/services/task_service.py

"""
タスク管理サービス

日付: 2026-02-12
機能:
- 案件に対する標準タスクの自動生成
- タスクの一括更新
- タスク一覧の取得
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import joinedload

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, Task, TaskTemplate, User

logger = logging.getLogger(__name__)


class TaskService:
    """タスク管理サービスクラス"""

    def __init__(self):
        self.db = DatabaseManager()

    def initialize_tasks(self, case_id: int) -> bool:
        """
        案件に標準タスクを初期化する

        Args:
            case_id: 案件ID

        Returns:
            bool: 成功した場合True

        日付: 2026-02-12
        """
        session = self.db._get_session()
        try:
            # 案件を取得
            case = session.query(Case).options(joinedload(Case.tasks)).get(case_id)

            if not case:
                logger.error(f"Case not found: {case_id}")
                return False

            # 既にタスクが存在する場合はスキップ
            if case.tasks:
                logger.warning(f"Tasks already exist for case {case_id}")
                return False

            # テンプレートを取得
            templates = (
                session.query(TaskTemplate)
                .order_by(TaskTemplate.default_due_days)
                .all()
            )

            if not templates:
                logger.error("No task templates found")
                return False

            # 基準日を決定（契約日がなければ今日）
            base_date = case.contract_date if case.contract_date else date.today()

            # テンプレートからタスクを生成
            for template in templates:
                # 期限日を計算
                due_date = datetime.combine(
                    base_date + timedelta(days=template.default_due_days),
                    datetime.min.time(),
                )

                # 担当者を割り当て
                if template.is_manager_task:
                    assigned_user_id = case.manager_id
                else:
                    assigned_user_id = case.operator_id

                # タスクを作成
                new_task = Task(
                    case_id=case_id,
                    template_id=template.template_id,
                    description=template.description,
                    due_date=due_date,
                    assigned_user_id=assigned_user_id,
                    is_completed=False,
                    weight=1.0,  # デフォルト重み
                )

                session.add(new_task)
                logger.info(
                    f"Created task: {template.description} "
                    f"(due: {due_date.date()}, assigned: {assigned_user_id})"
                )

            session.commit()
            logger.info(
                f"Successfully initialized {len(templates)} tasks for case {case_id}"
            )
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error initializing tasks: {e}", exc_info=True)
            return False
        finally:
            session.close()

    def get_tasks_by_case(self, case_id: int) -> List[Dict[str, Any]]:
        """
        案件のタスク一覧を取得（表示用）

        Args:
            case_id: 案件ID

        Returns:
            List[Dict]: タスク情報の辞書リスト

        日付: 2026-02-12
        """
        session = self.db._get_session()
        try:
            tasks = (
                session.query(Task)
                .options(joinedload(Task.assigned_user))
                .filter(Task.case_id == case_id)
                .order_by(Task.due_date)
                .all()
            )

            result = []
            for task in tasks:
                result.append(
                    {
                        "task_id": task.task_id,
                        "description": task.description,
                        "due_date": task.due_date.date() if task.due_date else None,
                        "is_completed": task.is_completed,
                        "assigned_user_id": task.assigned_user_id,
                        "assigned_user_name": task.assigned_user.name
                        if task.assigned_user
                        else "未割当",
                        "weight": task.weight,
                        "last_updated_at": task.last_updated_at,
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Error getting tasks: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def update_tasks_bulk(self, updates: List[Dict[str, Any]]) -> bool:
        """
        タスクを一括更新する

        Args:
            updates: 更新情報のリスト
                [
                    {
                        "task_id": 1,
                        "is_completed": True,
                        "due_date": date(2026, 3, 1),
                        "assigned_user_id": 2,
                        "weight": 1.5
                    },
                    ...
                ]

        Returns:
            bool: 成功した場合True

        日付: 2026-02-12
        """
        session = self.db._get_session()
        try:
            for update_data in updates:
                task_id = update_data.get("task_id")
                if not task_id:
                    continue

                task = session.query(Task).get(task_id)
                if not task:
                    logger.warning(f"Task not found: {task_id}")
                    continue

                # 更新可能なフィールドを更新
                if "is_completed" in update_data:
                    task.is_completed = update_data["is_completed"]

                if "due_date" in update_data and update_data["due_date"]:
                    # dateオブジェクトをdatetimeに変換
                    if isinstance(update_data["due_date"], date):
                        task.due_date = datetime.combine(
                            update_data["due_date"], datetime.min.time()
                        )
                    else:
                        task.due_date = update_data["due_date"]

                if "assigned_user_id" in update_data:
                    task.assigned_user_id = update_data["assigned_user_id"]

                if "weight" in update_data:
                    task.weight = update_data["weight"]

                # 更新日時を自動更新
                task.last_updated_at = datetime.now()

                logger.info(f"Updated task {task_id}: {task.description}")

            session.commit()
            logger.info(f"Successfully updated {len(updates)} tasks")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error updating tasks: {e}", exc_info=True)
            return False
        finally:
            session.close()

    def get_available_users(self) -> List[Dict[str, Any]]:
        """
        担当者候補のユーザー一覧を取得

        Returns:
            List[Dict]: ユーザー情報の辞書リスト

        日付: 2026-02-12
        """
        session = self.db._get_session()
        try:
            users = session.query(User).all()

            result = []
            for user in users:
                result.append(
                    {
                        "id": user.id,
                        "name": user.name,
                        "dept": user.dept if hasattr(user, "dept") else "",
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Error getting users: {e}", exc_info=True)
            return []
        finally:
            session.close()

    def delete_task(self, task_id: int) -> bool:
        """
        タスクを削除する

        Args:
            task_id: タスクID

        Returns:
            bool: 成功した場合True

        日付: 2026-02-12
        """
        session = self.db._get_session()
        try:
            task = session.query(Task).get(task_id)
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            session.delete(task)
            session.commit()
            logger.info(f"Deleted task {task_id}: {task.description}")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error deleting task: {e}", exc_info=True)
            return False
        finally:
            session.close()

    def add_custom_task(
        self,
        case_id: int,
        description: str,
        due_date: Optional[date] = None,
        assigned_user_id: Optional[int] = None,
        weight: float = 1.0,
    ) -> bool:
        """
        カスタムタスクを追加する

        Args:
            case_id: 案件ID
            description: タスク説明
            due_date: 期限日
            assigned_user_id: 担当者ID
            weight: 重み

        Returns:
            bool: 成功した場合True

        日付: 2026-02-12
        """
        session = self.db._get_session()
        try:
            # 期限日がない場合は7日後に設定
            if not due_date:
                due_date = date.today() + timedelta(days=7)

            # datetimeに変換
            due_datetime = datetime.combine(due_date, datetime.min.time())

            new_task = Task(
                case_id=case_id,
                template_id=None,  # カスタムタスクはテンプレートなし
                description=description,
                due_date=due_datetime,
                assigned_user_id=assigned_user_id,
                is_completed=False,
                weight=weight,
            )

            session.add(new_task)
            session.commit()
            logger.info(f"Added custom task: {description}")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Error adding custom task: {e}", exc_info=True)
            return False
        finally:
            session.close()
