from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.campaign_model import Campaign
from app.domain.models.RegInstitute_model import CharityProfile
from app.domain.models.campaign_report_model import CampaignReport
from app.domain.schemas.campaign_report_schema import (
    CampaignReportCreate,
    CampaignReportUpdate,
)
from app.repository.campaign_report_repository import CampaignReportRepository


class CampaignReportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = CampaignReportRepository(db)

    async def _get_campaign(self, campaign_id: UUID) -> Campaign:
        result = await self.db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )

        return campaign

    async def _can_manage_campaign(self, campaign: Campaign, user: dict) -> bool:
        role = user.get("role")
        user_id = user.get("user_id") or user.get("sub")

        if role in ["admin", "verifier"]:
            return True

        result = await self.db.execute(
            select(CharityProfile).where(CharityProfile.id == campaign.charity_id)
        )
        charity = result.scalar_one_or_none()

        if charity and str(charity.user_id) == str(user_id):
            return True

        return False

    async def create_report(
        self,
        campaign_id: UUID,
        data: CampaignReportCreate,
        current_user: dict,
    ) -> CampaignReport:
        campaign = await self._get_campaign(campaign_id)

        if not await self._can_manage_campaign(campaign, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to create report for this campaign",
            )

        user_id = current_user.get("user_id") or current_user.get("sub")

        report = CampaignReport(
            campaign_id=campaign_id,
            author_id=UUID(str(user_id)),
            **data.model_dump(),
        )

        return await self.repository.create(report)

    async def list_reports(
        self,
        campaign_id: UUID,
        current_user: dict | None = None,
    ):
        campaign = await self._get_campaign(campaign_id)

        can_manage = False
        if current_user:
            can_manage = await self._can_manage_campaign(campaign, current_user)

        return await self.repository.list_by_campaign(
            campaign_id=campaign_id,
            public_only=not can_manage,
        )

    async def get_report(
        self,
        campaign_id: UUID,
        report_id: UUID,
        current_user: dict | None = None,
    ) -> CampaignReport:
        campaign = await self._get_campaign(campaign_id)
        report = await self.repository.get_by_id(report_id)

        if not report or report.campaign_id != campaign_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign report not found",
            )

        can_manage = False
        if current_user:
            can_manage = await self._can_manage_campaign(campaign, current_user)

        if not report.is_public and not can_manage:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This report is not public",
            )

        return report

    async def update_report(
        self,
        campaign_id: UUID,
        report_id: UUID,
        data: CampaignReportUpdate,
        current_user: dict,
    ) -> CampaignReport:
        campaign = await self._get_campaign(campaign_id)

        if not await self._can_manage_campaign(campaign, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to update this report",
            )

        report = await self.repository.get_by_id(report_id)

        if not report or report.campaign_id != campaign_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign report not found",
            )

        update_data = data.model_dump(exclude_unset=True)
        return await self.repository.update(report, update_data)

    async def delete_report(
        self,
        campaign_id: UUID,
        report_id: UUID,
        current_user: dict,
    ) -> dict:
        campaign = await self._get_campaign(campaign_id)

        if not await self._can_manage_campaign(campaign, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to delete this report",
            )

        report = await self.repository.get_by_id(report_id)

        if not report or report.campaign_id != campaign_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign report not found",
            )

        await self.repository.delete(report)

        return {
            "status": "success",
            "message": "Campaign report deleted successfully",
        }