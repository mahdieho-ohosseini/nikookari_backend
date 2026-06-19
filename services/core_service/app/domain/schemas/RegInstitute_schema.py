from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.domain.models.RegInstitute_model import CharityVerificationStatus


class MediaFileLinkSchema(BaseModel):
    file_id: Optional[int] = None
    metadata_url: Optional[str] = None
    download_url: Optional[str] = None


class CharityVerificationDocumentsSchema(BaseModel):
    articles_of_association: MediaFileLinkSchema
    activity_license: MediaFileLinkSchema
    national_card: MediaFileLinkSchema


class CharityVerificationRequestCreateSchema(BaseModel):
    charity_name: str = Field(..., min_length=2, max_length=255)
    registration_number: str = Field(..., min_length=2, max_length=50)
    establishment_date: date
    activity_field: str = Field(..., min_length=2, max_length=100)
    short_description: str = Field(..., min_length=10)

    phone: str = Field(..., min_length=8, max_length=20)
    email: EmailStr
    website: Optional[str] = Field(default=None, max_length=255)

    province: str = Field(..., min_length=2, max_length=50)
    city: str = Field(..., min_length=2, max_length=100)
    full_address: str = Field(..., min_length=5)

    bank_name: str = Field(..., min_length=2, max_length=100)
    shaba_number: str = Field(..., min_length=24, max_length=26)
    account_owner: str = Field(..., min_length=2, max_length=255)

    articles_of_association_file_id: Optional[int] = None
    activity_license_file_id: Optional[int] = None
    national_card_file_id: Optional[int] = None


class CharityVerificationRequestResponseSchema(BaseModel):
    id: UUID
    user_id: UUID

    charity_name: str
    registration_number: str
    establishment_date: date
    activity_field: str
    short_description: str

    phone: str
    email: EmailStr
    website: Optional[str] = None

    province: str
    city: str
    full_address: str

    bank_name: str
    shaba_number: str
    account_owner: str

    articles_of_association_file_id: Optional[int] = None
    activity_license_file_id: Optional[int] = None
    national_card_file_id: Optional[int] = None

    documents: Optional[CharityVerificationDocumentsSchema] = None

    status: CharityVerificationStatus
    rejection_reason: Optional[str] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CharityVerificationCancelResponseSchema(BaseModel):
    message: str
    deleted_request_id: UUID