from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.schemas.campaign_report_schema import (
    CampaignReportCreate,
    CampaignReportResponse,
    CampaignReportUpdate,
)
from app.services.campaign_report_service import CampaignReportService
from app.services.jwt_middleware import get_current_user


router = APIRouter(prefix="/campaigns", tags=["Campaign Reports"])


@router.post(
    "/{campaign_id}/reports",
    response_model=CampaignReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_campaign_report(
    campaign_id: UUID,
    data: CampaignReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = CampaignReportService(db)
    return await service.create_report(campaign_id, data, current_user)


@router.get(
    "/{campaign_id}/reports",
    response_model=list[CampaignReportResponse],
)
async def list_campaign_reports(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = CampaignReportService(db)
    return await service.list_reports(campaign_id, current_user)


@router.get(
    "/{campaign_id}/reports/{report_id}",
    response_model=CampaignReportResponse,
)
async def get_campaign_report(
    campaign_id: UUID,
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = CampaignReportService(db)
    return await service.get_report(campaign_id, report_id, current_user)


@router.patch(
    "/{campaign_id}/reports/{report_id}",
    response_model=CampaignReportResponse,
)
async def update_campaign_report(
    campaign_id: UUID,
    report_id: UUID,
    data: CampaignReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = CampaignReportService(db)
    return await service.update_report(campaign_id, report_id, data, current_user)


@router.delete(
    "/{campaign_id}/reports/{report_id}",
)
async def delete_campaign_report(
    campaign_id: UUID,
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = CampaignReportService(db)
    return await service.delete_report(campaign_id, report_id, current_user)
