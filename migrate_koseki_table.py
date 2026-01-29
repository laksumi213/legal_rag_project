import sys
import os
from sqlalchemy import text, inspect

# パス解決
sys.path.append(os.path.join(os.getcwd(), "src"))
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Base

def fix_schema():
    print("🚀 データベース構造の自動修復・同期を開始します...")
    
    db = DatabaseManager()
    engine = db.engine
    
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            # ====================================================
            # 1. heirs テーブルの修正 (今回のエラー原因)
            # ====================================================
            if inspector.has_table("heirs"):
                cols = [c['name'] for c in inspector.get_columns("heirs")]
                
                # エラー原因: occupation (職業)
                if "occupation" not in cols:
                    print("🛠️ 'heirs' テーブルに 'occupation' カラムを追加中...")
                    conn.execute(text("ALTER TABLE heirs ADD COLUMN occupation VARCHAR;"))
                
                # 本籍地
                if "hometown" not in cols:
                    print("🛠️ 'heirs' テーブルに 'hometown' カラムを追加中...")
                    conn.execute(text("ALTER TABLE heirs ADD COLUMN hometown VARCHAR;"))
                
                print("   -> heirs テーブル確認完了")

            # ====================================================
            # 2. file_registry テーブルの修正 (Ver 3.3新機能)
            # ====================================================
            if inspector.has_table("file_registry"):
                cols = [c['name'] for c in inspector.get_columns("file_registry")]
                
                if "status" not in cols:
                    print("🛠️ 'file_registry' に 'status' を追加中...")
                    conn.execute(text("ALTER TABLE file_registry ADD COLUMN status VARCHAR DEFAULT 'CONFIRMED';"))
                    
                if "ai_confidence" not in cols:
                    print("🛠️ 'file_registry' に 'ai_confidence' を追加中...")
                    conn.execute(text("ALTER TABLE file_registry ADD COLUMN ai_confidence FLOAT DEFAULT 0.0;"))
                    
                if "extracted_data" not in cols:
                    print("🛠️ 'file_registry' に 'extracted_data' を追加中...")
                    conn.execute(text("ALTER TABLE file_registry ADD COLUMN extracted_data TEXT;"))
                
                print("   -> file_registry テーブル確認完了")

            # ====================================================
            # 3. 未作成テーブルの一括作成 (IncomingNoteBufferなど)
            # ====================================================
            print("🛠️ 未作成のテーブルがあれば作成します...")
            Base.metadata.create_all(engine)

            conn.commit()
            print("\n✅ データベースの修復が完了しました！")
            print("   これで 'occupation' カラムのエラーは解消されます。")
            
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print("   PostgreSQLが起動していることを確認してください。")

if __name__ == "__main__":
    fix_schema()