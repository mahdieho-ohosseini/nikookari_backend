from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.schemas.charity_profile_schema import (
    PublicCharityProfileDetail,
    PublicCharityProfileListItem,
)
from app.services.public_charity_service import PublicCharityService


router = APIRouter(
    prefix="/charities",
    tags=["Public Charities"],
)

public_charity_service = PublicCharityService()


@router.get(
    "",
    response_model=list[PublicCharityProfileListItem],
)
async def list_public_charities(
    search: Optional[str] = Query(default=None),
    province: Optional[str] = Query(default=None),
    city: Optional[str] = Query(default=None),
    activity_field: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await public_charity_service.list_public_charities(
        db=db,
        search=search,
        province=province,
        city=city,
        activity_field=activity_field,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{slug}",
    response_model=PublicCharityProfileDetail,
)
async def get_public_charity_detail(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    return await public_charity_service.get_public_charity_by_slug(
        db=db,
        slug=slug,
    )
