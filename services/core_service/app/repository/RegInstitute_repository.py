from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.RegInstitute_model import (
    CharityVerificationRequest,
    CharityVerificationStatus,
)


class CharityVerificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> CharityVerificationRequest:
        verification_request = CharityVerificationRequest(**data)
        self.db.add(verification_request)
        await self.db.commit()
        await self.db.refresh(verification_request)
        return verification_request

    async def get_by_id(self, request_id: UUID) -> Optional[CharityVerificationRequest]:
        stmt = select(CharityVerificationRequest).where(
            CharityVerificationRequest.id == request_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_by_user_id(self, user_id: UUID) -> Optional[CharityVerificationRequest]:
        stmt = (
            select(CharityVerificationRequest)
            .where(CharityVerificationRequest.user_id == user_id)
            .order_by(CharityVerificationRequest.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def has_open_request(self, user_id: UUID) -> bool:
        stmt = select(CharityVerificationRequest.id).where(
            CharityVerificationRequest.user_id == user_id,
            CharityVerificationRequest.status == CharityVerificationStatus.PENDING,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def has_approved_request(self, user_id: UUID) -> bool:
        stmt = select(CharityVerificationRequest.id).where(
            CharityVerificationRequest.user_id == user_id,
            CharityVerificationRequest.status == CharityVerificationStatus.APPROVED,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
