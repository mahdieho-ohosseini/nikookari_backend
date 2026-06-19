import enum
import uuid

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.base import EntityBase


class CharityVerificationStatus(str, enum.Enum):
    """وضعیت تأیید مؤسسه"""

    PENDING = "pending"      # در انتظار بررسی
    APPROVED = "approved"    # تأیید شده
    REJECTED = "rejected"    # رد شده


class CharityProfileStatus(str, enum.Enum):
    incomplete = "incomplete" #کامل نشده
    active = "active"   #خیریه تایید شده
    pending_review = "pending_review"#در دست بررسی
    suspended = "suspended"#غیرفعال 
    rejected = "rejected"




class CharityVerificationRequest(EntityBase):
    __tablename__ = "charity_verification_requests"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        default=uuid.uuid4,
    )

    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    charity_name = Column(String(255), nullable=False)
    registration_number = Column(String(50), unique=False, nullable=False, index=True)  # شماره ثبت رسمی
    establishment_date = Column(Date, nullable=False)  # تاریخ تأسیس
    activity_field = Column(String(100), nullable=False)  # حوزه فعالیت (درمان، آموزش، ...)
    short_description = Column(Text, nullable=False)

    # تماس
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    website = Column(String(255))

    # آدرس
    province = Column(String(50), nullable=False)
    city = Column(String(100), nullable=False)
    full_address = Column(Text, nullable=False)

    # مالی
    bank_name = Column(String(100), nullable=False)
    shaba_number = Column(String(26), nullable=False)  # IR...
    account_owner = Column(String(255), nullable=False)

    # مدارک احراز خیریه - file_id دریافتی از media_service
    articles_of_association_file_id = Column(BigInteger, nullable=True)
    activity_license_file_id = Column(BigInteger, nullable=True)
    national_card_file_id = Column(BigInteger, nullable=True)

    status = Column(
        Enum(CharityVerificationStatus),
        nullable=False,
        default=CharityVerificationStatus.PENDING,
        index=True,
    )
    rejection_reason = Column(Text, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    profile = relationship(
        "CharityProfile",
        back_populates="verification_request",
        uselist=False,
    )


class CharityProfile(EntityBase):
    __tablename__ = "charity_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    verification_request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("charity_verification_requests.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    charity_name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)  # آدرس خوانا و یکتای صفحه خیریه

    registration_number = Column(String(100), nullable=False)
    establishment_date = Column(Date, nullable=True)
    activity_field = Column(String(150), nullable=True)

    phone = Column(String(30), nullable=False)
    email = Column(String(255), nullable=False)
    website = Column(String(255), nullable=True)
    province = Column(String(50), nullable=True)
    city = Column(String(100), nullable=True)
    full_address = Column(Text, nullable=True)

    shaba_number = Column(String(50), nullable=True)
    bank_name = Column(String(150), nullable=True)
    account_name = Column(String(255), nullable=True)

    logo_file_id = Column(BigInteger, nullable=True)
    cover_file_id = Column(BigInteger, nullable=True)

    short_description = Column(Text, nullable=True)
    about_text = Column(Text, nullable=True)
    vision_text = Column(Text, nullable=True)

    social_links = Column(JSON, nullable=True)

    status = Column(
        Enum(CharityProfileStatus),
        nullable=False,
        default=CharityProfileStatus.incomplete,
        index=True,
    )

    is_published = Column(Boolean, nullable=False, default=False)
    published_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    verification_request = relationship(
        "CharityVerificationRequest",
        back_populates="profile",
    )