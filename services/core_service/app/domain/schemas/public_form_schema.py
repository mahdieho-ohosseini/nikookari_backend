from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional, List

# --- Question Schema
class PublicQuestionSchema(BaseModel):
    question_id: UUID
    question_text: str
    description: Optional[str]
    type: str
    is_required: bool
    min_length: int
    max_length: int
    order_index: int

    class Config:
        from_attributes  = True

# --- Setting Schema
class PublicSettingSchema(BaseModel):
    show_progress: bool
    multiple_allow: bool
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    language: str
    show_prev_button: bool
    show_next_button: bool
    auto_advance: bool

    class Config:
        from_attributes  = True

# --- Survey (Form) Schema
class PublicFormSchema(BaseModel):
    title: str
    public_code: str
    settings: Optional[PublicSettingSchema]
    questions: List[PublicQuestionSchema]

    class Config:
        from_attributes  = True
