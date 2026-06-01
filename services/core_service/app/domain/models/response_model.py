import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    TIMESTAMP,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.base import EntityBase


class Response(EntityBase):
    __tablename__ = "responses"

    response_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    survey_id = Column(
        UUID(as_uuid=True),
        ForeignKey("surveys.survey_id", ondelete="CASCADE"),
        nullable=False,
    )

    user_agent = Column(String(255))
    ip_address = Column(String(45))

    started_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
    )

    submitted_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    is_complete = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    answers_count = Column(
        Integer,
        default=0,
        nullable=False,
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ✅ جلوگیری از پاسخ تکراری
    __table_args__ = (
        UniqueConstraint(
            "survey_id",
            "ip_address",
            name="uq_response_survey_ip",
        ),
    )

    # ========================
    # Relationships
    # ========================
    survey = relationship(
        "Survey",
        back_populates="responses",
    )

    text_answers = relationship(
        "AnswerText",
        back_populates="response",
        cascade="all, delete-orphan",
    )
