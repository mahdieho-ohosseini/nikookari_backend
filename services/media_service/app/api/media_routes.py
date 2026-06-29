from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.domain.schemas.MediaFile_schema import (
    MediaFileDeleteResponse,
    MediaFileResponse,
)
from app.logging.audit_logger import audit_log
from app.services.media_service import MediaService


router = APIRouter(
    prefix="/api/v1/media",
    tags=["Media"],
)


@router.post(
    "/upload",
    response_model=MediaFileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_file(
    source_service: str = Form(...),
    file_usage: str = Form(...),
    is_public: bool = Form(False),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    media_file = await MediaService.upload_file(
        db=db,
        file=file,
        source_service=source_service,
        file_usage=file_usage,
        owner_user_id=current_user["user_id"],
        is_public=is_public,
    )

    audit_log(
        event="media_upload_file",
        outcome="success",
        actor_id=str(current_user["user_id"]),
        actor_role=str(current_user.get("role", "")),
        target_id=str(media_file.id),
        details={
            "source_service": source_service,
            "file_usage": file_usage,
            "is_public": is_public,
            "mime_type": media_file.mime_type,
            "size_bytes": media_file.size_bytes,
        },
    )

    return media_file


@router.get(
    "/files/{file_id}",
    response_model=MediaFileResponse,
)
async def get_file_metadata(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    media_file = await MediaService.get_file_by_id(
        db=db,
        file_id=file_id,
    )

    MediaService.check_file_access(
        media_file=media_file,
        current_user=current_user,
    )

    return media_file


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    media_file = await MediaService.get_file_by_id(
        db=db,
        file_id=file_id,
    )

    MediaService.check_file_access(
        media_file=media_file,
        current_user=current_user,
    )

    absolute_path = MediaService.get_absolute_file_path(media_file)

    return FileResponse(
        path=absolute_path,
        media_type=media_file.mime_type,
        filename=media_file.original_filename,
    )


@router.delete(
    "/files/{file_id}",
    response_model=MediaFileDeleteResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await MediaService.soft_delete_file(
        db=db,
        file_id=file_id,
        current_user=current_user,
    )

    audit_log(
        event="media_delete_file",
        outcome="success",
        actor_id=str(current_user["user_id"]),
        actor_role=str(current_user.get("role", "")),
        target_id=str(file_id),
    )

    return result