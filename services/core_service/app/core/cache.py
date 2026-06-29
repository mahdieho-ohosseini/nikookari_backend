import json
from typing import Any

import redis.asyncio as redis
from loguru import logger


REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0


async def get_redis_client() -> redis.Redis:
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
    )


async def get_json_cache(key: str) -> Any | None:
    try:
        redis_client = await get_redis_client()
        cached_value = await redis_client.get(key)

        if not cached_value:
            logger.info(f"Cache MISS | key={key}")
            return None

        logger.info(f"Cache HIT | key={key}")
        return json.loads(cached_value)

    except Exception as exc:
        logger.warning(f"Cache read skipped | key={key} | error={exc}")
        return None


async def set_json_cache(
    key: str,
    value: Any,
    ttl_seconds: int,
) -> None:
    try:
        redis_client = await get_redis_client()
        await redis_client.setex(
            key,
            ttl_seconds,
            json.dumps(value, ensure_ascii=False),
        )

        logger.info(f"Cache SET | key={key} | ttl={ttl_seconds}s")

    except Exception as exc:
        logger.warning(f"Cache write skipped | key={key} | error={exc}")