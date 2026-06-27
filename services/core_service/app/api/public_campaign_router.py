from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.services.campaign_service import campaign_service

router = APIRouter(prefix="/public/campaigns", tags=["Public Campaigns"])


@router.get("")
async def list_public_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await campaign_service.get_public_campaigns(
        db=db,
        skip=skip,
        limit=limit,
    )


@router.get("/{campaign_id}")
async def get_public_campaign_detail(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    campaign = await campaign_service.get_public_campaign_by_id(
        db=db,
        campaign_id=campaign_id,
    )
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )
    return campaign
