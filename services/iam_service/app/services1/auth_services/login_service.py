from fastapi import HTTPException, status
from loguru import logger

from app.core.config import get_settings
from app.domain.token_schemas import TokenSchema
from app.domain.user_schemas import UserLoginSchema
from app.logging.audit_logger import audit_log
from app.services1.auth_services.hash_service import HashService
from app.services1.auth_services.jwt_service import JWTService
from app.services1.base_service import BaseService
from app.services1.user_service import UserService


settings = get_settings()


class LoginService(BaseService):
    def __init__(
        self,
        user_service: UserService,
        hash_service: HashService,
        jwt_service: JWTService,
        redis_client,
    ) -> None:
        super().__init__()
        self.user_service = user_service
        self.hash_service = hash_service
        self.jwt_service = jwt_service
        self.redis = redis_client

    async def authenticate_user(self, user: UserLoginSchema) -> TokenSchema:
        existing_user = await self.user_service.get_user_by_email(user.email)

        logger.info(f"Authenticating user with email {user.email}")

        if not existing_user:
            logger.error(f"User with email {user.email} does not exist")

            audit_log(
                event="login_failed",
                outcome="failure",
                actor_email=user.email,
                details={"reason": "user_not_found"},
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not exist",
            )

        if not existing_user.is_verified:
            logger.error(f"User with email {user.email} is not verified")

            audit_log(
                event="login_failed",
                outcome="failure",
                actor_id=str(existing_user.user_id),
                actor_email=existing_user.email,
                actor_role=existing_user.role,
                details={"reason": "user_not_verified"},
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not verified",
            )

        if existing_user.status != "active":
            logger.error(f"User with email {user.email} is not active")

            audit_log(
                event="login_failed",
                outcome="failure",
                actor_id=str(existing_user.user_id),
                actor_email=existing_user.email,
                actor_role=existing_user.role,
                details={
                    "reason": "user_not_active",
                    "status": existing_user.status,
                },
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active",
            )

        if not self.hash_service.verify_password(
            user.password,
            existing_user.password_hash,
        ):
            logger.error(f"Invalid password for user email {user.email}")

            audit_log(
                event="login_failed",
                outcome="failure",
                actor_id=str(existing_user.user_id),
                actor_email=existing_user.email,
                actor_role=existing_user.role,
                details={"reason": "invalid_password"},
            )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        await self.user_service.update_last_login(existing_user.user_id)

        access_token = self.jwt_service.create_access_token(
            str(existing_user.user_id),
            existing_user.role,
        )

        refresh_token = self.jwt_service.create_refresh_token(
            str(existing_user.user_id),
            existing_user.role,
        )

        await self.redis.setex(
            f"refresh:{refresh_token}",
            settings.REFRESH_TOKEN_EXPIRE_DAYS,
            str(existing_user.user_id),
        )

        audit_log(
            event="login_success",
            outcome="success",
            actor_id=str(existing_user.user_id),
            actor_email=existing_user.email,
            actor_role=existing_user.role,
        )

        logger.info(f"User with email {user.email} authenticated successfully")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user_id": str(existing_user.user_id),
            "email": existing_user.email,
            "role": existing_user.role,
        }