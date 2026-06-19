from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domain.models.RegInstitute_model import CharityVerificationStatus
from app.domain.schemas.RegInstitute_schema import CharityVerificationRequestCreateSchema
from app.repository.RegInstitute_repository import CharityVerificationRepository


settings = get_settings()


class CharityVerificationService:
    def __init__(self, db: AsyncSession):
        self.repository = CharityVerificationRepository(db)

    async def create_request(
        self,
        user_id: UUID,
        payload: CharityVerificationRequestCreateSchema,
    ):
        if await self.repository.has_open_request(user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="شما یک درخواست در حال بررسی دارید.",
            )

        if await self.repository.has_approved_request(user_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="خیریه شما قبلاً تأیید شده است.",
            )

        data = payload.model_dump()
        data["user_id"] = user_id
        data["status"] = CharityVerificationStatus.PENDING

        created_request = await self.repository.create(data)

        return self._build_request_response(created_request)

    async def get_my_latest_request(
        self,
        user_id: UUID,
    ) -> dict:
        request_obj = await self.repository.get_latest_by_user_id(user_id)

        if not request_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="درخواستی برای شما پیدا نشد.",
            )

        return self._build_request_response(request_obj)

    async def delete_my_pending_request(
        self,
        user_id: UUID,
    ) -> dict:
        request_obj = await self.repository.get_open_request_by_user_id(user_id)

        if not request_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="درخواست در حال بررسی برای شما پیدا نشد.",
            )

        deleted_request_id = request_obj.id

        await self.repository.delete_by_id(deleted_request_id)

        return {
            "message": "درخواست در حال بررسی با موفقیت حذف شد.",
            "deleted_request_id": deleted_request_id,
        }

    def _build_media_file_link(
        self,
        file_id: Optional[int],
    ) -> dict:
        if not file_id:
            return {
                "file_id": None,
                "metadata_url": None,
                "download_url": None,
            }

        media_base_url = settings.MEDIA_SERVICE_URL.rstrip("/")

        return {
            "file_id": file_id,
            "metadata_url": f"{media_base_url}/api/v1/media/files/{file_id}",
            "download_url": f"{media_base_url}/api/v1/media/files/{file_id}/download",
        }

    def _build_request_response(
        self,
        request_obj,
    ) -> dict:
        return {
            "id": request_obj.id,
            "user_id": request_obj.user_id,
            "charity_name": request_obj.charity_name,
            "registration_number": request_obj.registration_number,
            "establishment_date": request_obj.establishment_date,
            "activity_field": request_obj.activity_field,
            "short_description": request_obj.short_description,
            "phone": request_obj.phone,
            "email": request_obj.email,
            "website": request_obj.website,
            "province": request_obj.province,
            "city": request_obj.city,
            "full_address": request_obj.full_address,
            "bank_name": request_obj.bank_name,
            "shaba_number": request_obj.shaba_number,
            "account_owner": request_obj.account_owner,
            "articles_of_association_file_id": request_obj.articles_of_association_file_id,
            "activity_license_file_id": request_obj.activity_license_file_id,
            "national_card_file_id": request_obj.national_card_file_id,
            "documents": {
                "articles_of_association": self._build_media_file_link(
                    request_obj.articles_of_association_file_id
                ),
                "activity_license": self._build_media_file_link(
                    request_obj.activity_license_file_id
                ),
                "national_card": self._build_media_file_link(
                    request_obj.national_card_file_id
                ),
            },
            "status": request_obj.status,
            "rejection_reason": request_obj.rejection_reason,
            "reviewed_by": request_obj.reviewed_by,
            "reviewed_at": request_obj.reviewed_at,
            "created_at": request_obj.created_at,
            "updated_at": request_obj.updated_at,
        }