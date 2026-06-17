from uuid import UUID
from datetime import datetime

from fastapi import Depends
from loguru import logger
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # -----------------------------------
    # CREATE
    # -----------------------------------
    async def create_user(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        logger.info(f"User {user.user_id} created")
        return user

    # -----------------------------------
    # READ
    # -----------------------------------
    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(User).where(User.user_id == user_id)
        result = await self.session.execute(stmt)

        logger.info(f"Fetching user {user_id}")
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        stmt = select(User.user_id).where(User.email == email)
        result = await self.session.execute(stmt)

        return result.first() is not None

    async def list_all(self) -> list[User]:
        stmt = select(User).order_by(User.created_at.desc())
        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def count_by_role(self, role: str) -> int:
        stmt = select(func.count()).select_from(User).where(User.role == role)
        result = await self.session.execute(stmt)

        return int(result.scalar_one())

    async def count_active_by_role(self, role: str) -> int:
        stmt = (
            select(func.count())
            .select_from(User)
            .where(
                User.role == role,
                User.status == "active",
            )
        )
        result = await self.session.execute(stmt)

        return int(result.scalar_one())

    async def list_by_role(self, role: str) -> list[User]:
        stmt = (
            select(User)
            .where(User.role == role)
            .order_by(User.created_at.desc())
        )
        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    # -----------------------------------
    # UPDATE
    # -----------------------------------
    async def update_last_login(self, user_id: UUID) -> None:
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(
                last_login=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

        await self.session.execute(stmt)
        await self.session.commit()

    async def verify_user(self, user_id: UUID) -> None:
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(
                is_verified=True,
                updated_at=datetime.utcnow(),
            )
        )

        await self.session.execute(stmt)
        await self.session.commit()

    async def set_status(self, user_id: UUID, status: str) -> None:
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(
                status=status,
                updated_at=datetime.utcnow(),
            )
        )

        await self.session.execute(stmt)
        await self.session.commit()

    async def suspend_user(self, user_id: UUID) -> None:
        await self.set_status(user_id, "suspended")

    async def deactivate_user(self, user_id: UUID) -> None:
        await self.set_status(user_id, "inactive")

    async def activate_user(self, user_id: UUID) -> None:
        await self.set_status(user_id, "active")

    async def update_role(self, user_id: UUID, role: str) -> None:
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(
                role=role,
                updated_at=datetime.utcnow(),
            )
        )

        await self.session.execute(stmt)
        await self.session.commit()

    async def update_password(self, user_id: UUID, new_hash: str, must_change_password: bool | None = None,) -> None:
        values = {
        "password_hash": new_hash,
        "updated_at": datetime.utcnow(),}
        
        if must_change_password is not None:
               values["must_change_password"] = must_change_password
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(
              **values
            )
        )

        await self.session.execute(stmt)
        await self.session.commit()

    async def delete_user(self, user: User) -> None:
        await self.session.delete(user)
        await self.session.commit()

        logger.info(f"User {user.user_id} deleted")

    # -----------------------------------
    # ADMIN
    # -----------------------------------
    async def get_admin_user(self) -> User | None:
        stmt = (
            select(User)
            .where(User.role == "admin")
            .order_by(User.created_at.asc())
        )
        result = await self.session.execute(stmt)

        return result.scalars().first()

    async def get_active_admins(self) -> list[User]:
        stmt = (
            select(User)
            .where(
                User.role == "admin",
                User.status == "active",
            )
            .order_by(User.created_at.asc())
        )
        result = await self.session.execute(stmt)

        return list(result.scalars().all())


# ---------------------------------------
# Dependency
# ---------------------------------------
async def get_user_repository(
    session: AsyncSession = Depends(get_db),
) -> UserRepository:
    return UserRepository(session)
