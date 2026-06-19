from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.verifier_repository import VerifierRepository
from app.services import charity_profile_service
from app.services.notification_service import NotificationService


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
            "items": items,
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

        return request_obj

    async def approve_request(
        self,
        db: AsyncSession,
        request_id: UUID,
        verifier_id: UUID,
    ):
        request_obj = await self.get_request_detail(
            db=db,
            request_id=request_id,
        )

        if request_obj.status == "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request is already approved",
            )

        approved_request = await self.repository.approve(
            db=db,
            request_obj=request_obj,
            verifier_id=verifier_id,
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
        await charity_profile_service.create_from_verification_request(
        db=db,
        request_obj=request_obj,
)

        return approved_request

    async def reject_request(
        self,
        db: AsyncSession,
        request_id: UUID,
        verifier_id: UUID,
        reason: str,
    ):
        request_obj = await self.get_request_detail(
            db=db,
            request_id=request_id,
        )

        if request_obj.status == "rejected":
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
            "license_file",
            "statute_file",
            "newspaper_file",
            "national_card_file",
            "activity_report_file",
        ]

        return sum(
            1
            for field in document_fields
            if getattr(request_obj, field, None)
        )

    def _calculate_checklist_percent(self, request_obj) -> int:
        checklist_fields = [
            "charity_name",
            "national_id",
            "registration_number",
            "phone",
            "address",
            "description",
        ]

        filled_count = sum(
            1
            for field in checklist_fields
            if getattr(request_obj, field, None)
        )

        if not checklist_fields:
            return 0

        return round((filled_count / len(checklist_fields)) * 100)
