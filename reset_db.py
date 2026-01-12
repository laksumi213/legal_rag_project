# file: reset_db.py
import os
import sys

from sqlalchemy import text

# パスを通す
sys.path.append(os.path.join(os.getcwd(), "src"))

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Base


def reset_database():
    print("🔄 データベースの完全リセットを開始します...")

    db = DatabaseManager()
    engine = db.engine

    # 1. スキーマごと強制削除 (DROP SCHEMA public CASCADE)
    # これにより、テーブル間の依存関係を無視して全てを消し去ります。
    print("💣 既存のスキーマ(public)を破棄中...")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.commit()

    # 2. テーブルを再作成
    # 最新の tables.py の定義に基づいて作成されます
    print("🔨 テーブルを再作成中...")
    Base.metadata.create_all(engine)

    print("✅ 完了しました！")
    print(
        "   PostgreSQLは完全に初期化され、最新の定義(client_name含む)と一致しました。"
    )


if __name__ == "__main__":
    print("⚠️ 【警告】PostgreSQLの全データを物理的に破壊・初期化します。")
    check = input("実行してよろしいですか？ (y/n): ")
    if check.lower() == "y":
        try:
            reset_database()
        except Exception as e:
            print(f"❌ エラーが発生しました: {e}")
            print("Dockerが起動しているか、.envの設定が正しいか確認してください。")
    else:
        print("中止しました。")
