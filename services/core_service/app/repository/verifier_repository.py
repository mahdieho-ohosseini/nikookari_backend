from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.RegInstitute_model import CharityVerificationRequest, CharityVerificationStatus


class VerifierRepository:

    def _normalize_empty_param(self, value: Optional[str]) -> Optional[str]:
        """تبدیل مقادیر بلااستفاده سوییگر یا نال به None واقعی"""
        if value is None:
            return None
        value = value.strip()
        if not value or value.lower() in {"null", "none", "undefined", "string"}:
            return None
        return value

    async def get_dashboard_stats(self, db: AsyncSession) -> dict:
        # استفاده از Enum تعریف شده در مدل برای دقت بیشتر
        query = select(
            func.count(CharityVerificationRequest.id).label("total"),
            func.sum(
                case((CharityVerificationRequest.status == CharityVerificationStatus.PENDING, 1), else_=0)
            ).label("pending"),
            func.sum(
                case((CharityVerificationRequest.status == CharityVerificationStatus.APPROVED, 1), else_=0)
            ).label("approved"),
            func.sum(
                case((CharityVerificationRequest.status == CharityVerificationStatus.REJECTED, 1), else_=0)
            ).label("rejected"),
        )

        result = await db.execute(query)
        row = result.one()

        return {
            "total": row.total or 0,
            "pending": int(row.pending or 0),
            "approved": int(row.approved or 0),
            "rejected": int(row.rejected or 0),
        }

    async def get_dashboard_requests(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        activity_field: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ):
        status = self._normalize_empty_param(status)
        activity_field = self._normalize_empty_param(activity_field)
        search = self._normalize_empty_param(search)

        query = select(CharityVerificationRequest)
        filters = []

        if status:
            filters.append(CharityVerificationRequest.status == status)

        if activity_field:
            filters.append(CharityVerificationRequest.activity_field == activity_field)

        if search:
            keyword = f"%{search}%"
            filters.append(
                or_(
                    CharityVerificationRequest.charity_name.ilike(keyword), # اصلاح شد
                    CharityVerificationRequest.registration_number.ilike(keyword),
                    CharityVerificationRequest.email.ilike(keyword) # جایگزین کد ملی فرضی
                )
            )

        if filters:
            query = query.where(and_(*filters))

        query = (
            query
            .order_by(CharityVerificationRequest.created_at.desc()) # اصلاح شد
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(query)
        return result.scalars().all()

    async def list_requests(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CharityVerificationRequest]:
        status = self._normalize_empty_param(status)
        search = self._normalize_empty_param(search)

        query = select(CharityVerificationRequest)
        filters = []

        if status:
            filters.append(CharityVerificationRequest.status == status)

        if search:
            keyword = f"%{search}%"
            filters.append(
                or_(
                    CharityVerificationRequest.charity_name.ilike(keyword), # اصلاح شد
                    CharityVerificationRequest.registration_number.ilike(keyword)
                )
            )

        if filters:
            query = query.where(and_(*filters))

        query = (
            query
            .order_by(CharityVerificationRequest.created_at.desc()) # اصلاح شد
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        db: AsyncSession,
        request_id: UUID,
    ) -> Optional[CharityVerificationRequest]:
        query = select(CharityVerificationRequest).where(
            CharityVerificationRequest.id == request_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def approve(
        self,
        db: AsyncSession,
        request_obj: CharityVerificationRequest,
        verifier_id: UUID,
    ) -> CharityVerificationRequest:
        request_obj.status = CharityVerificationStatus.APPROVED
        request_obj.reviewed_by = verifier_id
        request_obj.rejection_reason = None
        request_obj.reviewed_at = datetime.now(timezone.utc)

        db.add(request_obj)
        await db.commit()
        await db.refresh(request_obj)
        return request_obj

    async def reject(
        self,
        db: AsyncSession,
        request_obj: CharityVerificationRequest,
        verifier_id: UUID,
        reason: str,
    ) -> CharityVerificationRequest:
        request_obj.status = CharityVerificationStatus.REJECTED
        request_obj.reviewed_by = verifier_id
        request_obj.rejection_reason = reason
        request_obj.reviewed_at = datetime.now(timezone.utc)

        db.add(request_obj)
        await db.commit()
        await db.refresh(request_obj)
        return request_obj
    
    
