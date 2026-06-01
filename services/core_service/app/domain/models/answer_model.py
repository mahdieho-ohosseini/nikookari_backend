import uuid
from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.base import EntityBase


class AnswerText(EntityBase):
    __tablename__ = "answers_text"

    answer_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    response_id = Column(
        UUID(as_uuid=True),
        ForeignKey("responses.response_id", ondelete="CASCADE"),
        nullable=False,
    )

    question_id = Column(
        UUID(as_uuid=True),
        ForeignKey("questions.question_id", ondelete="CASCADE"),
        nullable=False,
    )

    text_value = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # ========================
    # Relationships
    # ========================
    response = relationship(
        "Response",
        back_populates="text_answers",
    )

    question = relationship(
        "Question",
    )
