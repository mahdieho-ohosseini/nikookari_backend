# app/services/charity_verification_service.py

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.RegInstitute_model import CharityVerificationStatus
from app.repository.RegInstitute_repository import CharityVerificationRepository
from app.domain.schemas.RegInstitute_schema import CharityVerificationRequestCreateSchema


class CharityVerificationService:
    def __init__(self, db: AsyncSession):
        self.repository = CharityVerificationRepository(db)

    async def create_request(
        self,
        user_id: UUID,
        payload: CharityVerificationRequestCreateSchema,
    ):
        if await self.repository.has_open_request(user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="شما یک درخواست در حال بررسی دارید.",
            )

        if await self.repository.has_approved_request(user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="خیریه شما قبلاً تأیید شده است.",
            )

        data = payload.model_dump()
        data["user_id"] = user_id
        data["status"] = CharityVerificationStatus.PENDING

        return await self.repository.create(data)
