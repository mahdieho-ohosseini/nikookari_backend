from fastapi import Request
from fastapi.responses import JSONResponse
from jwt import ExpiredSignatureError, InvalidTokenError
import jwt
import os

from app.core.config import get_settings


PUBLIC_ROUTES = (
    "/",
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
    "/openapi.json",
    "/redoc",
)


def is_public_route(path: str) -> bool:
    return any(
        path == route or path.startswith(f"{route}/")
        for route in PUBLIC_ROUTES
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
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if payload.get("type") != "access":
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token type"},
            )

        user_id = payload.get("sub")
        role = payload.get("role")
        jti = payload.get("jti")

        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token missing subject"},
            )

        if not role:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token missing role"},
            )

        redis = getattr(request.app.state, "redis", None)
        if redis and jti and await redis.exists(f"blacklist:{jti}"):
            return JSONResponse(
                status_code=401,
                content={"detail": "Token revoked"},
            )

        request.state.user_id = user_id
        request.state.user_role = role
        request.state.user = payload

    except ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"detail": "Token expired"},
        )
    except InvalidTokenError:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid token"},
        )

    return await call_next(request)
