import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from typing import Annotated
from loguru import logger

from app.domain.token_schemas import TokenSchema, RefreshRequest
from app.domain.user_schemas import (
    CompleteOnboardingSchema,
    UserCreateSchema,
    RegisterStartResponse,
    RegisterCompleteSchema,
    RegisterCompleteResponse,
    UserLoginSchema,
    ResendOTPSchema,
    ResendOTPResponseSchema,
    UserResponseSchema,
)
from app.dependencies import (
    get_register_service,
    get_login_service,
    get_jwt_service,
    get_current_user,
    get_redis_client,
    get_user_service,
)
from app.core.rate_limiter import RateLimiter
from app.services1.auth_services.signup_service import RegisterService
from app.services1.auth_services.login_service import LoginService
from app.services1.auth_services.jwt_service import JWTService
from app.services1.user_service import UserService


bearer_scheme = HTTPBearer(
    auto_error=True,
    scheme_name="BearerAuth",
)


auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


# ===================================================================
# 1. Register Endpoint - Rate Limited
# ===================================================================
@auth_router.post(
    "/register",
    response_model=RegisterStartResponse,
    status_code=status.HTTP_200_OK,
    summary="Step 1: Submit email & password -> Receive OTP",
)
async def register(
    user_data: UserCreateSchema,
    register_service: Annotated[RegisterService, Depends(get_register_service)],
    redis_client: redis.Redis = Depends(get_redis_client),
):
    rate_limiter = RateLimiter(redis_client)

    await rate_limiter.check(
        key=f"rate_limit:register:{user_data.email.lower()}",
        limit=5,
        window_seconds=3600,
        message="Too many registration attempts. Please try again later.",
    )

    logger.info(f"Starting registration for email: {user_data.email}")
    return await register_service.register_user(user_data)


# ===================================================================
# 2. Verify OTP Endpoint
# ===================================================================
@auth_router.post(
    "/verify-otp",
    response_model=RegisterCompleteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Step 2: Verify OTP -> Create User in DB",
)
async def verify_otp(
    verify_schema: RegisterCompleteSchema,
    register_service: Annotated[RegisterService, Depends(get_register_service)],
    redis_client: redis.Redis = Depends(get_redis_client),
):
    rate_limiter = RateLimiter(redis_client)

    await rate_limiter.check(
        key=f"rate_limit:verify_otp:{verify_schema.email.lower()}",
        limit=5,
        window_seconds=900,
        message="Too many OTP verification attempts. Please try again later.",
    )

    logger.info(f"Verifying OTP for user with email: {verify_schema.email}")
    return await register_service.verify_user(verify_schema)


# ===================================================================
# 3. Login Endpoint - Rate Limited
# ===================================================================
@auth_router.post(
    "/login",
    response_model=TokenSchema,
    status_code=status.HTTP_200_OK,
    summary="Step 3: User Login -> Receive JWT Token",
)
async def login(
    login_data: UserLoginSchema,
    login_service: Annotated[LoginService, Depends(get_login_service)],
    redis_client: redis.Redis = Depends(get_redis_client),
):
    rate_limiter = RateLimiter(redis_client)

    await rate_limiter.check(
        key=f"rate_limit:login:{login_data.email.lower()}",
        limit=5,
        window_seconds=300,
        message="Too many login attempts. Please try again later.",
    )

    return await login_service.authenticate_user(login_data)


# ===================================================================
# 4. Resend OTP Endpoint - Rate Limited
# ===================================================================
@auth_router.post(
    "/resend-otp",
    response_model=ResendOTPResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def resend_otp(
    resend_schema: ResendOTPSchema,
    register_service: Annotated[RegisterService, Depends(get_register_service)],
    redis_client: redis.Redis = Depends(get_redis_client),
):
    rate_limiter = RateLimiter(redis_client)

    await rate_limiter.check(
        key=f"rate_limit:resend_otp:{resend_schema.email.lower()}",
        limit=3,
        window_seconds=3600,
        message="Too many OTP resend requests. Please try again later.",
    )

    logger.info(f"Resending OTP for user with email: {resend_schema.email}")
    return await register_service.resend_otp(resend_schema)


# ===================================================================
# 5. Get Current User Endpoint
# ===================================================================

@auth_router.get(
    "/me-token",
    dependencies=[Depends(bearer_scheme)],
    openapi_extra={"security": [{"BearerAuth": []}]},
    summary="Test JWT middleware state",
)
async def me_token(request: Request):
    return {
        "user_id": request.state.user_id,
        "role": request.state.user_role,
        "payload": request.state.user,
    }



# ===================================================================
# 6. Refresh Token
# ===================================================================
@auth_router.post(
    "/refresh",
    summary="Refresh access token",
)
async def refresh_token(
    body: RefreshRequest,
    jwt_service: JWTService = Depends(get_jwt_service),
):
    tokens = await jwt_service.refresh(body.refresh_token)

    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": "bearer",
    }
# ===================================================================
# 6. 
# ===================================================================
@auth_router.post("/verifier/complete-onboarding")
async def complete_onboarding(
    payload: CompleteOnboardingSchema,
    user_service: UserService = Depends(get_user_service),
):
    try:
        await user_service.complete_verifier_onboarding(
            token=payload.token,
            new_password=payload.new_password
        )
        return {"message": "Account activated successfully. You can now login."}
    except Exception as e:
        # لاگ خطا یادت نره
        raise HTTPException(status_code=400, detail=str(e))