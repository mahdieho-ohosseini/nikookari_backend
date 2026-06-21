from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import or_, select
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
            .limit(1)

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
        profile.published_at = datetime.now(timezone.utc) if is_published else None

        await db.flush()
        await db.refresh(profile)
        return profile
    
    #لینک عمومی
    async def get_public_by_slug(
        self,
        db: AsyncSession,
        slug: str,
    ) -> Optional[CharityProfile]:
        result = await db.execute(
            select(CharityProfile).where(
                CharityProfile.slug == slug,
                CharityProfile.status == CharityProfileStatus.active,
                CharityProfile.is_published.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_public_profiles(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        province: Optional[str] = None,
        city: Optional[str] = None,
        activity_field: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CharityProfile]:
        stmt = select(CharityProfile).where(
            CharityProfile.status == CharityProfileStatus.active,
            CharityProfile.is_published.is_(True),
        )

        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    CharityProfile.charity_name.ilike(pattern),
                    CharityProfile.short_description.ilike(pattern),
                    CharityProfile.about_text.ilike(pattern),
                )
            )

        if province:
            stmt = stmt.where(CharityProfile.province == province)

        if city:
            stmt = stmt.where(CharityProfile.city == city)

        if activity_field:
            stmt = stmt.where(CharityProfile.activity_field == activity_field)

        stmt = stmt.order_by(CharityProfile.published_at.desc().nullslast())
        stmt = stmt.offset(offset).limit(limit)

        result = await db.execute(stmt)
        return list(result.scalars().all())




charity_profile_repository = CharityProfileRepository()
