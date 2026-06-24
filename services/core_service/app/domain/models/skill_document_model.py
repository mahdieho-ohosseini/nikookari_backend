import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import EntityBase


class SkillDocumentType(str, enum.Enum):
    CERTIFICATE = "certificate"
    RESUME = "resume"
    PORTFOLIO = "portfolio"
    LICENSE = "license"
    IDENTITY = "identity"
    OTHER = "other"


class SkillDocumentStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class SkillDocument(EntityBase):
    __tablename__ = "skill_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    skill_contribution_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(String(50), nullable=False)

    file_id = Column(Integer, nullable=False)
    is_public = Column(Boolean, nullable=False, default=False)

    status = Column(String(50), nullable=False, default=SkillDocumentStatus.PENDING.value)
    review_note = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)