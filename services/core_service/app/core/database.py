from typing import AsyncGenerator

from fastapi import HTTPException
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

    except HTTPException:
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


async def apply_lightweight_migrations() -> None:
    """
    مایگریشن سبک برای تغییرات کوچک دیتابیس در فاز فعلی پروژه.

    دلیل وجود این تابع:
    EntityBase.metadata.create_all فقط جدول‌های جدید را می‌سازد،
    اما ستون جدید را به جدول‌های قبلی اضافه نمی‌کند.

    پس اینجا ستون‌هایی که برای اتصال core_service به media_service لازم داریم
    به شکل امن و idempotent اضافه می‌شوند.
    یعنی اگر ستون از قبل وجود داشته باشد، خطا نمی‌دهد.
    """

    logger.info("Applying core_service lightweight migrations...")

    migration_queries = [
        """
        ALTER TABLE charity_verification_requests
        ADD COLUMN IF NOT EXISTS articles_of_association_file_id BIGINT;
        """,
        """
        ALTER TABLE charity_verification_requests
        ADD COLUMN IF NOT EXISTS activity_license_file_id BIGINT;
        """,
        """
        ALTER TABLE charity_verification_requests
        ADD COLUMN IF NOT EXISTS national_card_file_id BIGINT;
        """,
    ]

    async with engine.begin() as conn:
        for query in migration_queries:
            await conn.execute(text(query))

    logger.success("Core_service lightweight migrations applied successfully!")


# مدل‌ها باید import شوند تا SQLAlchemy جدول‌ها را داخل metadata بشناسد
import app.domain.models


async def create_db_and_tables() -> None:
    logger.info("Creating core_service database tables...")

    async with engine.begin() as conn:
        await conn.run_sync(EntityBase.metadata.create_all)

    logger.success("Core_service tables created successfully!")

    await apply_lightweight_migrations()