# migrate_add_assessed_value.py
import os
import sys
from sqlalchemy import text

# パス解決
sys.path.append(os.path.join(os.getcwd(), "src"))

from legal_system.core.database_manager import DatabaseManager

def add_assessed_value_column():
    print("🔄 データベース構造の変更を開始します...")
    print("👉 'real_estate_assets' テーブルに 'assessed_value' カラムを追加します。")

    db = DatabaseManager()
    engine = db.engine

    # SQLコマンド
    alter_sql = text("ALTER TABLE real_estate_assets ADD COLUMN assessed_value FLOAT DEFAULT 0.0;")

    try:
        with engine.connect() as conn:
            conn.execute(alter_sql)
            conn.commit()
        print("✅ 成功: カラムを追加しました。")

    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg or "Duplicate column" in error_msg:
            print("ℹ️  スキップ: カラムは既に追加されています。")
        else:
            print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    add_assessed_value_column()