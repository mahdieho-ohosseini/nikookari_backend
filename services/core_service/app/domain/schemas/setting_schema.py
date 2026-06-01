from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


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
