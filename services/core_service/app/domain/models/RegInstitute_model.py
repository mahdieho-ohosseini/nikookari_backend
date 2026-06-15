import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.base import EntityBase
from sqlalchemy import Column, String, Text, BigInteger, ForeignKey, Date, Enum
import enum

class VerificationStatus(str, enum.Enum):
    """وضعیت تأیید مؤسسه"""
    PENDING = "pending"      # در انتظار بررسی
    APPROVED = "approved"    # تأیید شده
    REJECTED = "rejected"    # رد شده

class Institute(EntityBase):
    __tablename__ = "institutes"

    institute_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        default=uuid.uuid4,
    )
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    institute_name = Column(String(255), nullable=False)
    registration_number = Column(String(50), unique=True, nullable=False)#شماره ثبت رسمی
    establishment_date = Column(Date, nullable=False)#تاریخ تأسیس
    activity_field = Column(String(100), nullable=False)#حوزه فعالیت (درمان، آموزش، ...)
    short_description = Column(Text, nullable=False)
    
    # تماس
    contact_phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    website = Column(String(255))
    
    # آدرس
    province = Column(String(50), nullable=False)
    city = Column(String(100), nullable=False)
    full_address = Column(Text, nullable=False)
    
    # مالی
    bank_name = Column(String(100), nullable=False)
    shaba_number = Column(String(26), nullable=False) # IR...
    account_owner = Column(String(255), nullable=False)
    
    # مدارک (آدرس فایل‌ها)
    articles_of_association_url = Column(Text)
    activity_license_url = Column(Text)
    national_card_url = Column(Text)
    
    status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
