from typing import Annotated, Any
from fastapi import Depends, HTTPException, status

from app.core.redis import get_redis_client


from typing import Annotated, Any
from fastapi import Depends
from app.core.redis import get_redis_client
from app.services1.auth_services.jwt_service import JWTService
from app.services1.auth_services.token_blacklist import blacklist_token

class LogoutService:
    def __init__(
        self,
        jwt_service: Annotated[JWTService, Depends()],
        redis: Annotated[Any, Depends(get_redis_client)],
    ):
        self.jwt = jwt_service
        self.redis = redis

    async def logout(self, refresh_token: str):
        payload = await self.jwt.decode_token(refresh_token)

        if payload["type"] != "refresh":
            raise HTTPException(400, "Invalid token type")

        jti = payload["jti"]
        exp = payload["exp"]

        # ✅ واقعی‌ترین Logout
        await blacklist_token(self.redis, jti, exp)
