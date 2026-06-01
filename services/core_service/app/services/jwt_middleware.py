# app/services/jwt_middleware.py

from fastapi import Request, HTTPException
import jwt
from app.core.config import get_settings
import os
from loguru import logger
import re

settings = get_settings()


async def jwt_middleware(request: Request, call_next):
    """
    JWT Middleware for protected routes
    """
    
    # ✅ 0. Allow CORS preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    method = request.method
    
    logger.info(f"🔵 Middleware checking: {method} {path}")

    # ✅ 1. مسیرهای کاملاً عمومی
    public_exact_routes = [
        "/docs",
        "/openapi.json",
        "/redoc",
        "/favicon.ico",
        "/health",
        "/",
    ]
    
    if path in public_exact_routes:
        logger.info(f"✅ Exact public route: {path}")
        return await call_next(request)

    # ✅ 2. مسیرهای Auth (عمومی)
    auth_public_routes = [
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/verify-otp",
        "/api/v1/auth/resend-otp",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password/verify",
        "/api/v1/auth/reset-password/complete",
    ]
    
    if path in auth_public_routes:
        logger.info(f"✅ Auth public route: {path}")
        return await call_next(request)

    # ✅ 3. الگوهای Regex برای فرم‌های عمومی
    public_patterns = [
        # بدون /api/v1
        r"^/public/forms/s/[^/]+$",           # GET form detail
        r"^/public/forms/s/[^/]+/responses$", # POST response
        
        # با /api/v1 (اگه بعداً لازم شد)
        r"^/api/v1/public/forms/s/[^/]+$",
        r"^/api/v1/public/forms/s/[^/]+/responses$",
    ]

    # بررسی الگوهای عمومی
    for i, pattern in enumerate(public_patterns):
        if re.match(pattern, path):
            logger.info(f"✅ Public pattern matched (#{i}): {path}")
            return await call_next(request)
    
    logger.warning(f"🔒 Protected endpoint, checking JWT: {path}")

    # ✅ 4. Dev mode bypass
    if os.getenv("DEV_MODE", "false").lower() == "true":
        logger.warning("🚨 DEV_MODE enabled — JWT bypassed")
        request.state.user_id = "00000000-0000-0000-0000-000000000000"
        return await call_next(request)

    # ✅ 5. Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.error(f"❌ Missing Authorization header for {path}")
        raise HTTPException(
            status_code=403,
            detail="Missing or invalid Authorization header",
        )

    token = auth_header.split(" ", 1)[1]

    # ✅ 6. Decode & validate token
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        # ✅ 7. Token type
        if payload.get("type") != "access":
            logger.error(f"❌ Invalid token type for {path}")
            raise HTTPException(
                status_code=403,
                detail="Invalid token type (access required)",
            )

        # ✅ 8. Extract user_id
        user_id = payload.get("sub")
        if not user_id:
            logger.error(f"❌ Token missing subject for {path}")
            raise HTTPException(
                status_code=403,
                detail="Token missing subject (sub)",
            )

        request.state.user_id = user_id
        logger.info(f"✅ Authenticated user {user_id} for {path}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ JWT error: {e}")
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    return await call_next(request)
