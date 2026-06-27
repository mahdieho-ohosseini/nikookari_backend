from datetime import datetime
from typing import Optional
from decimal import Decimal

from pydantic import BaseModel, Field, UUID4, ConfigDict, field_validator

from app.domain.models.campaign_model import CampaignStatus, CampaignDonationStatus


class CampaignBase(BaseModel):
    title: str = Field(..., max_length=255, example="Help us build a school")
    description: str = Field(
        ...,
        example="We need funds to build a school for underprivileged children",
    )
    short_description: str = Field(
        ...,
        max_length=500,
        example="Fundraising to build a school for children in need",
    )
    category: str = Field(..., max_length=100, example="Education")
    target_amount: Decimal = Field(..., gt=0, example=1000.0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    cover_image_file_id: Optional[int] = Field(
        default=None,
        example=1,
        description="Media file id for campaign cover image",
    )
    gallery_file_ids: list[int] = Field(
        default_factory=list,
        example=[2, 3],
        description="Media file ids for campaign gallery images",
    )
    attachment_file_ids: list[int] = Field(
        default_factory=list,
        example=[4, 5],
        description="Media file ids for campaign attachments such as PDF documents",
    )

    @field_validator("gallery_file_ids", "attachment_file_ids")
    @classmethod
    def validate_file_ids(cls, value: list[int]) -> list[int]:
        if any(file_id <= 0 for file_id in value):
            raise ValueError("file ids must be positive integers")
        return value


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    target_amount: Optional[Decimal] = Field(None, gt=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    cover_image_file_id: Optional[int] = None
    gallery_file_ids: Optional[list[int]] = None
    attachment_file_ids: Optional[list[int]] = None

    @field_validator("gallery_file_ids", "attachment_file_ids")
    @classmethod
    def validate_optional_file_ids(cls, value: Optional[list[int]]) -> Optional[list[int]]:
        if value is None:
            return value
        if any(file_id <= 0 for file_id in value):
            raise ValueError("file ids must be positive integers")
        return value


class CampaignResponse(CampaignBase):
    id: UUID4
    charity_id: UUID4
    status: CampaignStatus
    collected_amount: Decimal

    reviewed_by: Optional[UUID4] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None

    suspended_by: Optional[UUID4] = None
    suspended_at: Optional[datetime] = None
    suspension_reason: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CampaignDonationCreate(BaseModel):
    campaign_id: UUID4
    donor_id: Optional[UUID4] = None
    amount: Decimal = Field(..., gt=0)
    status: CampaignDonationStatus = CampaignDonationStatus.PENDING


class CampaignDonationResponse(BaseModel):
    id: UUID4
    campaign_id: UUID4
    donor_id: Optional[UUID4] = None
    amount: Decimal
    status: CampaignDonationStatus
    payment_ref: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CampaignActionCreate(BaseModel):
    campaign_id: UUID4
    actor_id: UUID4
    action: str
    reason: Optional[str] = None


class CampaignActionResponse(BaseModel):
    id: UUID4
    campaign_id: UUID4
    actor_id: UUID4
    action: str
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PublicCampaignResponse(BaseModel):
    
    id:UUID4
    title: str
    description: str | None = None
    goal_amount: int | None = None
    current_amount: int | None = None
    status: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
