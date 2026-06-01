from typing import Optional
from uuid import UUID

from fastapi import Depends
from loguru import logger

from app.domain.models import User
from app.domain.user_schemas import UserCreateSchema
from app.repositories.user_repository import UserRepository
from app.repositories.RefreshTokenRepository import RefreshTokenRepository
from app.services1.auth_services.hash_service import HashService
from app.services1.base_service import BaseService


class UserService(BaseService):
    def __init__(
        self,
        user_repository: UserRepository = Depends(),
        hash_service: HashService = Depends(),
        refresh_token_repository: Optional[RefreshTokenRepository] = None,
    ) -> None:
        super().__init__()
        self.user_repository = user_repository
        self.hash_service = hash_service
        self.refresh_token_repository = refresh_token_repository

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

    async def update_password(self, user_id: UUID, new_password: str) -> None:
        logger.info(f"Updating password for user {user_id}")

        hashed = self.hash_service.hash_password(new_password)
        await self.user_repository.update_password(user_id, hashed)

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

        user = await self.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        if user.user_id == actor_user.user_id:
            raise ValueError("You cannot suspend your own account")

        if actor_user.role == "admin" and user.role in {"admin", "super_admin"}:
            raise ValueError("Admin cannot suspend admin or super_admin users")

        await self.user_repository.suspend_user(user_id)

        logger.warning(f"User {user_id} was suspended by {actor_user.user_id}")

        updated_user = await self.get_user(user_id)
        if not updated_user:
            raise ValueError("User not found after update")

        return updated_user

    async def activate_user_by_id(self, user_id: UUID, actor_user: User) -> User:
        logger.info(
            f"User {actor_user.user_id} with role {actor_user.role} requested activation for user {user_id}"
        )

        user = await self.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        await self.user_repository.activate_user(user_id)

        logger.info(f"User {user_id} was activated by {actor_user.user_id}")

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
            f"Super admin {actor_user.user_id} requested role change for user {user_id} to {new_role}"
        )

        allowed_roles = {
            "donor",
            "charity_representative",
            "admin",
        }

        if new_role not in allowed_roles:
            raise ValueError("Invalid role")

        user = await self.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        if user.user_id == actor_user.user_id:
            raise ValueError("You cannot change your own role")

        await self.user_repository.update_role(user_id, new_role)

        logger.warning(
            f"Role of user {user_id} changed to {new_role} by super_admin {actor_user.user_id}"
        )

        updated_user = await self.get_user(user_id)
        if not updated_user:
            raise ValueError("User not found after update")

        return updated_user

    def list_roles(self) -> list[str]:
        return [
            "donor",
            "charity_representative",
            "admin",
            "super_admin",
        ]

    async def create_admin(self, user_body: UserCreateSchema) -> User:
        logger.info("Creating admin user")

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