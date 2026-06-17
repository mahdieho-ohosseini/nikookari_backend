import secrets
from typing import Optional
from uuid import UUID
import os
import secrets

from fastapi import Depends, HTTPException
from loguru import logger
from redis.asyncio import Redis

from app.domain.models import User
from app.domain.user_schemas import UserCreateSchema
from app.repositories.user_repository import UserRepository
from app.repositories.RefreshTokenRepository import RefreshTokenRepository
from app.services1.auth_services.email_service import EmailService
from app.services1.auth_services.hash_service import HashService
from app.services1.base_service import BaseService


class UserService(BaseService):
    def __init__(
        self,
        user_repository: UserRepository = Depends(),
        hash_service: HashService = Depends(),
        refresh_token_repository: Optional[RefreshTokenRepository] = None,
        email_service: Optional[EmailService] = None,
        redis_client: Optional[Redis] = None,
    ) -> None:
        super().__init__()
        self.user_repository = user_repository
        self.hash_service = hash_service
        self.refresh_token_repository = refresh_token_repository
        self.email_service = email_service
        self.redis_client = redis_client



    async def create_user(self, user_body: UserCreateSchema) -> User:
        logger.info(f"Creating user with email {user_body.email}")

        password_hash = self.hash_service.hash_password(user_body.password)

        user_model = User(
            full_name=user_body.full_name,
            email=user_body.email,
            password_hash=password_hash,
            role="donor",
            is_verified=True,
            status="active",
        )

        return await self.user_repository.create_user(user_model)

    async def delete_user(self, user: User) -> None:
        logger.info(f"Deleting user with id {user.user_id}")
        return await self.user_repository.delete_user(user)

    async def get_user(self, user_id: UUID) -> User | None:
        logger.info(f"Fetching user with id {user_id}")
        return await self.user_repository.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        logger.info(f"Fetching user with email {email}")
        return await self.user_repository.get_by_email(email)

    async def update_last_login(self, user_id: UUID) -> None:
        return await self.user_repository.update_last_login(user_id)

    async def invalidate_all_tokens(self, user_id: UUID) -> None:
        if self.refresh_token_repository is None:
            logger.warning(
                f"Cannot invalidate tokens for user {user_id}: RefreshTokenRepository not injected"
            )
            return

        await self.refresh_token_repository.delete_all_by_user_id(user_id)
    async def update_password(
        self,
        user_id: UUID,
        new_password: str,
        must_change_password: Optional[bool] = None,
        ) -> None:
        logger.info(f"Updating password for user {user_id}")

        hashed = self.hash_service.hash_password(new_password)

        await self.user_repository.update_password(
            user_id=user_id,
            new_hash=hashed,
            must_change_password=must_change_password,
        )   

         

    # ======================================================
    # RBAC / ARBAC Admin Services
    # ======================================================

    async def list_users(self) -> list[User]:
        logger.info("Admin requested user list")
        return await self.user_repository.list_all()

    async def get_user_detail(self, user_id: UUID) -> User:
        logger.info(f"Admin requested detail for user {user_id}")

        user = await self.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        return user

    async def suspend_user_by_id(self, user_id: UUID, actor_user: User) -> User:
        logger.info(
            f"User {actor_user.user_id} with role {actor_user.role} requested suspend for user {user_id}"
        )

        if actor_user.role != "admin":
            raise ValueError("Only admin can suspend users")

        user = await self.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        if user.user_id == actor_user.user_id:
            raise ValueError("You cannot suspend your own account")

        if user.role == "admin":
            admin_count = await self.user_repository.count_by_role("admin")
            if admin_count <= 1:
                raise ValueError("You cannot suspend the last admin account")

            raise ValueError("Admin cannot suspend another admin")

        await self.user_repository.suspend_user(user_id)

        logger.warning(f"User {user_id} was suspended by admin {actor_user.user_id}")

        updated_user = await self.get_user(user_id)
        if not updated_user:
            raise ValueError("User not found after update")

        return updated_user

    async def activate_user_by_id(self, user_id: UUID, actor_user: User) -> User:
        logger.info(
            f"User {actor_user.user_id} with role {actor_user.role} requested activation for user {user_id}"
        )

        if actor_user.role != "admin":
            raise ValueError("Only admin can activate users")

        user = await self.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        await self.user_repository.activate_user(user_id)

        logger.info(f"User {user_id} was activated by admin {actor_user.user_id}")

        updated_user = await self.get_user(user_id)
        if not updated_user:
            raise ValueError("User not found after update")

        return updated_user

    async def update_user_role(
        self,
        user_id: UUID,
        new_role: str,
        actor_user: User,
    ) -> User:
        logger.info(
            f"User {actor_user.user_id} with role {actor_user.role} requested role change for user {user_id} to {new_role}"
        )

        if actor_user.role != "admin":
            raise ValueError("Only admin can change user roles")

        allowed_roles = {
            "donor",
            "charity",
            "verifier",
            "admin",
        }

        if new_role not in allowed_roles:
            raise ValueError("Invalid role")

        user = await self.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        if user.user_id == actor_user.user_id:
            raise ValueError("You cannot change your own role")

        if user.role == "admin" and new_role != "admin":
            admin_count = await self.user_repository.count_by_role("admin")
            if admin_count <= 1:
                raise ValueError("You cannot change the role of the last admin")

            raise ValueError("Admin role cannot be downgraded by another admin")

        await self.user_repository.update_role(user_id, new_role)

        logger.warning(
            f"Role of user {user_id} changed to {new_role} by admin {actor_user.user_id}"
        )

        updated_user = await self.get_user(user_id)
        if not updated_user:
            raise ValueError("User not found after update")

        return updated_user

    def list_roles(self) -> list[str]:
        return [
            "donor",
            "charity",
            "verifier",
            "admin",
        ]

    async def create_initial_admin(self, user_body: UserCreateSchema) -> User:
        logger.info("Creating initial admin user")

        existing_admin = await self.user_repository.get_admin_user()
        if existing_admin:
            raise ValueError("An admin user already exists")

        hashed = self.hash_service.hash_password(user_body.password)

        admin_user = User(
            full_name=user_body.full_name,
            email=user_body.email,
            password_hash=hashed,
            role="admin",
            is_verified=True,
            status="active",
        )

        return await self.user_repository.create_user(admin_user)

    async def create_verifier(self, user_body: UserCreateSchema, actor_user: User) -> dict:
        logger.info(
            f"User {actor_user.user_id} with role {actor_user.role} requested verifier creation for {user_body.email}"
        )

        if actor_user.role != "admin":
            raise ValueError("Only admin can create verifier users")

        existing_user = await self.get_user_by_email(user_body.email)
        if existing_user:
            raise ValueError("A user with this email already exists")

        temporary_password = secrets.token_urlsafe(16)
        password_hash = self.hash_service.hash_password(temporary_password)

        verifier_user = User(
            full_name=user_body.full_name,
            email=user_body.email,
            password_hash=password_hash,
            role="verifier",
             must_change_password=True,
            is_verified=False,
            status="inactive",
        )

        created_user = await self.user_repository.create_user(verifier_user)
        try:
             if self.redis_client is None:
                 logger.error("Redis client is not injected; onboarding token was not stored")
                 return created_user
     
             if self.email_service is None:
                 logger.error("Email service is not injected; onboarding email was not sent")
                 return created_user
     
             onboarding_token = secrets.token_urlsafe(48)
             onboarding_key = f"onboarding:verifier:{onboarding_token}"
     
             await self.redis_client.set(
                 onboarding_key,
                 str(created_user.user_id),
                 ex=24 * 60 * 60,
             )
     
             frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
             onboarding_link = f"{frontend_url}/onboarding?token={onboarding_token}"
     
             await self.email_service.send_verifier_welcome_email(
                 email=created_user.email,
                 full_name=created_user.full_name,
                 onboarding_link=onboarding_link,
             )
     
        except Exception as error:
          logger.error(
            f"Failed to send verifier onboarding email to {created_user.email}: {error}"
            )
        logger.warning(
            f"Verifier user {created_user.user_id} created by admin {actor_user.user_id}"
        )

        return {
    "user_id": str(created_user.user_id),
    "full_name": created_user.full_name,
    "email": created_user.email,
    "role": created_user.role,
    "status": created_user.status,
    "is_verified": created_user.is_verified,
    "must_change_password": created_user.must_change_password,
    "onboarding_token": onboarding_token,
    "onboarding_link": onboarding_link,
      }

    
    
    async def complete_verifier_onboarding(self, token: str, new_password: str) -> None:
        if self.redis_client is None:
            raise ValueError("Redis client is not configured")

        onboarding_key = f"onboarding:verifier:{token}"
        user_id_str = await self.redis_client.get(onboarding_key)
        
        if not user_id_str:
            raise HTTPException(status_code=400, detail="Invalid or expired token")
        
        user_id = UUID(user_id_str)
        
        # ۱. آپدیت کردن پسورد و وضعیت کاربر
        await self.update_password(
            user_id=user_id,
            new_password=new_password,
            must_change_password=False
        )
        
        # ۲. فعال‌سازی نهایی کاربر
        await self.user_repository.activate_user(user_id) # این متد باید در repository باشد یا دستی انجام بده
        # اگر متد مخصوص برای فعال‌سازی در repo نداری، می‌توانی از update_status استفاده کنی:
        # await self.user_repository.update_status(user_id, "active")
        
        # ۳. تایید نهایی
        await self.user_repository.verify_user(user_id) # یک متد ساده برای set کردن is_verified=True
        
        # ۴. حذف توکن از Redis
        await self.redis_client.delete(onboarding_key)
        
        logger.info(f"Onboarding completed successfully for user {user_id}")

    
