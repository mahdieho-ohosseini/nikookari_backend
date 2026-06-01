from typing import Annotated
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.profile_repository import ProfileRepository
from app.services1.auth_services.hash_service import HashService
from app.services1.user_service import UserService
from app.domain.profile_schemas import UserProfileResponse


class ProfileService:
    def __init__(
        self,
        db: Annotated[AsyncSession, Depends(get_db)],
        user_service: Annotated[UserService, Depends()],
        hash_service: Annotated[HashService, Depends()],
    ):
        self.repo = ProfileRepository(db)
        self.user_service = user_service
        self.hash_service = hash_service

    async def get_profile(self, user_id: str):
       user = await self.repo.get_by_id(user_id)
       return UserProfileResponse.model_validate(user)

    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str
    ):
        user = await self.repo.get_by_id(user_id)

        if not self.hash_service.verify_password (
            current_password,
            user.password_hash
        ):
            raise HTTPException(status_code=400, detail="Invalid current password")

        await self.user_service.update_password(user.user_id, new_password)
        await self.user_service.invalidate_all_tokens(user.user_id)