from datetime import datetime, timedelta
import uuid
import jwt
from fastapi import HTTPException, Depends
from typing import Annotated
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.services1.auth_services.token_blacklist import (
    blacklist_token,
    is_token_blacklisted,
)

settings = get_settings()


class JWTService:
    def __init__(
        self,
        redis: Annotated[Redis, Depends(get_redis_client)],
    ):
        self.redis = redis

    # ------------------ Access Token ------------------
    def create_access_token(self, user_id: str) -> str:
        payload = {
            "sub": user_id,
            "jti": str(uuid.uuid4()),
            "type": "access",
            "exp": datetime.utcnow()
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        }

        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    # ------------------ Refresh Token ------------------
    def create_refresh_token(self, user_id: str) -> str:
        payload = {
            "sub": user_id,
            "jti": str(uuid.uuid4()),
            "type": "refresh",
            "exp": datetime.utcnow()
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        }

        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )

    # ------------------ Decode ------------------
    async def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(401, "Invalid token")

    # ------------------ Refresh Rotation ✅ ------------------
    async def refresh(self, refresh_token: str) -> dict:
        payload = await self.decode_token(refresh_token)

        if payload["type"] != "refresh":
            raise HTTPException(401, "Invalid refresh token")

        jti = payload["jti"]
        exp = payload["exp"]
        user_id = payload["sub"]

        # ⛔ reuse detection
        if await is_token_blacklisted(self.redis, jti):
            raise HTTPException(401, "Refresh token revoked")

        # ✅ invalidate old refresh token
        await blacklist_token(self.redis, jti, exp)

        return {
            "access_token": self.create_access_token(user_id),
            "refresh_token": self.create_refresh_token(user_id),
            "token_type": "bearer",
        }
