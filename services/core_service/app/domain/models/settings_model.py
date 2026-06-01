import uuid
from sqlalchemy import (
    Column, String, Boolean, TIMESTAMP, Integer,
    ForeignKey, func, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import EntityBase  # فرض می‌کنیم ORM Base جای درستی ایمپورت شده

class Setting(EntityBase):
    __tablename__ = "settings"

    setting_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        unique=True,
        index=True
    )

    survey_id = Column(
        UUID(as_uuid=True),
        ForeignKey("surveys.survey_id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    show_progress = Column(Boolean, default=True)
    multiple_allow = Column(Boolean, default=False)
    start_date = Column(TIMESTAMP(timezone=True), nullable=True)
    end_date = Column(TIMESTAMP(timezone=True), nullable=True)
    language = Column(String(10), default="fa")
    show_prev_button = Column(Boolean, default=True)
    show_next_button = Column(Boolean, default=True)
    auto_advance = Column(Boolean, default=False)

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        onupdate=func.now()
    )
    is_active = Column(Boolean, nullable=False,server_default=text("false"))



    # Optional: ارتباط با مدل Survey
    survey = relationship("Survey", back_populates="settings", uselist=False)

    def __repr__(self):
        return (
            f"<Setting(setting_id={self.setting_id}, survey_id={self.survey_id}, "
            f"show_progress={self.show_progress}, multiple_allow={self.multiple_allow}, "
            f"start_date={self.start_date}, end_date={self.end_date}, language={self.language})>"
        )
