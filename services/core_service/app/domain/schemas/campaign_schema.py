from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, UUID4, ConfigDict
from decimal import Decimal

from app.domain.models.campaign_model import CampaignStatus, CampaignDonationStatus


class CampaignBase(BaseModel):
    title: str = Field(..., max_length=255, example="Help us build a school")
    description: str = Field(
        ...,
        example="We need funds to build a school for underprivileged children",
    )
    # فیلد گمشده که باعث خطا می‌شد:
    short_description: str = Field(
        ..., 
        max_length=500, 
        example="Fundraising to build a school for children in need"
    )
    category: str = Field(..., max_length=100, example="Education")
    target_amount: Decimal = Field(..., gt=0, example=1000.0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


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


class CampaignResponse(CampaignBase):
    id: UUID4
    charity_id: UUID4
    status: CampaignStatus
    collected_amount: Decimal
    
    # فیلدهای واقعی مربوط به بررسی (جایگزین review و suspension قدیمی)
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
    action: str  # این باید با CampaignActionType هماهنگ باشد
    reason: Optional[str] = None


class CampaignActionResponse(BaseModel):
    id: UUID4
    campaign_id: UUID4
    actor_id: UUID4
    action: str
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
