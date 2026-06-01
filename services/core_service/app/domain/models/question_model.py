from sqlalchemy import Column, String, Boolean, Integer, Text, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.core.base import EntityBase
import uuid
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class Question(EntityBase):
    __tablename__ = "questions"

    question_id = Column(UUID(as_uuid=True), primary_key=True,index=True, default=uuid.uuid4)
    survey_id = Column(UUID(as_uuid=True), ForeignKey("surveys.survey_id", ondelete="CASCADE"), nullable=False)

    type = Column(String(50), nullable=False, default="text")
    question_text = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    min_length = Column(Integer, default=0)
    max_length = Column(Integer, default=255)

    is_required = Column(Boolean, default=True)
    order_index = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


    survey = relationship(
        "Survey",
        back_populates="questions"  # ← همنام با relationship در Survey
    )


    __table_args__ = (
        UniqueConstraint(
            "survey_id",
            "question_text",
            name="uq_survey_text_question"
        ),
    )