from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.campaign_report_model import CampaignReport


class CampaignReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, report: CampaignReport) -> CampaignReport:
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def get_by_id(self, report_id: UUID) -> CampaignReport | None:
        result = await self.db.execute(
            select(CampaignReport).where(CampaignReport.id == report_id)
        )
        return result.scalar_one_or_none()

    async def list_by_campaign(self, campaign_id: UUID, public_only: bool = False):
        stmt = select(CampaignReport).where(CampaignReport.campaign_id == campaign_id)

        if public_only:
            stmt = stmt.where(CampaignReport.is_public == True)

        stmt = stmt.order_by(CampaignReport.created_at.desc())

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update(self, report: CampaignReport, update_data: dict) -> CampaignReport:
        for key, value in update_data.items():
            setattr(report, key, value)

        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def delete(self, report: CampaignReport) -> None:
        await self.db.delete(report)
        await self.db.commit()