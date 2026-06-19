from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class VerifierRequestStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class VerifierDashboardStats(BaseModel):
    total: int = 0
    pending: int = 0
    approved: int = 0
    rejected: int = 0


class VerifierDashboardItem(BaseModel):
    id: UUID
    user_id: UUID
    charity_name: Optional[str] = None
    status: VerifierRequestStatus
    documents_count: int = 0
    checklist_percent: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class VerifierDashboardResponse(BaseModel):
    stats: VerifierDashboardStats
    items: list[VerifierDashboardItem]


class VerifierMediaFileLinkSchema(BaseModel):
    file_id: Optional[int] = None
    metadata_url: Optional[str] = None
    download_url: Optional[str] = None


class VerifierDocumentsSchema(BaseModel):
    articles_of_association: VerifierMediaFileLinkSchema
    activity_license: VerifierMediaFileLinkSchema
    national_card: VerifierMediaFileLinkSchema


class VerifierRequestDetailResponse(BaseModel):
    id: UUID
    user_id: UUID
    status: VerifierRequestStatus

    charity_name: Optional[str] = None
    registration_number: Optional[str] = None
    establishment_date: Optional[date] = None
    activity_field: Optional[str] = None
    short_description: Optional[str] = None

    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None

    province: Optional[str] = None
    city: Optional[str] = None
    full_address: Optional[str] = None

    bank_name: Optional[str] = None
    shaba_number: Optional[str] = None
    account_owner: Optional[str] = None

    articles_of_association_file_id: Optional[int] = None
    activity_license_file_id: Optional[int] = None
    national_card_file_id: Optional[int] = None

    documents: Optional[VerifierDocumentsSchema] = None

    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class VerifierRejectRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=1000)


class VerifierReviewResponse(BaseModel):
    id: UUID
    status: VerifierRequestStatus
    reviewed_by: UUID
    rejection_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)