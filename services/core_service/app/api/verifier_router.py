from typing import Optional
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.campaign_router import _extract_user_id
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.domain.schemas.campaign_schema import CampaignResponse
from app.domain.schemas.verifier_schema import (
    VerifierDashboardResponse,
    VerifierRejectRequest,
    VerifierRequestDetailResponse,
    VerifierRequestStatus,
    VerifierReviewResponse,
)
from app.services.campaign_service import campaign_service
from app.services.charity_profile_service import CharityProfileService
from app.services.verifier_service import VerifierService


router = APIRouter(prefix="/verifier")

service = VerifierService()
charity_profile_service = CharityProfileService()


@router.get(
    "/dashboard",
    response_model=VerifierDashboardResponse,
    tags=["Verifier"],
    dependencies=[Depends(require_roles("verifier", "admin"))],
)
async def get_verifier_dashboard(
    status: Optional[VerifierRequestStatus] = Query(None),
    activity_field: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_dashboard_data(
        db=db,
        status_filter=status.value if status else None,
        activity_field=activity_field,
        search_query=search,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/requests/{request_id}",
    response_model=VerifierRequestDetailResponse,
    tags=["Verifier"],
    dependencies=[Depends(require_roles("verifier", "admin"))],
)
async def get_verifier_request_detail(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    return await service.get_request_detail(
        db=db,
        request_id=request_id,
    )


@router.post(
    "/requests/{request_id}/approve",
    response_model=VerifierReviewResponse,
    tags=["Verification Requests"],
    dependencies=[Depends(require_roles("verifier", "admin"))],
)
async def approve_verification_request(
    request_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    verifier_id = UUID(str(request.state.user_id))

    return await service.approve_request(
        db=db,
        request_id=request_id,
        verifier_id=verifier_id,
    )


@router.post(
    "/requests/{request_id}/reject",
    response_model=VerifierReviewResponse,
    tags=["Verification Requests"],
    dependencies=[Depends(require_roles("verifier", "admin"))],
)
async def reject_verification_request(
    request_id: UUID,
    payload: VerifierRejectRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    verifier_id = UUID(str(request.state.user_id))

    return await service.reject_request(
        db=db,
        request_id=request_id,
        verifier_id=verifier_id,
        reason=payload.reason,
    )


@router.get(
    "/charity-profiles/pending",
    tags=["Charity Profile Management"],
    dependencies=[Depends(require_roles("verifier", "admin"))],
)
async def get_pending_charity_profiles(
    db: AsyncSession = Depends(get_db),
):
    return await charity_profile_service.get_profiles_for_review(db=db)


@router.post(
    "/charity-profiles/{profile_id}/approve",
    tags=["Charity Profile Management"],
    dependencies=[Depends(require_roles("verifier", "admin"))],
)
async def approve_charity_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    profile = await charity_profile_service.approve_profile(
        db=db,
        profile_id=profile_id,
    )

    return {
        "id": profile.id,
        "status": profile.status,
        "is_published": profile.is_published,
        "message": "Charity profile approved successfully",
    }


@router.post(
    "/charity-profiles/{profile_id}/reject",
    tags=["Charity Profile Management"],
    dependencies=[Depends(require_roles("verifier", "admin"))],
)
async def reject_charity_profile(
    profile_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    profile = await charity_profile_service.reject_profile(
        db=db,
        profile_id=profile_id,
    )

    return {
        "id": profile.id,
        "status": profile.status,
        "is_published": profile.is_published,
        "message": "Charity profile rejected successfully",
    }


@router.patch(
    "/{campaign_id}/approve",
    response_model=CampaignResponse,
    tags=["Campaign Management"],
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
    tags=["Campaign Management"],
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
    tags=["Campaign Management"],
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
    tags=["Campaign Management"],
    dependencies=[Depends(require_roles("admin", "verifier"))],
)
async def resume_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    actor_id = _extract_user_id(current_user)
    return await campaign_service.resume_campaign(db, campaign_id, actor_id)
