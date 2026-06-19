from datetime import date, datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.RegInstitute_model import CharityProfileStatus


class CharityProfileBase(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=255)
    logo_file_id: Optional[int] = None
    cover_file_id: Optional[int] = None
    short_description: Optional[str] = None
    about_text: Optional[str] = None
    vision_text: Optional[str] = None
    website: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=30)
    province: Optional[str] = Field(default=None, max_length=50)
    city: Optional[str] = Field(default=None, max_length=100)
    full_address: Optional[str] = None
    social_links: Optional[Dict[str, Any]] = None


class CharityProfileUpdate(BaseModel):
    # User-editable public fields
    charity_name: Optional[str] = Field(default=None, max_length=255)
    logo_file_id: Optional[int] = None
    cover_file_id: Optional[int] = None
    short_description: Optional[str] = None
    about_text: Optional[str] = None
    vision_text: Optional[str] = None
    website: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=30)
    province: Optional[str] = Field(default=None, max_length=50)
    city: Optional[str] = Field(default=None, max_length=100)
    full_address: Optional[str] = None
    social_links: Optional[Dict[str, Any]] = None


class CharityProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    verification_request_id: UUID

    charity_name: str
    slug: str

    registration_number: str
    establishment_date: Optional[date] = None
    activity_field: Optional[str] = None

    phone: str
    email: str
    website: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    full_address: Optional[str] = None

    shaba_number: Optional[str] = None
    bank_name: Optional[str] = None
    account_name: Optional[str] = None

    logo_file_id: Optional[int] = None
    cover_file_id: Optional[int] = None

    short_description: Optional[str] = None
    about_text: Optional[str] = None
    vision_text: Optional[str] = None

    social_links: Optional[Dict[str, Any]] = None

    status: CharityProfileStatus
    is_published: bool
    published_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime


class MyCharityProfileResponse(BaseModel):
    has_profile: bool
    profile: Optional[CharityProfileResponse] = None


class CharityProfileSubmitResponse(BaseModel):
    id: UUID
    status: CharityProfileStatus
    message: str
