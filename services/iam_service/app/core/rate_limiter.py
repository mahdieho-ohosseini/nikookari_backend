from fastapi import HTTPException, status
from loguru import logger


class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        message: str,
    ) -> None:
        current_count = await self.redis.incr(key)

        if current_count == 1:
            await self.redis.expire(key, window_seconds)

        ttl = await self.redis.ttl(key)

        if current_count > limit:
            logger.warning(
                f"Rate limit exceeded | key={key} | "
                f"limit={limit} | window={window_seconds}s | ttl={ttl}s"
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": message,
                    "limit": limit,
                    "retry_after_seconds": max(ttl, 0),
                },
            )

        logger.info(
            f"Rate limit check passed | key={key} | "
            f"count={current_count}/{limit} | window={window_seconds}s"
        )