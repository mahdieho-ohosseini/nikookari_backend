import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import EntityBase


class PaymentProvider(str, enum.Enum):
    MOCK = "mock"
    ZARINPAL = "zarinpal"


class PaymentTransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"


class SkillContributionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_INFO = "needs_info"
    COMPLETED = "completed"
    CANCELED = "canceled"


class SkillCategory(str, enum.Enum):
    MEDICAL = "medical"
    EDUCATION = "education"
    TECHNICAL_ENGINEERING = "technical_engineering"
    LEGAL_FINANCIAL = "legal_financial"
    ART_CULTURE = "art_culture"
    IT = "it"
    MANAGEMENT_ADMIN = "management_admin"
    PUBLIC_SERVICES = "public_services"
    OTHER = "other"


class CollaborationType(str, enum.Enum):
    IN_PERSON = "in_person"
    ONLINE = "online"
    BOTH = "both"


class PaymentTransaction(EntityBase):
    __tablename__ = "payment_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    donation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("campaign_donations.id"),
        nullable=False,
        index=True,
    )
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)

    provider = Column(Enum(PaymentProvider), nullable=False, default=PaymentProvider.MOCK)
    status = Column(
        Enum(PaymentTransactionStatus),
        nullable=False,
        default=PaymentTransactionStatus.PENDING,
        index=True,
    )

    amount = Column(Numeric(18, 2), nullable=False)
    authority = Column(String(255), nullable=False, unique=True, index=True)
    ref_id = Column(String(255), nullable=True, index=True)
    payment_url = Column(Text, nullable=True)
    callback_url = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)

    donation = relationship("CampaignDonation")
    campaign = relationship("Campaign")


class SkillContribution(EntityBase):
    __tablename__ = "skill_contributions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    skill_category = Column(Enum(SkillCategory), nullable=False, index=True)
    skill_title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    availability = Column(Text, nullable=False)
    collaboration_type = Column(Enum(CollaborationType), nullable=False)
    contact_phone = Column(String(20), nullable=True)
    document_file_id = Column(String(100), nullable=True)

    status = Column(
        Enum(SkillContributionStatus),
        nullable=False,
        default=SkillContributionStatus.PENDING,
        index=True,
    )
    owner_note = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    campaign = relationship("Campaign")
