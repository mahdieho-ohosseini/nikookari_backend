from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from sqlalchemy.orm import Session

class SettingBase(BaseModel):
    show_progress: bool = True
    multiple_allow: bool = False

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    language: str = "fa"

    show_prev_button: bool = True
    show_next_button: bool = True
    auto_advance: bool = False
    is_active :bool =False


class SettingUpdateSchema(SettingBase):
    """
    PATCH schema
    """
    pass


class SettingResponseSchema(SettingBase):
    setting_id: UUID
    survey_id: UUID

    class Config:
        from_attributes = True
class InstituteBase(BaseModel):
    institute_name: str
    registration_number: str
    establishment_date: date
    activity_field: str
    short_description: str
    contact_phone: str
    email: EmailStr
    website: Optional[str] = None
    province: str
    city: str
    full_address: str
    bank_name: str
    shaba_number: str
    account_owner: str

class InstituteRead(InstituteBase):
    user_id: int
    status: str
    
    class Config:
        from_attributes = True

class InstituteResponse(BaseModel):
    user_id: UUID
    institute_name: str
    status: str
    created_at: Optional[date] = None

    class Config:
        from_attributes = True