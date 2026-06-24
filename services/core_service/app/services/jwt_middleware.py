import os
import uuid

import jwt
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import get_settings


PUBLIC_ROUTES = (
    "/",
    "/health",
    "/openapi.json",
    "/auth/login",
    "/auth/register",
    "/auth/verify-otp",
    "/auth/refresh",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/verify-otp",
    "/api/v1/auth/refresh",
    "/api/v1/charities",
    "/charities",
    "/docs",
    "/redoc",
    "/api/v1/payments/callback",
)


def is_public_route(path: str) -> bool:
    return any(
        path == route or path.startswith(f"{route}/")
        for route in PUBLIC_ROUTES
    )


def decode_access_token(token: str) -> dict:
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")
        role = payload.get("role")

        # 🔥 مهم: validation UUID برای جلوگیری از خراب شدن سیستم
        try:
            uuid.UUID(str(user_id))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user_id format (must be UUID)",
            )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject",
            )

        if not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing role",
            )

        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


async def jwt_middleware(request: Request, call_next):
    path = request.url.path

    if is_public_route(path):
        return await call_next(request)

    if os.getenv("DEV_MODE", "false").lower() == "true":
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Missing or invalid token"},
        )

    token = auth_header.removeprefix("Bearer ").strip()

    try:
        payload = decode_access_token(token)

        jti = payload.get("jti")
        redis = getattr(request.app.state, "redis", None)

        if redis and jti and await redis.exists(f"blacklist:{jti}"):
            return JSONResponse(
                status_code=401,
                content={"detail": "Token revoked"},
            )

        # ✅ استاندارد نهایی سیستم تو
        request.state.user_id = payload.get("sub")
        request.state.user_role = payload.get("role")
        request.state.user = payload

    except HTTPException as exc:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    return await call_next(request)


def get_current_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token",
        )

    return {
        **user,
        "user_id": user.get("sub"),
        "role": user.get("role"),
    }


def get_optional_current_user(request: Request) -> dict | None:
    user = getattr(request.state, "user", None)

    if not user:
        return None

    return {
        **user,
        "user_id": user.get("sub"),
        "role": user.get("role"),
    }