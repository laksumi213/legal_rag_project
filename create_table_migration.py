import os
import sys
from sqlalchemy import inspect

# プロジェクトの src ディレクトリをパスに追加してモジュールを読み込めるようにする
sys.path.append(os.path.join(os.getcwd(), "src"))

# DatabaseManager と 作成したいモデル(IncomingNoteBuffer)をインポート
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import IncomingNoteBuffer

def create_incoming_note_buffer_table():
    print("🚀 'IncomingNoteBuffer' テーブルの作成を開始します...")

    # データベース接続エンジンの取得
    db = DatabaseManager()
    engine = db.engine

    # すでにテーブルが存在するかチェック
    inspector = inspect(engine)
    if inspector.has_table("incoming_note_buffer"):
        print("ℹ️  テーブル 'incoming_note_buffer' は既に存在します。作成をスキップします。")
        return

    try:
        # SQLAlchemyの機能を使って、モデル定義からテーブルを作成する
        IncomingNoteBuffer.__table__.create(engine)
        print("✅ 成功: テーブル 'incoming_note_buffer' を作成しました。")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    create_incoming_note_buffer_table()