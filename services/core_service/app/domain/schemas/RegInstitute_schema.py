from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.domain.models.RegInstitute_model import CharityVerificationStatus
from pydantic import BaseModel, EmailStr, Field



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

    articles_of_association_url: Optional[str] = None
    activity_license_url: Optional[str] = None
    national_card_url: Optional[str] = None


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

    articles_of_association_url: Optional[str] = None
    activity_license_url: Optional[str] = None
    national_card_url: Optional[str] = None

    status: CharityVerificationStatus
    rejection_reason: Optional[str] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


