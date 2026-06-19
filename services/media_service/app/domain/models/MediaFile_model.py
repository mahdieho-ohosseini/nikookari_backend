from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.base import EntityBase


class MediaFile(EntityBase):
    __tablename__ = "media_files"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        index=True,
        nullable=False,
    )

    owner_user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    source_service = Column(
        String(50),
        nullable=False,
        index=True,
    )

    file_usage = Column(
        String(100),
        nullable=False,
        index=True,
    )

    original_filename = Column(
        String(255),
        nullable=False,
    )

    stored_filename = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    mime_type = Column(
        String(100),
        nullable=False,
    )

    extension = Column(
        String(20),
        nullable=True,
    )

    size_bytes = Column(
        BigInteger,
        nullable=False,
    )

    storage_backend = Column(
        String(30),
        nullable=False,
        default="local",
    )

    storage_path = Column(
        Text,
        nullable=False,
        unique=True,
    )

    public_url = Column(
        Text,
        nullable=True,
    )

    is_public = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    checksum_sha256 = Column(
        String(64),
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
