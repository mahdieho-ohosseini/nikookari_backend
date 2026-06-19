from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domain.models.RegInstitute_model import CharityVerificationStatus
from app.repository.verifier_repository import VerifierRepository
from app.services import charity_profile_service
from app.services.notification_service import NotificationService


settings = get_settings()


class VerifierService:
    def __init__(self) -> None:
        self.repository = VerifierRepository()
        self.notification_service = NotificationService()

    async def get_dashboard_data(
        self,
        db: AsyncSession,
        status_filter: Optional[str] = None,
        activity_field: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ):
        stats = await self.repository.get_dashboard_stats(db)

        items = await self.repository.get_dashboard_requests(
            db=db,
            status=status_filter,
            activity_field=activity_field,
            search=search_query,
            limit=limit,
            offset=offset,
        )

        return {
            "stats": stats,
            "items": [
                {
                    "id": item.id,
                    "user_id": item.user_id,
                    "charity_name": item.charity_name,
                    "status": item.status,
                    "documents_count": self._calculate_documents_count(item),
                    "checklist_percent": self._calculate_checklist_percent(item),
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                }
                for item in items
            ],
        }

    async def get_request_detail(
        self,
        db: AsyncSession,
        request_id: UUID,
    ):
        request_obj = await self.repository.get_by_id(
            db=db,
            request_id=request_id,
        )

        if not request_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verification request not found",
            )

        return self._build_request_detail_response(request_obj)

    async def approve_request(
        self,
        db: AsyncSession,
        request_id: UUID,
        verifier_id: UUID,
    ):
        request_obj = await self.repository.get_by_id(
            db=db,
            request_id=request_id,
        )

        if not request_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verification request not found",
            )

        if request_obj.status == CharityVerificationStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request is already approved",
            )

        approved_request = await self.repository.approve(
            db=db,
            request_obj=request_obj,
            verifier_id=verifier_id,
        )
        await charity_profile_service.create_from_verification_request(
        db=db,
        request_obj=request_obj,
                            )

        await self.notification_service.create(
            db=db,
            user_id=request_obj.user_id,
            title="درخواست احراز خیریه تأیید شد",
            message=(
                "درخواست احراز خیریه شما تأیید شد. "
                "اکنون می‌توانید پروفایل مؤسسه را تکمیل کنید."
            ),
            type="charity_verification_approved",
        )


        return approved_request

    async def reject_request(
        self,
        db: AsyncSession,
        request_id: UUID,
        verifier_id: UUID,
        reason: str,
    ):
        request_obj = await self.repository.get_by_id(
            db=db,
            request_id=request_id,
        )

        if not request_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verification request not found",
            )

        if request_obj.status == CharityVerificationStatus.REJECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request is already rejected",
            )

        rejected_request = await self.repository.reject(
            db=db,
            request_obj=request_obj,
            verifier_id=verifier_id,
            reason=reason,
        )

        await self.notification_service.create(
            db=db,
            user_id=request_obj.user_id,
            title="درخواست احراز خیریه رد شد",
            message=f"درخواست احراز خیریه شما رد شد. دلیل: {reason}",
            type="charity_verification_rejected",
        )

        return rejected_request

    def _calculate_documents_count(self, request_obj) -> int:
        document_fields = [
            "articles_of_association_file_id",
            "activity_license_file_id",
            "national_card_file_id",
        ]

        return sum(
            1
            for field in document_fields
            if getattr(request_obj, field, None)
        )

    def _calculate_checklist_percent(self, request_obj) -> int:
        checklist_fields = [
            "charity_name",
            "registration_number",
            "establishment_date",
            "activity_field",
            "short_description",
            "phone",
            "email",
            "province",
            "city",
            "full_address",
            "bank_name",
            "shaba_number",
            "account_owner",
        ]

        filled_count = sum(
            1
            for field in checklist_fields
            if getattr(request_obj, field, None)
        )

        if not checklist_fields:
            return 0

        return round((filled_count / len(checklist_fields)) * 100)

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

    def _build_request_detail_response(
        self,
        request_obj,
    ) -> dict:
        return {
            "id": request_obj.id,
            "user_id": request_obj.user_id,
            "status": request_obj.status,
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
            "reviewed_by": request_obj.reviewed_by,
            "reviewed_at": request_obj.reviewed_at,
            "rejection_reason": request_obj.rejection_reason,
            "created_at": request_obj.created_at,
            "updated_at": request_obj.updated_at,
        }
