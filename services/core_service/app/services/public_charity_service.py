from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_json_cache, set_json_cache
from app.domain.models.RegInstitute_model import CharityProfile
from app.domain.schemas.charity_profile_schema import (
    PublicCharityProfileDetail,
    PublicCharityProfileListItem,
)
from app.repository.charity_profile_repository import CharityProfileRepository


PUBLIC_CHARITY_CACHE_TTL_SECONDS = 60


class PublicCharityService:
    def __init__(self):
        self.repository = CharityProfileRepository()

    def _build_list_cache_key(
        self,
        *,
        search: Optional[str],
        province: Optional[str],
        city: Optional[str],
        activity_field: Optional[str],
        limit: int,
        offset: int,
    ) -> str:
        return (
            "core:public_charities:list:"
            f"search={search or ''}:"
            f"province={province or ''}:"
            f"city={city or ''}:"
            f"activity_field={activity_field or ''}:"
            f"limit={limit}:"
            f"offset={offset}"
        )

    def _build_detail_cache_key(self, slug: str) -> str:
        return f"core:public_charities:detail:{slug}"

    async def list_public_charities(
        self,
        db: AsyncSession,
        search: Optional[str] = None,
        province: Optional[str] = None,
        city: Optional[str] = None,
        activity_field: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CharityProfile] | list[dict]:
        cache_key = self._build_list_cache_key(
            search=search,
            province=province,
            city=city,
            activity_field=activity_field,
            limit=limit,
            offset=offset,
        )

        cached_value = await get_json_cache(cache_key)
        if cached_value is not None:
            return cached_value

        profiles = await self.repository.list_public_profiles(
            db=db,
            search=search,
            province=province,
            city=city,
            activity_field=activity_field,
            limit=limit,
            offset=offset,
        )

        cache_value = [
            PublicCharityProfileListItem.model_validate(profile).model_dump(
                mode="json"
            )
            for profile in profiles
        ]

        await set_json_cache(
            key=cache_key,
            value=cache_value,
            ttl_seconds=PUBLIC_CHARITY_CACHE_TTL_SECONDS,
        )

        return profiles

    async def get_public_charity_by_slug(
        self,
        db: AsyncSession,
        slug: str,
    ) -> CharityProfile | dict:
        cache_key = self._build_detail_cache_key(slug)

        cached_value = await get_json_cache(cache_key)
        if cached_value is not None:
            return cached_value

        profile = await self.repository.get_public_by_slug(
            db=db,
            slug=slug,
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Charity profile not found",
            )

        cache_value = PublicCharityProfileDetail.model_validate(profile).model_dump(
            mode="json"
        )

        await set_json_cache(
            key=cache_key,
            value=cache_value,
            ttl_seconds=PUBLIC_CHARITY_CACHE_TTL_SECONDS,
        )

        return profile