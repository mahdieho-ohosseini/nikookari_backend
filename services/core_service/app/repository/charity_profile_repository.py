from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.RegInstitute_model import CharityProfile, CharityProfileStatus


class CharityProfileRepository:
    async def get_by_id(
        self,
        db: AsyncSession,
        profile_id: UUID,
    ) -> Optional[CharityProfile]:
        result = await db.execute(
            select(CharityProfile).where(CharityProfile.id == profile_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_user_id(
        self,
        db: AsyncSession,
        profile_id: UUID,
        user_id: UUID,
    ) -> Optional[CharityProfile]:
        result = await db.execute(
            select(CharityProfile).where(
                CharityProfile.id == profile_id,
                CharityProfile.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[CharityProfile]:
        result = await db.execute(
            select(CharityProfile)
            .where(CharityProfile.user_id == user_id)
            .order_by(CharityProfile.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def get_by_verification_request_id(
        self,
        db: AsyncSession,
        verification_request_id: UUID,
    ) -> Optional[CharityProfile]:
        result = await db.execute(
            select(CharityProfile).where(
                CharityProfile.verification_request_id == verification_request_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_slug(
        self,
        db: AsyncSession,
        slug: str,
    ) -> Optional[CharityProfile]:
        result = await db.execute(
            select(CharityProfile).where(CharityProfile.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_pending_profiles(
        self,
        db: AsyncSession,
    ) -> list[CharityProfile]:
        result = await db.execute(
            select(CharityProfile).where(
                CharityProfile.status == CharityProfileStatus.pending_review
            )
        )
        return list(result.scalars().all())

    async def create(
        self,
        db: AsyncSession,
        profile: CharityProfile,
    ) -> CharityProfile:
        db.add(profile)
        await db.flush()
        await db.refresh(profile)
        return profile

    async def update(
        self,
        db: AsyncSession,
        profile: CharityProfile,
        data: dict,
    ) -> CharityProfile:
        for field, value in data.items():
            setattr(profile, field, value)

        await db.flush()
        await db.refresh(profile)
        return profile

    async def set_status(
        self,
        db: AsyncSession,
        profile: CharityProfile,
        status: CharityProfileStatus,
    ) -> CharityProfile:
        profile.status = status

        await db.flush()
        await db.refresh(profile)
        return profile

    async def update_status(
        self,
        db: AsyncSession,
        profile_id: UUID,
        status: CharityProfileStatus,
    ) -> Optional[CharityProfile]:
        profile = await self.get_by_id(
            db=db,
            profile_id=profile_id,
        )

        if not profile:
            return None

        profile.status = status

        await db.flush()
        await db.refresh(profile)
        return profile

    async def update_is_published(
        self,
        db: AsyncSession,
        profile_id: UUID,
        is_published: bool,
    ) -> Optional[CharityProfile]:
        profile = await self.get_by_id(
            db=db,
            profile_id=profile_id,
        )

        if not profile:
            return None

        profile.is_published = is_published

        await db.flush()
        await db.refresh(profile)
        return profile
