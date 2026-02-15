import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

# プロジェクトルートをパスに追加
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
sys.path.append(str(SRC_DIR))

from legal_system.core.config import Config
from legal_system.models.tables import Coordinate


def add_coordinate_dimensions_migration():
    print(
        "⚙️ 'coordinates' テーブルに 'width' および 'height' カラムを追加するマイグレーションを開始します... "
    )
    engine = create_engine(Config.DATABASE_URL)

    # Check if table exists (for idempotency and initial run safety)
    inspector = inspect(engine)
    if not inspector.has_table(Coordinate.__tablename__):
        print(
            f"⚠️ テーブル '{Coordinate.__tablename__}' が存在しません。スキップします。"
        )
        return

    with engine.connect() as connection:
        columns = [
            col["name"] for col in inspector.get_columns(Coordinate.__tablename__)
        ]

        # Check for 'width' column
        if "width" not in columns:
            print("   -> 'width' カラムを追加中...")
            connection.execute(text("ALTER TABLE coordinates ADD COLUMN width FLOAT"))
            print("   ✅ 'width' カラム追加完了。")
        else:
            print("   . 'width' カラムは既に存在します。スキップします。")

        # Check for 'height' column
        if "height" not in columns:
            print("   -> 'height' カラムを追加中...")
            connection.execute(text("ALTER TABLE coordinates ADD COLUMN height FLOAT"))
            print("   ✅ 'height' カラム追加完了。")
        else:
            print("   . 'height' カラムは既に存在します。スキップします。")

        connection.commit()

    print("✅ 'coordinates' テーブルのマイグレーションが完了しました。")


if __name__ == "__main__":
    add_coordinate_dimensions_migration()
