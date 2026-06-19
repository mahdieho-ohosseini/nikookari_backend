from typing import AsyncGenerator

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.base import EntityBase
from app.core.config import get_settings


config = get_settings()

DATABASE_URL = (
    f"postgresql+asyncpg://{config.DATABASE_USERNAME}:"
    f"{config.DATABASE_PASSWORD}@"
    f"{config.DATABASE_HOSTNAME}:"
    f"{config.DATABASE_PORT}/"
    f"{config.DATABASE_NAME}"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=config.DEBUG_MODE,
    future=True,
)

async_session = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session = async_session()

    try:
        yield session

    except Exception as ex:
        logger.error(f"DB error: {ex}")
        await session.rollback()
        raise

    finally:
        await session.close()


async def db_health_check() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True

    except Exception as ex:
        logger.error(f"[DB Health] Connection Error: {ex}")
        return False


import app.domain.models


async def create_db_and_tables():
    logger.info("Creating media service database tables...")

    async with engine.begin() as conn:
        await conn.run_sync(EntityBase.metadata.create_all)

    logger.success("Media service tables created successfully!")