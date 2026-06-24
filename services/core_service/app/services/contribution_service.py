from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.campaign_model import CampaignDonation, CampaignDonationStatus, CampaignStatus
from app.domain.models.contribution_model import (
    PaymentProvider,
    PaymentTransaction,
    PaymentTransactionStatus,
    SkillContribution,
    SkillContributionStatus,
)
from app.domain.schemas.contribution_schema import DonationCreate, SkillContributionCreate
from app.repository.campaign_repository import campaign_repository
from app.repository.charity_profile_repository import charity_profile_repository
from app.repository.contribution_repository import contribution_repository
from app.services.payment_provider import payment_provider


class ContributionService:
    async def _get_active_campaign(self, db: AsyncSession, campaign_id: UUID):
        campaign = await campaign_repository.get_campaign_by_id(db, campaign_id)
        if campaign is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        if campaign.status != CampaignStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Campaign is not active")
        return campaign

    async def _assert_campaign_owner_or_staff(
        self,
        db: AsyncSession,
        *,
        campaign_id: UUID,
        user_id: UUID,
        role: str,
    ):
        if role.lower() in {"admin", "verifier"}:
            return

        campaign = await campaign_repository.get_campaign_by_id(db, campaign_id)
        if campaign is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

        profile = await charity_profile_repository.get_by_user_id(db, user_id)
        if profile is None or profile.id != campaign.charity_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this campaign")

    async def start_donation(
        self,
        db: AsyncSession,
        *,
        campaign_id: UUID,
        user_id: UUID,
        data: DonationCreate,
        base_url: str,
    ):
        campaign = await self._get_active_campaign(db, campaign_id)

        remaining_amount = Decimal(campaign.target_amount) - Decimal(campaign.collected_amount)
        if remaining_amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Campaign target is already completed")
        if data.amount > remaining_amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Donation amount is greater than remaining campaign target")

        donation = CampaignDonation(
            campaign_id=campaign.id,
            donor_id=user_id,
            amount=data.amount,
            status=CampaignDonationStatus.PENDING,
        )
        donation = await contribution_repository.create_donation(db, donation)

        transaction = PaymentTransaction(
            donation_id=donation.id,
            user_id=user_id,
            campaign_id=campaign.id,
            provider=PaymentProvider.MOCK,
            status=PaymentTransactionStatus.PENDING,
            amount=data.amount,
            authority=f"TEMP-{donation.id}",
        )
        transaction = await contribution_repository.create_transaction(db, transaction)

        callback_url = f"{base_url.rstrip('/')}/api/v1/payments/callback"
        payment = payment_provider.create_payment(
            transaction_id=transaction.id,
            amount=data.amount,
            callback_url=callback_url,
            base_url=base_url,
        )

        transaction.authority = payment.authority
        transaction.payment_url = payment.payment_url
        transaction.callback_url = payment.callback_url
        db.add(transaction)

        await db.commit()
        await db.refresh(donation)
        await db.refresh(transaction)

        return donation, transaction

    async def mark_payment_success(self, db: AsyncSession, *, transaction_id: UUID):
        transaction = await contribution_repository.get_transaction_by_id(db, transaction_id)
        if transaction is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment transaction not found")

        if transaction.status == PaymentTransactionStatus.SUCCESS:
            donation = await contribution_repository.get_donation_by_id(db, transaction.donation_id)
            return donation, transaction

        donation = await contribution_repository.get_donation_by_id(db, transaction.donation_id)
        campaign = await campaign_repository.get_campaign_by_id(db, transaction.campaign_id)
        if donation is None or campaign is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation or campaign not found")

        if donation.status == CampaignDonationStatus.PAID:
            return donation, transaction

        remaining_amount = Decimal(campaign.target_amount) - Decimal(campaign.collected_amount)
        if Decimal(transaction.amount) > remaining_amount:
            transaction.status = PaymentTransactionStatus.FAILED
            transaction.failure_reason = "Donation amount is greater than remaining campaign target"
            donation.status = CampaignDonationStatus.FAILED
            db.add(transaction)
            db.add(donation)
            await db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Donation amount is greater than remaining campaign target")

        ref_id = payment_provider.verify_payment(authority=transaction.authority, amount=Decimal(transaction.amount))

        transaction.status = PaymentTransactionStatus.SUCCESS
        transaction.ref_id = ref_id
        transaction.verified_at = datetime.utcnow()

        donation.status = CampaignDonationStatus.PAID
        donation.payment_ref = ref_id
        donation.paid_at = datetime.utcnow()

        campaign.collected_amount = Decimal(campaign.collected_amount) + Decimal(transaction.amount)

        db.add(transaction)
        db.add(donation)
        db.add(campaign)
        await db.commit()
        await db.refresh(donation)
        await db.refresh(transaction)
        return donation, transaction

    async def mark_payment_failed(self, db: AsyncSession, *, transaction_id: UUID, reason: str = "Payment failed"):
        transaction = await contribution_repository.get_transaction_by_id(db, transaction_id)
        if transaction is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment transaction not found")

        donation = await contribution_repository.get_donation_by_id(db, transaction.donation_id)
        if donation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")

        if transaction.status != PaymentTransactionStatus.SUCCESS:
            transaction.status = PaymentTransactionStatus.FAILED
            transaction.failure_reason = reason
            donation.status = CampaignDonationStatus.FAILED
            db.add(transaction)
            db.add(donation)
            await db.commit()

        await db.refresh(donation)
        await db.refresh(transaction)
        return donation, transaction

    async def verify_callback(self, db: AsyncSession, *, authority: str, callback_status: str):
        transaction = await contribution_repository.get_transaction_by_authority(db, authority)
        if transaction is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment transaction not found")

        if callback_status.lower() in {"ok", "success", "paid"}:
            return await self.mark_payment_success(db, transaction_id=transaction.id)

        return await self.mark_payment_failed(db, transaction_id=transaction.id, reason="Payment callback returned failed status")

    async def list_my_donations(self, db: AsyncSession, *, user_id: UUID):
        return await contribution_repository.list_user_donations(db, user_id)

    async def list_campaign_donations(self, db: AsyncSession, *, campaign_id: UUID, user_id: UUID, role: str):
        await self._assert_campaign_owner_or_staff(db, campaign_id=campaign_id, user_id=user_id, role=role)
        return await contribution_repository.list_campaign_donations(db, campaign_id)

    async def create_skill_contribution(
        self,
        db: AsyncSession,
        *,
        campaign_id: UUID,
        user_id: UUID,
        data: SkillContributionCreate,
    ):
        await self._get_active_campaign(db, campaign_id)

        active_items = await contribution_repository.list_user_skill_contributions(db, user_id)
        active_count = sum(
            1 for item in active_items
            if item.status in {SkillContributionStatus.PENDING, SkillContributionStatus.APPROVED, SkillContributionStatus.NEEDS_INFO}
        )
        if active_count >= 10:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot have more than 10 active skill contributions")

        item = SkillContribution(
            campaign_id=campaign_id,
            user_id=user_id,
            **data.model_dump(),
        )
        item = await contribution_repository.create_skill_contribution(db, item)
        await db.commit()
        await db.refresh(item)
        return item

    async def list_my_skill_contributions(self, db: AsyncSession, *, user_id: UUID):
        return await contribution_repository.list_user_skill_contributions(db, user_id)

    async def list_campaign_skill_contributions(self, db: AsyncSession, *, campaign_id: UUID, user_id: UUID, role: str):
        await self._assert_campaign_owner_or_staff(db, campaign_id=campaign_id, user_id=user_id, role=role)
        return await contribution_repository.list_campaign_skill_contributions(db, campaign_id)

    async def update_skill_status(
        self,
        db: AsyncSession,
        *,
        campaign_id: UUID,
        contribution_id: UUID,
        user_id: UUID,
        role: str,
        next_status: SkillContributionStatus,
        note: str | None = None,
    ):
        item = await contribution_repository.get_skill_contribution_by_id(db, contribution_id)
        if item is None or item.campaign_id != campaign_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill contribution not found")

        if next_status == SkillContributionStatus.CANCELED:
            if item.user_id != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only contribution owner can cancel it")
        else:
            await self._assert_campaign_owner_or_staff(db, campaign_id=campaign_id, user_id=user_id, role=role)

        item.status = next_status
        item.owner_note = note
        item.reviewed_at = datetime.utcnow()
        if next_status == SkillContributionStatus.COMPLETED:
            item.completed_at = datetime.utcnow()

        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item


contribution_service = ContributionService()
