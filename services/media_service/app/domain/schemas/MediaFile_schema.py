from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MediaFileResponse(BaseModel):
    id: int

    owner_user_id: Optional[UUID] = None

    source_service: str
    file_usage: str

    original_filename: str
    stored_filename: str

    mime_type: str
    extension: Optional[str] = None
    size_bytes: int

    storage_backend: str
    storage_path: str
    public_url: Optional[str] = None
    is_public: bool

    checksum_sha256: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MediaFileDeleteResponse(BaseModel):
    message: str
    deleted_file_id: int
