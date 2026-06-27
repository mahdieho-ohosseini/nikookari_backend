from uuid import UUID
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.campaign_model import Campaign, CampaignStatus


class CampaignRepository:
    async def get_campaign_by_id(
        self,
        db: AsyncSession,
        campaign_id: UUID,
    ) -> Campaign | None:
        stmt = select(Campaign).where(Campaign.id == campaign_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_campaigns(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        charity_id: UUID | None = None,
    ) -> Sequence[Campaign]:
        stmt = select(Campaign)

        if charity_id is not None:
            stmt = stmt.where(Campaign.charity_id == charity_id)

        stmt = stmt.offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()

    async def create_campaign(
        self,
        db: AsyncSession,
        campaign: Campaign,
    ) -> Campaign:
        db.add(campaign)
        await db.flush()
        await db.refresh(campaign)
        return campaign

    async def update_campaign(
        self,
        db: AsyncSession,
        campaign: Campaign,
    ) -> Campaign:
        db.add(campaign)
        await db.flush()
        await db.refresh(campaign)
        return campaign

    async def delete_campaign(
        self,
        db: AsyncSession,
        campaign: Campaign,
    ) -> None:
        await db.delete(campaign)
        await db.flush()

    async def get_campaigns_for_verifier(
        self,
        db: AsyncSession,
        *,
        status: CampaignStatus | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Campaign]:
        stmt = select(Campaign).order_by(Campaign.created_at.desc())

        if status is not None:
            stmt = stmt.where(Campaign.status == status)

        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Campaign.title.ilike(search_pattern),
                    Campaign.description.ilike(search_pattern),
                )
            )

        stmt = stmt.offset(offset).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_public_campaigns(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 10,
    ):
        stmt = (
            select(Campaign)
            .where(Campaign.status == CampaignStatus.ACTIVE)
            .offset(skip)
            .limit(limit)
            .order_by(Campaign.created_at.desc())
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_public_campaign_by_id(
        self,
        db: AsyncSession,
        campaign_id: UUID,
    ):
        stmt = select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.status == CampaignStatus.ACTIVE,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    


campaign_repository = CampaignRepository()
