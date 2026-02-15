import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import IncomingNoteBuffer


def check():
    db = DatabaseManager()
    session = db._get_session()
    notes = session.query(IncomingNoteBuffer).filter_by(status="PENDING").all()
    print(f"--- 保留中のメモ: {len(notes)}件 ---")
    for n in notes:
        print(f"件名: {n.subject}")
        print(f"抽出された名前: {n.detected_names}")
        print("-" * 30)
    session.close()


if __name__ == "__main__":
    check()
