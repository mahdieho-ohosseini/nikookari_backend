from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from loguru import logger
from app.core.config import get_settings
from app.core.base import EntityBase
from fastapi import HTTPException


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
    future=True
)

async_session = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=AsyncSession
)



async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session = async_session()
    try:
        yield session

    except HTTPException:
        # ✅ خطای بیزنسی، نه دیتابیس
        await session.rollback()
        raise

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

print("TABLES =", EntityBase.metadata.tables)
# ⬇⬇⬇ THIS IS THE MISSING PIECE ⬇⬇⬇
import app.domain.models

async def create_db_and_tables():
    # This loads the model class so SQLAlchemy registers the table

    print("Registered tables:", EntityBase.metadata.tables.keys())

    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(EntityBase.metadata.create_all)

    logger.success("All tables created successfully!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(create_db_and_tables())


import asyncio

async def main():
    is_ok = await db_health_check()
    print("✅ DB HEALTH =", is_ok)

if __name__ == "__main__":
    asyncio.run(main())
