import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db

from app.core.dependencies import require_roles ,get_current_user
from app.domain.schemas.campaign_schema import (
    CampaignCreate,
    CampaignResponse,
    CampaignUpdate,
)
from app.services.campaign_service import campaign_service


router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _extract_user_id(current_user: dict) -> uuid.UUID:
    raw_user_id = current_user.get("user_id") or current_user.get("id")
    if raw_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authenticated user payload",
        )
    return uuid.UUID(str(raw_user_id))


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = _extract_user_id(current_user)
    return await campaign_service.create_campaign(db, campaign_data, user_id)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await campaign_service.get_campaign(db, campaign_id)


@router.get("/", response_model=list[CampaignResponse])
async def get_campaigns(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    charity_id: uuid.UUID | None = None,
):
    return await campaign_service.get_campaigns(
        db,
        skip=skip,
        limit=limit,
        charity_id=charity_id,
    )


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: uuid.UUID,
    campaign_data: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = _extract_user_id(current_user)
    return await campaign_service.update_campaign(db, campaign_id, campaign_data, user_id)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = _extract_user_id(current_user)
    await campaign_service.delete_campaign(db, campaign_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{campaign_id}/submit", response_model=CampaignResponse)
async def submit_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    actor_id = _extract_user_id(current_user)
    return await campaign_service.submit_campaign(db, campaign_id, actor_id)


@router.patch(
    "/{campaign_id}/approve",
    response_model=CampaignResponse,
    dependencies=[Depends(require_roles("admin", "verifier"))],
)
async def approve_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    actor_id = _extract_user_id(current_user)
    return await campaign_service.approve_campaign(db, campaign_id, actor_id)


@router.patch(
    "/{campaign_id}/reject",
    response_model=CampaignResponse,
    dependencies=[Depends(require_roles("admin", "verifier"))],
)
async def reject_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    actor_id = _extract_user_id(current_user)
    return await campaign_service.reject_campaign(db, campaign_id, actor_id)


@router.patch(
    "/{campaign_id}/suspend",
    response_model=CampaignResponse,
    dependencies=[Depends(require_roles("admin", "verifier"))],
)
async def suspend_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    actor_id = _extract_user_id(current_user)
    return await campaign_service.suspend_campaign(db, campaign_id, actor_id)


@router.patch(
    "/{campaign_id}/resume",
    response_model=CampaignResponse,
    dependencies=[Depends(require_roles("admin", "verifier"))],
)
async def resume_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    actor_id = _extract_user_id(current_user)
    return await campaign_service.resume_campaign(db, campaign_id, actor_id)
