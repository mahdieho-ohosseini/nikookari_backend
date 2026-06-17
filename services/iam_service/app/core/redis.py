from typing import Optional

from loguru import logger
from redis.asyncio import Redis

from app.core.config import get_settings

config = get_settings()
redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    global redis_client

    if redis_client is None:
        try:
            redis_client = Redis.from_url(
                config.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            logger.info("[Redis] Client initialized")
        except Exception as error:
            logger.error(f"[Redis] Initialization failed: {error}")
            raise

    return redis_client


async def get_redis_client() -> Redis:
    return await get_redis()
