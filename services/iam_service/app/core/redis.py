from redis.asyncio import Redis
from loguru import logger
from typing import Optional

from app.core.config import get_settings

config = get_settings()

redis_client: Optional[Redis] = None  # فقط یک Redis client ساخته شود


async def get_redis() -> Redis:
    """
    Create or return the existing Redis client (singleton).
    """
    global redis_client
    if redis_client is None:
        try:
            redis_client = Redis.from_url(
                config.REDIS_URL,      # مثل redis://localhost:6379/0
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("[Redis] Client initialized")
        except Exception as e:
            logger.error(f"[Redis] Initialization failed: {e}")
            raise

    return redis_client


async def get_redis_client() -> Redis:
    """
    FastAPI dependency wrapper — always returns a ready Redis client.
    """
    return await get_redis()


async def redis_health_check() -> bool:
    """
    Tests Redis connection (PING).
    """
    try:
        redis = await get_redis()
        pong = await redis.ping()
        return pong is True
    except Exception as e:
        logger.error(f"[Redis Health] Connection failed: {e}")
        return False
