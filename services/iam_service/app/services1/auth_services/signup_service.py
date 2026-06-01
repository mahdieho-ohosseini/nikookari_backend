from typing import Annotated, Any
from loguru import logger
from fastapi import Depends, HTTPException, status

from app.domain.user_schemas import (
    UserCreateSchema,
    RegisterStartResponse,
    RegisterCompleteSchema,
    RegisterCompleteResponse,
    ResendOTPSchema,
    ResendOTPResponseSchema,
    UserResponseSchema,
)

from app.services1.auth_services.otp_service import OTPService
from app.services1.base_service import BaseService
from app.services1.user_service import UserService
from app.core.redis import get_redis_client


class RegisterService(BaseService):
    def __init__(
        self,
        user_service: Annotated[UserService, Depends()],
        otp_service: Annotated[OTPService, Depends()],
        redis_client: Annotated[Any, Depends(get_redis_client)],
    ) -> None:
        super().__init__()
        self.user_service = user_service
        self.otp_service = otp_service
        self.redis = redis_client

    # ============================================
    # Step 1 — Register (store in redis + send OTP)
    # ============================================
    async def register_user(
        self,
        user: UserCreateSchema
    ) -> RegisterStartResponse:

        # check duplicate user
        existing = await self.user_service.get_user_by_email(user.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists",
            )

        # store pending user in redis (10 minutes)
        await self.redis.setex(
            f"pending_user:{user.email}",
            time=600,
            value=user.model_dump_json(),
        )

        await self.otp_service.send_otp(user.email)

        logger.info(f"Registration started for {user.email}")

        return RegisterStartResponse(
            success=True,
            message="OTP sent to email",
        )

    # ============================================
    # Step 2 — Verify OTP + Create User
    # ============================================
    async def verify_user(
        self,
        verify_schema: RegisterCompleteSchema
    ) -> RegisterCompleteResponse:

        email = verify_schema.email
        otp = verify_schema.otp

        # verify otp
        verified = await self.otp_service.verify_otp(email, otp)
        if not verified:
            logger.warning(f"Invalid OTP attempt for {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP",
            )

        # load pending user
        raw = await self.redis.get(f"pending_user:{email}")
        if not raw:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration expired. Please register again.",
            )

        # parse json -> schema
        data = UserCreateSchema.model_validate_json(raw)

        # create user
        new_user = await self.user_service.create_user(data)

        # cleanup
        await self.redis.delete(f"pending_user:{email}")

        logger.success(f"User registered successfully: {email}")

        return RegisterCompleteResponse(
            success=True,
            verified=True,
            message="User created successfully",
            user=UserResponseSchema.from_orm(new_user),
        )

    # ============================================
    # Resend OTP
    # ============================================
    async def resend_otp(
        self,
        resend_schema: ResendOTPSchema
    ) -> ResendOTPResponseSchema:

        email = resend_schema.email

        # check pending registration
        pending = await self.redis.get(f"pending_user:{email}")
        if not pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending registration for this email",
            )

        # cooldown check (OTP exists)
        if await self.otp_service.check_exist(email):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="OTP already sent. Please wait before requesting again.",
            )

        await self.otp_service.send_otp(email)

        logger.info(f"OTP resent for {email}")

        return ResendOTPResponseSchema(
            success=True,
            message="OTP resent successfully",
        )
