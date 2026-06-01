from fastapi import APIRouter, Depends
import redis.asyncio as redis

from app.core.rate_limiter import RateLimiter
from app.domain.resetpass_schemas import (
    PasswordResetResendSchema,
    PasswordResetStartSchema,
    PasswordResetVerifySchema,
    PasswordResetCompleteSchema,
    PasswordResetResponseSchema,
)
from app.services1.auth_services.password_reset_service import PasswordResetService
from app.dependencies import (
    get_password_reset_service,
    get_redis_client,
)


router = APIRouter(
    prefix="/auth/password-reset",
    tags=["Auth"],
)


# -----------------------------
# 1. Start Password Reset - Rate Limited
# -----------------------------
@router.post(
    "/start",
    response_model=PasswordResetResponseSchema,
)
async def start_password_reset(
    data: PasswordResetStartSchema,
    service: PasswordResetService = Depends(get_password_reset_service),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    rate_limiter = RateLimiter(redis_client)

    await rate_limiter.check(
        key=f"rate_limit:password_reset_start:{data.email.lower()}",
        limit=3,
        window_seconds=3600,
        message="Too many password reset requests. Please try again later.",
    )

    return await service.start(data.email)


# -----------------------------
# 2. Verify Password Reset OTP - Rate Limited
# -----------------------------
@router.post(
    "/verify",
    response_model=PasswordResetResponseSchema,
)
async def verify_password_reset(
    data: PasswordResetVerifySchema,
    service: PasswordResetService = Depends(get_password_reset_service),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    rate_limiter = RateLimiter(redis_client)

    await rate_limiter.check(
        key=f"rate_limit:password_reset_verify:{data.email.lower()}",
        limit=5,
        window_seconds=900,
        message="Too many password reset OTP verification attempts. Please try again later.",
    )

    return await service.verify(data.email, data.otp)


# -----------------------------
# 3. Complete Password Reset - Rate Limited
# -----------------------------
@router.post(
    "/complete",
    response_model=PasswordResetResponseSchema,
)
async def complete_password_reset(
    data: PasswordResetCompleteSchema,
    service: PasswordResetService = Depends(get_password_reset_service),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    rate_limiter = RateLimiter(redis_client)

    await rate_limiter.check(
        key=f"rate_limit:password_reset_complete:{data.email.lower()}",
        limit=5,
        window_seconds=900,
        message="Too many password reset completion attempts. Please try again later.",
    )

    return await service.complete(data.email, data.new_password)


# -----------------------------
# 4. Resend Password Reset OTP - Rate Limited
# -----------------------------
@router.post(
    "/resend_otp",
    response_model=None,
)
async def resend_password_reset_otp(
    data: PasswordResetResendSchema,
    service: PasswordResetService = Depends(get_password_reset_service),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    rate_limiter = RateLimiter(redis_client)

    await rate_limiter.check(
        key=f"rate_limit:password_reset_resend:{data.email.lower()}",
        limit=3,
        window_seconds=3600,
        message="Too many password reset OTP resend requests. Please try again later.",
    )

    return await service.resend(data.email)