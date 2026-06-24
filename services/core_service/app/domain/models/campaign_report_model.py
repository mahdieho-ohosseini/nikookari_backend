import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import EntityBase


class CampaignReportType(str, enum.Enum):
    PROGRESS = "progress"
    FINANCIAL = "financial"
    FINAL = "final"
    INVOICE = "invoice"
    GENERAL = "general"


class CampaignReport(EntityBase):
    __tablename__ = "campaign_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    report_type = Column(String(50), nullable=False, default=CampaignReportType.GENERAL.value)

    image_file_ids = Column(JSONB, nullable=False, default=list, server_default="[]")
    attachment_file_ids = Column(JSONB, nullable=False, default=list, server_default="[]")

    is_public = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )