# app/domain/models/notification_model.py

import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.base import EntityBase
import enum


class NotificationType(str, enum.Enum):
    CHARITY_VERIFICATION_APPROVED = "charity_verification_approved"
    CHARITY_VERIFICATION_REJECTED = "charity_verification_rejected"
    CHARITY_PROFILE_PENDING_REVIEW = "charity_profile_pending_review"
    CHARITY_PROFILE_APPROVED = "charity_profile_approved"


class Notification(EntityBase):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    type = Column(String(100), nullable=False)

    is_read = Column(Boolean, nullable=False, default=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
