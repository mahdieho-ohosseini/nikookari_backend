from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.domain.models.campaign_model import Campaign, CampaignDonation
from app.domain.models.contribution_model import PaymentTransaction, SkillContribution


class ContributionRepository:
    async def create_donation(self, db: AsyncSession, donation: CampaignDonation) -> CampaignDonation:
        db.add(donation)
        await db.flush()
        await db.refresh(donation)
        return donation

    async def create_transaction(self, db: AsyncSession, transaction: PaymentTransaction) -> PaymentTransaction:
        db.add(transaction)
        await db.flush()
        await db.refresh(transaction)
        return transaction

    async def get_transaction_by_id(self, db: AsyncSession, transaction_id: UUID) -> PaymentTransaction | None:
        result = await db.execute(
            select(PaymentTransaction).where(PaymentTransaction.id == transaction_id)
        )
        return result.scalar_one_or_none()

    async def get_transaction_by_authority(self, db: AsyncSession, authority: str) -> PaymentTransaction | None:
        result = await db.execute(
            select(PaymentTransaction).where(PaymentTransaction.authority == authority)
        )
        return result.scalar_one_or_none()

    async def get_donation_by_id(self, db: AsyncSession, donation_id: UUID) -> CampaignDonation | None:
        result = await db.execute(
            select(CampaignDonation).where(CampaignDonation.id == donation_id)
        )
        return result.scalar_one_or_none()

    async def list_user_donations(self, db: AsyncSession, user_id: UUID) -> Sequence[CampaignDonation]:
        result = await db.execute(
             select(CampaignDonation)
            .options(
            # اینجا داریم زنجیره‌ای Join می‌زنیم: Donation -> Campaign -> Institute
            joinedload(CampaignDonation.campaign)
            .joinedload(Campaign.institute) 
           )
        .where(CampaignDonation.donor_id == user_id)
        .order_by(CampaignDonation.created_at.desc())
          )
        return result.scalars().all()

    async def list_campaign_donations(self, db: AsyncSession, campaign_id: UUID) -> Sequence[CampaignDonation]:
        result = await db.execute(
            select(CampaignDonation)
            .where(CampaignDonation.campaign_id == campaign_id)
            .order_by(CampaignDonation.created_at.desc())
        )
        return result.scalars().all()

    async def create_skill_contribution(self, db: AsyncSession, item: SkillContribution) -> SkillContribution:
        db.add(item)
        await db.flush()
        await db.refresh(item)
        return item

    async def get_skill_contribution_by_id(self, db: AsyncSession, item_id: UUID) -> SkillContribution | None:
        result = await db.execute(
            select(SkillContribution).where(SkillContribution.id == item_id)
        )
        return result.scalar_one_or_none()

    async def list_user_skill_contributions(self, db: AsyncSession, user_id: UUID) -> Sequence[SkillContribution]:
        result = await db.execute(
            select(SkillContribution)
            .where(SkillContribution.user_id == user_id)
            .order_by(SkillContribution.created_at.desc())
        )
        return result.scalars().all()

    async def list_campaign_skill_contributions(self, db: AsyncSession, campaign_id: UUID) -> Sequence[SkillContribution]:
        result = await db.execute(
            select(SkillContribution)
            .where(SkillContribution.campaign_id == campaign_id)
            .order_by(SkillContribution.created_at.desc())
        )
        return result.scalars().all()


contribution_repository = ContributionRepository()
