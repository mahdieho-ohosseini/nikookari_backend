from datetime import datetime, timezone
from typing import Any

# ---------------------------
# Blacklist Refresh Token JTI
# ---------------------------

async def blacklist_token(redis: Any, jti: str, exp: int) -> None:
    """
    Blacklist a token JTI until its expiration time.
    """
    ttl = exp - int(datetime.now(timezone.utc).timestamp())

    # اگر توکن عملاً منقضی شده، دیگه ذخیره نکن
    if ttl <= 0:
        return

    key = f"blacklist:jti:{jti}"
    await redis.setex(key, ttl, "1")


# ---------------------------
# Check if Token is Blacklisted
# ---------------------------

async def is_token_blacklisted(redis: Any, jti: str) -> bool:
    key = f"blacklist:jti:{jti}"
    return await redis.exists(key) > 0
