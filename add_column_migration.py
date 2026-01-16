# add_column_migration_v2.py
import os
import sys
from sqlalchemy import text

# パスを通す
sys.path.append(os.path.join(os.getcwd(), "src"))

from legal_system.core.database_manager import DatabaseManager

def add_referral_phone_column():
    print("🔄 データベース構造の変更(V2)を開始します...")
    
    db = DatabaseManager()
    engine = db.engine

    # SQLコマンド: referral_sec_phone 列を追加
    alter_sql = text("ALTER TABLE cases ADD COLUMN referral_sec_phone VARCHAR;")
    
    try:
        with engine.connect() as conn:
            conn.execute(alter_sql)
            conn.commit()
        print("✅ 成功: 'cases' テーブルに 'referral_sec_phone' カラムを追加しました。")
        
    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg or "Duplicate column" in error_msg:
            print("ℹ️  スキップ: カラムは既に追加されています。")
        else:
            print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    add_referral_phone_column()