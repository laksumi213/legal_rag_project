# scripts/seed_data.py
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import CaseStatus, TaskTemplate


def seed_statuses():
    print("🌱 初期データの投入を開始します...")
    db = DatabaseManager()
    session = db._get_session()

    try:
        # ステータスマスタの初期値
        statuses = [
            (1, "受任・調査中"),
            (2, "書類作成中"),
            (3, "署名押印待ち"),
            (4, "申請中"),
            (5, "完了"),
            (9, "保留・中止"),
        ]

        for s_id, s_name in statuses:
            exists = session.query(CaseStatus).filter_by(id=s_id).first()
            if not exists:
                new_status = CaseStatus(id=s_id, name=s_name, order_num=s_id)
                session.add(new_status)
                print(f"  + 追加: {s_name}")
            else:
                print(f"  . 既存: {s_name}")

        session.commit()
        print("✅ ステータスマスタの投入が完了しました！")

    except Exception as e:
        session.rollback()
        print(f"❌ エラー: {e}")
    finally:
        session.close()


def seed_task_templates():
    """
    標準タスクテンプレートを投入する

    日付: 2026-02-12
    """
    print("\n🌱 タスクテンプレートの投入を開始します...")
    db = DatabaseManager()
    session = db._get_session()

    try:
        # 標準タスクテンプレート定義
        # (description, default_due_days, is_manager_task)
        templates = [
            ("戸籍収集（出生～死亡）", 20, False),
            ("相続関係説明図の作成", 34, False),
            ("金融資産・残高証明書の取得", 70, False),
            ("不動産・名寄帳/評価証明書の取得", 34, False),
            ("財産目録の作成・承認", 75, True),
            ("遺産分割協議書の作成", 80, False),
            ("遺産分割協議書の承認・実印押印", 94, True),
            ("金融機関への解約申請", 114, False),
            ("完了報告・報酬精算", 120, True),
        ]

        for description, due_days, is_manager in templates:
            # 重複チェック
            exists = (
                session.query(TaskTemplate).filter_by(description=description).first()
            )

            if not exists:
                new_template = TaskTemplate(
                    description=description,
                    default_due_days=due_days,
                    is_manager_task=is_manager,
                )
                session.add(new_template)
                role = "Manager" if is_manager else "Operator"
                print(f"  + 追加: {description} ({due_days}日, {role})")
            else:
                print(f"  . 既存: {description}")

        session.commit()
        print("✅ タスクテンプレートの投入が完了しました！")

    except Exception as e:
        session.rollback()
        print(f"❌ エラー: {e}")
        import traceback

        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    seed_statuses()
    seed_task_templates()
