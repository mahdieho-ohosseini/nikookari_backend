from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, UUID4

from app.domain.models.campaign_model import CampaignDonationStatus
from app.domain.models.contribution_model import (
    CollaborationType,
    PaymentProvider,
    PaymentTransactionStatus,
    SkillCategory,
    SkillContributionStatus,
)


class DonationCreate(BaseModel):
    amount: Decimal = Field(..., ge=10000, le=100000000, description="Donation amount in Toman/Rial based on project convention")


class DonationPaymentResponse(BaseModel):
    donation_id: UUID4
    transaction_id: UUID4
    campaign_id: UUID4
    amount: Decimal
    donation_status: CampaignDonationStatus
    payment_status: PaymentTransactionStatus
    provider: PaymentProvider
    authority: str
    payment_url: str
    callback_url: Optional[str] = None
    message: str


class DonationResponse(BaseModel):
    id: UUID4
    title :str
    campaign_id: UUID4
    charity_name: Optional[str] = None
    donor_id: Optional[UUID4] = None
    amount: Decimal
    status: CampaignDonationStatus
    payment_ref: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentTransactionResponse(BaseModel):
    id: UUID4
    donation_id: UUID4
    user_id: UUID4
    campaign_id: UUID4
    provider: PaymentProvider
    status: PaymentTransactionStatus
    amount: Decimal
    authority: str
    ref_id: Optional[str] = None
    payment_url: Optional[str] = None
    callback_url: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentResultResponse(BaseModel):
    status: PaymentTransactionStatus
    donation_id: UUID4
    transaction_id: UUID4
    campaign_id: UUID4
    amount: Decimal
    ref_id: Optional[str] = None
    message: str


class SkillContributionCreate(BaseModel):
    skill_category: SkillCategory
    skill_title: str = Field(..., min_length=2, max_length=150)
    description: str = Field(..., min_length=50)
    availability: str = Field(..., min_length=2)
    collaboration_type: CollaborationType
    contact_phone: Optional[str] = Field(None, max_length=20)
    document_file_id: Optional[str] = Field(None, max_length=100)


class SkillContributionResponse(BaseModel):
    id: UUID4
    campaign_id: UUID4
    user_id: UUID4
    skill_category: SkillCategory
    skill_title: str
    description: str
    availability: str
    collaboration_type: CollaborationType
    contact_phone: Optional[str] = None
    document_file_id: Optional[str] = None
    status: SkillContributionStatus
    owner_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    reviewed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SkillContributionDecision(BaseModel):
    note: Optional[str] = Field(None, max_length=1000)
