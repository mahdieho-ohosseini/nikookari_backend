from fastapi import Request, HTTPException
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from core.config import get_settings
import os

async def jwt_middleware(request: Request, call_next):
    path = request.url.path

    public_routes = {
        "/auth/login",
        "/auth/register",
        "/auth/verify-otp",
        "/auth/refresh",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    if any(path.startswith(p) for p in public_routes):
        return await call_next(request)

    if os.getenv("DEV_MODE", "false").lower() == "true":
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid token")

    token = auth_header.split(" ")[1]

    settings = get_settings()  # ✅ خیلی مهم

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        redis = request.app.state.redis
        jti = payload.get("jti")

        if jti and await redis.exists(f"blacklist:{jti}"):
            raise HTTPException(401, "Token revoked")

        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")

        request.state.user = payload

    except ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except InvalidTokenError:
        raise HTTPException(401, "Invalid token")

    return await call_next(request)
