import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config


# ============================================
# Project path
# ============================================
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))


# ============================================
# App imports
# ============================================
from app.core.database import DATABASE_URL
from app.core.base import EntityBase

# Important: import models so SQLAlchemy registers tables
from app.domain import models  # noqa: F401


# ============================================
# Alembic config
# ============================================
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ============================================
# Database URL
# ============================================
config.set_main_option("sqlalchemy.url", DATABASE_URL)


# ============================================
# Metadata for autogenerate
# ============================================
target_metadata = EntityBase.metadata


# ============================================
# Offline migrations
# ============================================
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================
# Online migrations
# ============================================
def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section)

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ============================================
# Run migrations
# ============================================
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()