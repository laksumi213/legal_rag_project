import os
import sys
from pathlib import Path

# パス設定
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from src.legal_system.core.database_manager import DatabaseManager
from src.legal_system.models.tables import IncomingNoteBuffer

def reset_audio_note():
    db = DatabaseManager()
    session = db._get_session()

    # 件名に「録音」を含むメモを探す
    target_notes = session.query(IncomingNoteBuffer).filter(
        IncomingNoteBuffer.subject.like('%録音%')
    ).all()

    if not target_notes:
        print("❌ 「録音」という件名のメモはデータベースに見つかりませんでした。")
        print("   すでに削除されているか、まだ取り込まれていない可能性があります。")
        return

    print(f"🔍 {len(target_notes)} 件の「録音」メモが見つかりました。")
    
    for note in target_notes:
        print(f"   - ID: {note.id} | 件名: {note.subject} | 受信: {note.received_at}")
        session.delete(note)
    
    session.commit()
    print("\n✅ 削除しました。これでもう一度メールを取り込める状態になりました！")
    print("   👉 'rye run start' を実行すると、音声解析付きで再取得されます。")

    session.close()

if __name__ == "__main__":
    reset_audio_note()