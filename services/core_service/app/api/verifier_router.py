from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.domain.schemas.verifier_schema import (
    VerifierDashboardResponse,
    VerifierRejectRequest,
    VerifierRequestDetailResponse,
    VerifierRequestStatus,
    VerifierReviewResponse,
)
from app.services import verifier_service
from app.services.verifier_service import VerifierService


router = APIRouter(
    prefix="/verifier",
    tags=["Verifier"],
)

service = VerifierService()


@router.get(
    "/dashboard",
    response_model=VerifierDashboardResponse,
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
