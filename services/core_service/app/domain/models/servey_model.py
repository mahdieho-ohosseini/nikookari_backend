import uuid
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from app.core.base import EntityBase
from sqlalchemy.orm import relationship

class Survey(EntityBase):
    __tablename__ = "surveys"

    survey_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        index=True,
        unique=True,
        nullable=False,
        default=uuid.uuid4
    )
    creator_id = Column(
    UUID(as_uuid=True),
    nullable=False
)

    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False,index=True)
    public_code = Column(String(12), unique=True, nullable=True, index=True)
    is_public = Column(Boolean, nullable=False,server_default=text("true"))
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
    is_deleted = Column(
        Boolean,
        nullable=False,
        server_default=text("false")
    )

    deleted_at = Column(
    TIMESTAMP(timezone=True),
    nullable=True)

    settings = relationship(
    "Setting",
    back_populates="survey",
    uselist=False,
    cascade="all, delete-orphan"
)
    __table_args__ = (
      UniqueConstraint(
        "creator_id",
        "title",
        name="uq_user_form_title"
    ),
)
    questions = relationship(
        "Question",  # ← نام کلاس مدل (نه نام جدول!)
        back_populates="survey",
        cascade="all, delete-orphan",
        order_by="Question.order_index",  # ← اسم مدل رو اینجا هم اصلاح کن
        lazy="selectin"
    )

    responses = relationship(
        "Response",
        back_populates="survey",
        cascade="all, delete-orphan",
    )
    