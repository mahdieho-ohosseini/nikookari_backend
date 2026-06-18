from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
    institute_name: Optional[str] = None
    status: VerifierRequestStatus
    documents_count: int = 0
    checklist_percent: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class VerifierDashboardResponse(BaseModel):
    stats: VerifierDashboardStats
    items: list[VerifierDashboardItem]


class VerifierRequestDetailResponse(BaseModel):
    id: UUID
    user_id: UUID
    status: VerifierRequestStatus

    institute_name: Optional[str] = None
    registration_number: Optional[str] = None

    phone: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None

    reviewed_by: Optional[UUID] = None
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
