import sys
from pathlib import Path

from sqlalchemy import text

# パス解決
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from legal_system.core.database_manager import DatabaseManager


def clean_only_notes():
    print("🧹 会議メモデータのクリーニングを開始します（案件データは維持されます）...")
    db = DatabaseManager()
    session = db._get_session()

    try:
        # 1. 既に取り込まれたメールの原本バッファを削除
        print(" -> IncomingNoteBuffer をクリア中...")
        session.execute(text("DELETE FROM incoming_note_buffer;"))

        # 2. 案件に紐付いてしまった「【自動取込】」が含まれる履歴だけを削除
        print(" -> 案件履歴内の自動取込メモをクリア中...")
        session.execute(
            text("DELETE FROM contact_logs WHERE contact_content LIKE '【自動取込】%';")
        )

        session.commit()
        print(
            "✅ クリーニング完了！これで修正版AIが過去7日間のメールを再度スキャンします。"
        )

    except Exception as e:
        session.rollback()
        print(f"❌ エラー: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    clean_only_notes()
