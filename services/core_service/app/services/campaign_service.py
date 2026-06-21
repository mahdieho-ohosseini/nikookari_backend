from uuid import UUID
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.campaign_model import (
    Campaign,
    CampaignAction,
    CampaignActionType,
    CampaignStatus,
)
from app.domain.models.RegInstitute_model import CharityProfileStatus
from app.domain.schemas.campaign_schema import CampaignCreate, CampaignUpdate
from app.repository.campaign_repository import campaign_repository
from app.repository.charity_profile_repository import charity_profile_repository


def now_naive_utc() -> datetime:
    """
    Returns current UTC datetime without timezone info.
    مناسب برای ستون‌های DateTime بدون timezone در دیتابیس.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(value: datetime | None) -> datetime | None:
    """
    Converts timezone-aware datetime to naive UTC datetime.
    If datetime is already naive, returns it unchanged.
    """
    if value is None:
        return None

    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    return value


class CampaignService:
    async def create_campaign(
        self,
        db: AsyncSession,
        data: CampaignCreate,
        user_id: UUID,
    ) -> Campaign:
        charity_profile = await charity_profile_repository.get_by_user_id(
            db,
            user_id,
        )

        if charity_profile is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No charity profile found for current user",
            )

        if charity_profile.status != CharityProfileStatus.active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Charity profile is not active",
            )

        payload = data.model_dump()

        payload["start_date"] = to_naive_utc(payload.get("start_date"))
        payload["end_date"] = to_naive_utc(payload.get("end_date"))

        if (
            payload.get("start_date") is not None
            and payload.get("end_date") is not None
            and payload["end_date"] < payload["start_date"]
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_date cannot be earlier than start_date",
            )

        campaign = Campaign(
            **payload,
            charity_id=charity_profile.id,
            status=CampaignStatus.PENDING_REVIEW,
        )

        campaign.actions.append(
            CampaignAction(
                actor_id=user_id,
                action=CampaignActionType.SUBMITTED,
                reason="Campaign submitted for review",
            )
        )

        created = await campaign_repository.create_campaign(db, campaign)
        await db.commit()
        await db.refresh(created)
        return created

    async def get_campaign(
        self,
        db: AsyncSession,
        campaign_id: UUID,
    ) -> Campaign:
        campaign = await campaign_repository.get_campaign_by_id(
            db,
            campaign_id,
        )

        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )

        return campaign

    async def get_campaigns(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        charity_id: UUID | None = None,
    ):
        return await campaign_repository.get_campaigns(
            db,
            skip=skip,
            limit=limit,
            charity_id=charity_id,
        )

    async def update_campaign(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        data: CampaignUpdate,
        user_id: UUID,
    ) -> Campaign:
        campaign = await campaign_repository.get_campaign_by_id(
            db,
            campaign_id,
        )

        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )

        if not await self._is_owner(
            db=db,
            charity_id=campaign.charity_id,
            user_id=user_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to update this campaign",
            )

        if campaign.status not in [
            CampaignStatus.DRAFT,
            CampaignStatus.PENDING_REVIEW,
            CampaignStatus.REJECTED,
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Campaign can only be updated when status is "
                    "DRAFT, PENDING_REVIEW or REJECTED"
                ),
            )

        campaign_data = data.model_dump(exclude_unset=True)

        if "start_date" in campaign_data:
            campaign_data["start_date"] = to_naive_utc(
                campaign_data["start_date"]
            )

        if "end_date" in campaign_data:
            campaign_data["end_date"] = to_naive_utc(
                campaign_data["end_date"]
            )

        next_start = campaign_data.get("start_date", campaign.start_date)
        next_end = campaign_data.get("end_date", campaign.end_date)

        if next_start and next_end and next_end < next_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_date cannot be earlier than start_date",
            )

        protected_fields = {
            "id",
            "charity_id",
            "status",
            "reviewed_by",
            "reviewed_at",
            "review_note",
            "suspended_by",
            "suspended_at",
            "suspension_reason",
            "actions",
        }

        for key, value in campaign_data.items():
            if key in protected_fields:
                continue

            setattr(campaign, key, value)

        updated = await campaign_repository.update_campaign(db, campaign)
        await db.commit()
        await db.refresh(updated)
        return updated

    async def delete_campaign(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        user_id: UUID,
    ) -> None:
        campaign = await campaign_repository.get_campaign_by_id(
            db,
            campaign_id,
        )

        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )

        if not await self._is_owner(
            db=db,
            charity_id=campaign.charity_id,
            user_id=user_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to delete this campaign",
            )

        await campaign_repository.delete_campaign(db, campaign)
        await db.commit()

    async def submit_campaign(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        actor_id: UUID,
    ) -> Campaign:
        campaign = await campaign_repository.get_campaign_by_id(
            db,
            campaign_id,
        )

        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )

        if not await self._is_owner(
            db=db,
            charity_id=campaign.charity_id,
            user_id=actor_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )

        if campaign.status != CampaignStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign can only be submitted when status is DRAFT",
            )

        campaign.status = CampaignStatus.PENDING_REVIEW
        campaign.reviewed_by = None
        campaign.reviewed_at = None
        campaign.review_note = None

        campaign.actions.append(
            CampaignAction(
                actor_id=actor_id,
                action=CampaignActionType.SUBMITTED,
                reason="Campaign submitted for review",
            )
        )

        updated = await campaign_repository.update_campaign(db, campaign)
        await db.commit()
        await db.refresh(updated)
        return updated

    async def approve_campaign(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        actor_id: UUID,
        review_note: str | None = None,
    ) -> Campaign:
        campaign = await campaign_repository.get_campaign_by_id(
            db,
            campaign_id,
        )

        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )

        if campaign.status != CampaignStatus.PENDING_REVIEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Campaign can only be approved when status is "
                    "PENDING_REVIEW"
                ),
            )

        campaign.status = CampaignStatus.ACTIVE
        campaign.reviewed_by = actor_id
        campaign.reviewed_at = now_naive_utc()
        campaign.review_note = review_note or "Campaign approved"

        campaign.suspended_by = None
        campaign.suspended_at = None
        campaign.suspension_reason = None

        campaign.actions.append(
            CampaignAction(
                actor_id=actor_id,
                action=CampaignActionType.APPROVED,
                reason=review_note or "Campaign approved",
            )
        )

        updated = await campaign_repository.update_campaign(db, campaign)
        await db.commit()
        await db.refresh(updated)
        return updated

    async def reject_campaign(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        actor_id: UUID,
        review_note: str | None = None,
    ) -> Campaign:
        campaign = await campaign_repository.get_campaign_by_id(
            db,
            campaign_id,
        )

        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )

        if campaign.status != CampaignStatus.PENDING_REVIEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Campaign can only be rejected when status is "
                    "PENDING_REVIEW"
                ),
            )

        campaign.status = CampaignStatus.REJECTED
        campaign.reviewed_by = actor_id
        campaign.reviewed_at = now_naive_utc()
        campaign.review_note = review_note or "Campaign rejected"

        campaign.actions.append(
            CampaignAction(
                actor_id=actor_id,
                action=CampaignActionType.REJECTED,
                reason=review_note or "Campaign rejected",
            )
        )

        updated = await campaign_repository.update_campaign(db, campaign)
        await db.commit()
        await db.refresh(updated)
        return updated

    async def suspend_campaign(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        actor_id: UUID,
        suspension_reason: str | None = None,
    ) -> Campaign:
        campaign = await campaign_repository.get_campaign_by_id(
            db,
            campaign_id,
        )

        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )

        if campaign.status not in [
            CampaignStatus.ACTIVE,
            CampaignStatus.PENDING_REVIEW,
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Campaign can only be suspended when status is "
                    "ACTIVE or PENDING_REVIEW"
                ),
            )

        campaign.status = CampaignStatus.SUSPENDED
        campaign.suspended_by = actor_id
        campaign.suspended_at = now_naive_utc()
        campaign.suspension_reason = (
            suspension_reason or "Campaign suspended"
        )

        campaign.actions.append(
            CampaignAction(
                actor_id=actor_id,
                action=CampaignActionType.SUSPENDED,
                reason=suspension_reason or "Campaign suspended",
            )
        )

        updated = await campaign_repository.update_campaign(db, campaign)
        await db.commit()
        await db.refresh(updated)
        return updated

    async def resume_campaign(
        self,
        db: AsyncSession,
        campaign_id: UUID,
        actor_id: UUID,
    ) -> Campaign:
        campaign = await campaign_repository.get_campaign_by_id(
            db,
            campaign_id,
        )

        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )

        if campaign.status != CampaignStatus.SUSPENDED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign can only be resumed when status is SUSPENDED",
            )

        campaign.status = CampaignStatus.ACTIVE
        campaign.suspended_by = None
        campaign.suspended_at = None
        campaign.suspension_reason = None

        campaign.actions.append(
            CampaignAction(
                actor_id=actor_id,
                action=CampaignActionType.RESUMED,
                reason="Campaign resumed",
            )
        )

        updated = await campaign_repository.update_campaign(db, campaign)
        await db.commit()
        await db.refresh(updated)
        return updated

    async def _is_owner(
        self,
        db: AsyncSession,
        charity_id: UUID,
        user_id: UUID,
    ) -> bool:
        charity_profile = await charity_profile_repository.get_by_user_id(
            db,
            user_id,
        )

        return charity_profile is not None and charity_profile.id == charity_id


campaign_service = CampaignService()
