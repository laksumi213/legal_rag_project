# migrations/env.py

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# 1. プロジェクトのルートディレクトリを Python パスに追加
# これにより 'src' フォルダ内のモジュールをインポート可能にします
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# 2. プロジェクトのモデルと設定をインポート
# tables.py に定義されている Base (MetaData) を取得します
from src.legal_system.core.config import Config
from src.legal_system.models.tables import Base

# Alembic Config オブジェクト
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3. 'autogenerate' サポートのためにモデルの MetaData をセット
target_metadata = Base.metadata

# 4. DB接続URLを Config クラスから取得して Alembic にセット
# これにより alembic.ini にパスワードを直接書く必要がなくなります
config.set_main_option("sqlalchemy.url", Config.DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # alembic.ini の設定ではなく、上記でセットした動的なURLを使用して接続を作成
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # autogenerate時にカラムの型変更なども検知するように設定
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
