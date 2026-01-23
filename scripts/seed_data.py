# scripts/seed_data.py
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from src.legal_system.core.database_manager import DatabaseManager
from src.legal_system.models.tables import CaseStatus

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
            (9, "保留・中止")
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
        print("✅ データの投入が完了しました！")

    except Exception as e:
        session.rollback()
        print(f"❌ エラー: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_statuses()