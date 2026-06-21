import enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import EntityBase


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"                    # هنوز آماده نشده
    PENDING_REVIEW = "pending_review"  # منتظر بررسی
    ACTIVE = "active"                  # فعال و قابل کمک
    REJECTED = "rejected"              # رد شده
    SUSPENDED = "suspended"            # موقتاً متوقف شده


class CampaignDonationStatus(str, enum.Enum):
    PENDING = "pending"                 #پرداخت شروع شده ولی هنوز نهایی نشده
    PAID = "paid"                       #پرداخت موفق بوده
    FAILED = "failed"                   #پرداخت ناموفق بوده.


class CampaignActionType(str, enum.Enum):
    SUBMITTED = "submitted"             #کمپین برای بررسی ارسال شده.
    APPROVED = "approved"               #کمپین تایید شده
    REJECTED = "rejected"               #کمپین رد شده.
    SUSPENDED = "suspended"             #کمپین متوقف شده.
    RESUMED = "resumed"                 # کمپین دوباره فعال شده.


class Campaign(EntityBase):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    charity_id = Column(UUID(as_uuid=True),ForeignKey("charity_profiles.id"), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    short_description = Column(String(500), nullable=False)

    category = Column(String(100), nullable=False, index=True)
    target_amount = Column(Numeric(18, 2), nullable=False)
    collected_amount = Column(Numeric(18, 2), nullable=False, default=0)

    status = Column(
        Enum(CampaignStatus),
        nullable=False,
        default=CampaignStatus.DRAFT,
        index=True,
    )

    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_note = Column(Text, nullable=True)

    suspended_by = Column(UUID(as_uuid=True), nullable=True)
    suspended_at = Column(DateTime, nullable=True)
    suspension_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    donations = relationship(
        "CampaignDonation",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )

    actions = relationship(
        "CampaignAction",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )
    charity = relationship("CharityProfile", back_populates="campaigns")



class CampaignDonation(EntityBase):
    __tablename__ = "campaign_donations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id"),
        nullable=False,
        index=True,
    )
    donor_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    amount = Column(Numeric(18, 2), nullable=False)
    status = Column(
        Enum(CampaignDonationStatus),
        nullable=False,
        default=CampaignDonationStatus.PENDING,
        index=True,
    )

    payment_ref = Column(String(255), nullable=True, index=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="donations")


class CampaignAction(EntityBase):
    __tablename__ = "campaign_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    campaign_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id"),
        nullable=False,
        index=True,
    )
    actor_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    action = Column(Enum(CampaignActionType), nullable=False)
    reason = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="actions")
