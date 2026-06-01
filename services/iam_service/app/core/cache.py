import json
from typing import Any

from loguru import logger


async def get_json_cache(redis_client, key: str) -> dict[str, Any] | None:
    cached_value = await redis_client.get(key)

    if not cached_value:
        logger.info(f"Cache MISS | key={key}")
        return None

    try:
        logger.info(f"Cache HIT | key={key}")
        return json.loads(cached_value)

    except json.JSONDecodeError:
        logger.warning(f"Invalid cache value deleted | key={key}")
        await redis_client.delete(key)
        return None


async def set_json_cache(
    redis_client,
    key: str,
    value: dict[str, Any],
    ttl_seconds: int,
) -> None:
    await redis_client.setex(
        key,
        ttl_seconds,
        json.dumps(value, ensure_ascii=False),
    )

    logger.info(f"Cache SET | key={key} | ttl={ttl_seconds}s")


async def delete_cache(redis_client, key: str) -> None:
    await redis_client.delete(key)
    logger.info(f"Cache DELETE | key={key}")