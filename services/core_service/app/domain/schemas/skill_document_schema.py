from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.models.skill_document_model import SkillDocumentType


class SkillDocumentCreate(BaseModel):
    skill_contribution_id: Optional[UUID] = None
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    document_type: SkillDocumentType = SkillDocumentType.OTHER
    file_id: int = Field(..., gt=0)
    is_public: bool = False


class SkillDocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    document_type: Optional[SkillDocumentType] = None
    file_id: Optional[int] = Field(None, gt=0)
    is_public: Optional[bool] = None


class SkillDocumentReview(BaseModel):
    status: str = Field(..., pattern="^(verified|rejected)$")
    review_note: Optional[str] = None


class SkillDocumentResponse(BaseModel):
    id: UUID
    user_id: UUID
    skill_contribution_id: Optional[UUID] = None

    title: str
    description: Optional[str] = None
    document_type: str
    file_id: int
    is_public: bool

    status: str
    review_note: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)