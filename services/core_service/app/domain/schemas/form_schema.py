from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

# ورودی (از Modal فرانت)
class CreateFormRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=100, description="نام فرم")

# خروجی (پاسخ به فرانت)
class CreateFormResponse(BaseModel):
    survey_id: UUID
    title: str
    slug: str
    is_public: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

#پاسخ به دریافت  فرم های کاربر
class SeeFormsResponseSchema(BaseModel):
    survey_id: UUID
    title: str
    created_at: datetime

    class Config:
        from_attributes = True



class UpdateFormNameSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)



class DeletedFormItemSchema(BaseModel):
    survey_id: UUID
    title: str
    deleted_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class DeletedFormListResponse(BaseModel):
    items: list[DeletedFormItemSchema]




class SoftDeleteFormActionResponse(BaseModel):
    success: bool = True
    message: str
    survey_id: UUID
