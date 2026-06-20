from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.RegInstitute_model import CharityProfile
from app.repository.charity_profile_repository import CharityProfileRepository


class PublicCharityService:
    def __init__(self):
        self.repository = CharityProfileRepository()

    async def list_public_charities(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        province: Optional[str] = None,
        city: Optional[str] = None,
        activity_field: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CharityProfile]:
        return await self.repository.list_public_profiles(
            db=db,
            search=search,
            province=province,
            city=city,
            activity_field=activity_field,
            limit=limit,
            offset=offset,
        )

    async def get_public_charity_by_slug(
        self,
        db: AsyncSession,
        slug: str,
    ) -> CharityProfile:
        profile = await self.repository.get_public_by_slug(
            db=db,
            slug=slug,
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Charity profile not found",
            )

        return profile
