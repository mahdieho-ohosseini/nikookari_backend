from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import PROJECT_ROOT, get_settings
from app.domain.models.MediaFile_model import MediaFile
from app.utils.file_utils import generate_stored_filename, get_file_extension


settings = get_settings()


class MediaService:
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

    ADMIN_ROLES = {"admin", "verifier"}

    ALLOWED_MIME_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
    }

    VERIFIER_ALLOWED_FILE_USAGE_PREFIXES = ("charity_verification_",)

    AUTHENTICATED_ALLOWED_FILE_USAGES = {
        "campaign_report",
    
    }

    @staticmethod
    async def upload_file(
        db: AsyncSession,
        file: UploadFile,
        source_service: str,
        file_usage: str,
        owner_user_id: UUID,
        is_public: bool = False,
    ) -> MediaFile:

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

        # ✅ normalize inputs
        source_service = source_service.strip().lower()
        file_usage = file_usage.strip().lower()

        # ✅ اگر فایل مربوط به گزارش‌های کمپین باشد، به طور خودکار عمومی (is_public = True) ذخیره می‌شود
        if file_usage in MediaService.AUTHENTICATED_ALLOWED_FILE_USAGES:
            is_public = True

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

        stored_filename = generate_stored_filename(file.filename)
        extension = get_file_extension(file.filename)

        now = datetime.now(timezone.utc)

        relative_dir = (
            Path(settings.UPLOAD_DIR)
            / source_service
            / file_usage
            / str(now.year)
            / str(now.month)
        )

        absolute_dir = PROJECT_ROOT / relative_dir
        absolute_dir.mkdir(parents=True, exist_ok=True)

        relative_path = relative_dir / stored_filename
        absolute_path = PROJECT_ROOT / relative_path

        checksum = sha256(file_bytes).hexdigest()

        try:
            with open(absolute_path, "wb") as out_file:
                out_file.write(file_bytes)

            media_file = MediaFile(
                owner_user_id=owner_user_id,
                source_service=source_service,
                file_usage=file_usage,
                original_filename=file.filename,
                stored_filename=stored_filename,
                mime_type=file.content_type,
                extension=extension,
                size_bytes=file_size,
                storage_backend=settings.STORAGE_BACKEND,
                storage_path=str(relative_path).replace("\\", "/"),
                public_url=None,
                is_public=is_public,
                checksum_sha256=checksum,
            )

            db.add(media_file)
            await db.commit()
            await db.refresh(media_file)

            return media_file

        except Exception as ex:
            logger.error(f"Upload file failed: {ex}")

            if absolute_path.exists():
                absolute_path.unlink()

            await db.rollback()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="File upload failed.",
            )

    @staticmethod
    async def get_file_by_id(
        db: AsyncSession,
        file_id: int,
    ) -> MediaFile:

        query = select(MediaFile).where(
            MediaFile.id == file_id,
            MediaFile.deleted_at.is_(None),
        )

        result = await db.execute(query)
        media_file = result.scalar_one_or_none()

        if not media_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found.",
            )

        return media_file

    @staticmethod
    def check_file_access(
        media_file: MediaFile,
        current_user: dict,
        allow_verifier: bool = True,
    ) -> None:

        role = current_user.get("role")
        user_id = current_user.get("user_id")

        if media_file.is_public:
            return

        if media_file.file_usage in MediaService.AUTHENTICATED_ALLOWED_FILE_USAGES:
            return

        if role in MediaService.ADMIN_ROLES:
            return

        if media_file.owner_user_id and media_file.owner_user_id == user_id:
            return

        if (
            allow_verifier
            and role == "verifier"
            and media_file.file_usage.startswith(
                MediaService.VERIFIER_ALLOWED_FILE_USAGE_PREFIXES
            )
        ):
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this file.",
        )

    @staticmethod
    def check_file_delete_access(
        media_file: MediaFile,
        current_user: dict,
    ) -> None:

        role = current_user.get("role")
        user_id = current_user.get("user_id")

        if role in MediaService.ADMIN_ROLES:
            return

        if media_file.owner_user_id and media_file.owner_user_id == user_id:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this file.",
        )

    @staticmethod
    async def soft_delete_file(
        db: AsyncSession,
        file_id: int,
        current_user: dict,
    ) -> dict:

        media_file = await MediaService.get_file_by_id(
            db=db,
            file_id=file_id,
        )

        MediaService.check_file_delete_access(
            media_file=media_file,
            current_user=current_user,
        )

        media_file.deleted_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(media_file)

        return {
            "message": "File deleted successfully.",
            "deleted_file_id": file_id,
        }

    @staticmethod
    def get_absolute_file_path(media_file: MediaFile) -> Path:
        return PROJECT_ROOT / media_file.storage_path
