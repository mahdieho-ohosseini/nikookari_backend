from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import jwt
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.api import media_routes
from app.core.config import get_settings
from app.main import app
from app.services.media_service import MediaService


OWNER_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_USER_ID = UUID("22222222-2222-4222-8222-222222222222")
VERIFIER_ID = UUID("33333333-3333-4333-8333-333333333333")
ADMIN_ID = UUID("44444444-4444-4444-8444-444444444444")

PUBLIC_FILE_ID = 1
OWNER_PRIVATE_FILE_ID = 2
OTHER_PRIVATE_FILE_ID = 3
CHARITY_VERIFICATION_FILE_ID = 4
CAMPAIGN_REPORT_FILE_ID = 5
MISSING_FILE_ID = 999999


@dataclass
class FakeMediaFile:
    id: int
    owner_user_id: UUID | None
    source_service: str
    file_usage: str
    original_filename: str
    stored_filename: str
    mime_type: str
    extension: str
    size_bytes: int
    storage_backend: str
    storage_path: str
    public_url: str | None
    is_public: bool
    checksum_sha256: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class FakeDBSession:
    async def execute(self, *_args, **_kwargs):
        return None


def make_media_file(
    *,
    file_id: int = PUBLIC_FILE_ID,
    owner_user_id: UUID | None = OWNER_ID,
    source_service: str = "core_service",
    file_usage: str = "campaign_report_image",
    original_filename: str = "test.pdf",
    mime_type: str = "application/pdf",
    extension: str = ".pdf",
    size_bytes: int = 128,
    is_public: bool = True,
) -> FakeMediaFile:
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    return FakeMediaFile(
        id=file_id,
        owner_user_id=owner_user_id,
        source_service=source_service,
        file_usage=file_usage,
        original_filename=original_filename,
        stored_filename=f"stored-{file_id}{extension}",
        mime_type=mime_type,
        extension=extension,
        size_bytes=size_bytes,
        storage_backend="local",
        storage_path=f"uploads/tests/stored-{file_id}{extension}",
        public_url=None,
        is_public=is_public,
        checksum_sha256="a" * 64,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )


def make_access_token(
    *,
    user_id: UUID = OWNER_ID,
    role: str = "donor",
    token_type: str = "access",
    expires_delta: timedelta | None = timedelta(hours=1),
) -> str:
    settings = get_settings()

    payload = {
        "sub": str(user_id),
        "role": role,
        "type": token_type,
        "jti": f"test-jti-{role}-{user_id}",
    }

    if expires_delta is not None:
        payload["exp"] = datetime.now(timezone.utc) + expires_delta

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def headers_for(*, user_id: UUID = OWNER_ID, role: str = "donor") -> dict[str, str]:
    return {
        "Authorization": f"Bearer {make_access_token(user_id=user_id, role=role)}",
    }


async def fake_get_file_by_id(db, file_id: int):
    if file_id == MISSING_FILE_ID:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found.",
        )

    if file_id == PUBLIC_FILE_ID:
        return make_media_file(
            file_id=file_id,
            owner_user_id=OTHER_USER_ID,
            file_usage="public_image",
            original_filename="public.png",
            mime_type="image/png",
            extension=".png",
            is_public=True,
        )

    if file_id == OWNER_PRIVATE_FILE_ID:
        return make_media_file(
            file_id=file_id,
            owner_user_id=OWNER_ID,
            file_usage="private_document",
            is_public=False,
        )

    if file_id == OTHER_PRIVATE_FILE_ID:
        return make_media_file(
            file_id=file_id,
            owner_user_id=OTHER_USER_ID,
            file_usage="private_document",
            is_public=False,
        )

    if file_id == CHARITY_VERIFICATION_FILE_ID:
        return make_media_file(
            file_id=file_id,
            owner_user_id=OTHER_USER_ID,
            file_usage="charity_verification_national_card",
            is_public=False,
        )

    if file_id == CAMPAIGN_REPORT_FILE_ID:
        return make_media_file(
            file_id=file_id,
            owner_user_id=OTHER_USER_ID,
            file_usage="campaign_report_image",
            is_public=False,
        )

    return make_media_file(file_id=file_id)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return headers_for(user_id=OWNER_ID, role="donor")


@pytest.fixture
def owner_headers() -> dict[str, str]:
    return headers_for(user_id=OWNER_ID, role="charity")


@pytest.fixture
def other_user_headers() -> dict[str, str]:
    return headers_for(user_id=OTHER_USER_ID, role="donor")


@pytest.fixture
def verifier_headers() -> dict[str, str]:
    return headers_for(user_id=VERIFIER_ID, role="verifier")


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return headers_for(user_id=ADMIN_ID, role="admin")


@pytest.fixture
def invalid_auth_headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer invalid-token",
    }


@pytest.fixture
def expired_auth_headers() -> dict[str, str]:
    token = make_access_token(
        user_id=OWNER_ID,
        role="donor",
        expires_delta=timedelta(seconds=-10),
    )

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
def refresh_token_headers() -> dict[str, str]:
    token = make_access_token(
        user_id=OWNER_ID,
        role="donor",
        token_type="refresh",
    )

    return {
        "Authorization": f"Bearer {token}",
    }


@pytest.fixture
def client(monkeypatch, tmp_path):
    app.dependency_overrides.clear()

    download_file_path = tmp_path / "download-test.pdf"
    download_file_path.write_bytes(b"test file content")

    async def override_db():
        return FakeDBSession()

    async def fake_upload_file(
        db,
        file,
        source_service: str,
        file_usage: str,
        owner_user_id: UUID,
        is_public: bool = False,
    ):
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File name is required.",
            )

        if file.content_type not in MediaService.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File type is not allowed. Allowed types: jpg, png, webp, pdf.",
            )

        file_bytes = await file.read()
        file_size = len(file_bytes)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        if file_size > MediaService.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size is too large. Maximum allowed size is 10MB.",
            )

        extension = Path(file.filename).suffix or ".bin"

        return make_media_file(
            file_id=100,
            owner_user_id=owner_user_id,
            source_service=source_service,
            file_usage=file_usage,
            original_filename=file.filename,
            mime_type=file.content_type,
            extension=extension,
            size_bytes=file_size,
            is_public=is_public,
        )

    async def fake_soft_delete_file(db, file_id: int, current_user: dict):
        media_file = await fake_get_file_by_id(db=db, file_id=file_id)

        MediaService.check_file_delete_access(
            media_file=media_file,
            current_user=current_user,
        )

        return {
            "message": "File deleted successfully.",
            "deleted_file_id": file_id,
        }

    def fake_get_absolute_file_path(media_file):
        return download_file_path

    app.dependency_overrides[media_routes.get_db] = override_db

    monkeypatch.setattr(
        MediaService,
        "upload_file",
        staticmethod(fake_upload_file),
    )
    monkeypatch.setattr(
        MediaService,
        "get_file_by_id",
        staticmethod(fake_get_file_by_id),
    )
    monkeypatch.setattr(
        MediaService,
        "soft_delete_file",
        staticmethod(fake_soft_delete_file),
    )
    monkeypatch.setattr(
        MediaService,
        "get_absolute_file_path",
        staticmethod(fake_get_absolute_file_path),
    )

    test_client = TestClient(app)

    yield test_client

    test_client.close()
    app.dependency_overrides.clear()