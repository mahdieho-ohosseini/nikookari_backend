import re
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.RegInstitute_model import (
    CharityProfile,
    CharityProfileStatus,
    CharityVerificationRequest,
)
from app.domain.schemas.charity_profile_schema import CharityProfileUpdate
from app.repository.charity_profile_repository import CharityProfileRepository
from app.services.notification_service import NotificationService


class CharityProfileService:
    def __init__(self):
        self.repository = CharityProfileRepository()
        self.notification_service = NotificationService()
    async def get_profiles_for_review(
       self,
       db: AsyncSession,
) ->   list[CharityProfile]:
       return await self.repository.get_pending_profiles(db=db)


    async def get_my_profile(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> dict:
        profile = await self.repository.get_by_user_id(db, user_id)

        if not profile:
            return {
                "has_profile": False,
                "profile": None,
            }

        return {
            "has_profile": True,
            "profile": profile,
        }

    async def get_user_profile_by_id(
        self,
        db: AsyncSession,
        profile_id: UUID,
        user_id: UUID,
    ) -> CharityProfile:
        profile = await self.repository.get_by_id_and_user_id(
            db=db,
            profile_id=profile_id,
            user_id=user_id,
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Charity profile not found",
            )

        return profile

    async def create_from_verification_request(
        self,
        db: AsyncSession,
        request_obj: CharityVerificationRequest,
    ) -> CharityProfile:
        existing_profile = await self.repository.get_by_verification_request_id(
            db=db,
            verification_request_id=request_obj.id,
        )

        if existing_profile:
            return existing_profile

        slug = await self._generate_unique_slug(
            db=db,
            base_text=request_obj.charity_name,
        )

        profile = CharityProfile(
            user_id=request_obj.user_id,
            verification_request_id=request_obj.id,
            charity_name=request_obj.charity_name,
            slug=slug,
            registration_number=request_obj.registration_number,
            establishment_date=request_obj.establishment_date,
            activity_field=request_obj.activity_field,
            phone=request_obj.phone,
            email=request_obj.email,
            website=request_obj.website,
            province=request_obj.province,
            city=request_obj.city,
            full_address=request_obj.full_address,
            shaba_number=request_obj.shaba_number,
            bank_name=request_obj.bank_name,
            account_name=request_obj.account_owner,
            short_description=request_obj.short_description,
            status=CharityProfileStatus.incomplete,
            is_published=False,
        )

        return await self.repository.create(db=db, profile=profile)

    async def update_my_profile(
        self,
        db: AsyncSession,
        profile_id: UUID,
        user_id: UUID,
        payload: CharityProfileUpdate,
    ) -> CharityProfile:
        profile = await self.get_user_profile_by_id(
            db=db,
            profile_id=profile_id,
            user_id=user_id,
        )

        if profile.status not in [
            CharityProfileStatus.incomplete,
            CharityProfileStatus.rejected,
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This profile can not be edited in current status",
            )

        data = payload.model_dump(exclude_unset=True)

        updated_profile = await self.repository.update(
            db=db,
            profile=profile,
            data=data,
        )

        await db.commit()
        await db.refresh(updated_profile)

        return updated_profile

    async def submit_my_profile(
        self,
        db: AsyncSession,
        profile_id: UUID,
        user_id: UUID,
    ) -> CharityProfile:
        profile = await self.get_user_profile_by_id(
            db=db,
            profile_id=profile_id,
            user_id=user_id,
        )

        if profile.status not in [
            CharityProfileStatus.incomplete,
            CharityProfileStatus.rejected,
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This profile can not be submitted in current status",
            )

        self._validate_profile_before_submit(profile)

        submitted_profile = await self.repository.set_status(
            db=db,
            profile=profile,
            status=CharityProfileStatus.pending_review,
        )

        await self.notification_service.create_notification(
            db=db,
            user_id=user_id,
            title="پروفایل برای بررسی ارسال شد",
            message="پروفایل خیریه شما با موفقیت برای بررسی ارسال شد.",
            type="charity_profile_submitted",
        )

        await db.commit()
        await db.refresh(submitted_profile)

        return submitted_profile

    def _validate_profile_before_submit(
        self,
        profile: CharityProfile,
    ) -> None:
        required_fields = {
            "charity_name": profile.charity_name,
            "short_description": profile.short_description,
            "about_text": profile.about_text,
            "phone": profile.phone,
            "email": profile.email,
            "province": profile.province,
            "city": profile.city,
            "full_address": profile.full_address,
        }

        missing_fields = [
            field_name
            for field_name, value in required_fields.items()
            if value is None or str(value).strip() == ""
        ]

        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Profile is incomplete",
                    "missing_fields": missing_fields,
                },
            )

    async def _generate_unique_slug(
        self,
        db: AsyncSession,
        base_text: str,
    ) -> str:
        base_slug = self._slugify(base_text)
        slug = base_slug
        counter = 1

        while await self.repository.get_by_slug(db=db, slug=slug):
            counter += 1
            slug = f"{base_slug}-{counter}"

        return slug

    def _slugify(
        self,
        text: str,
    ) -> str:
        text = text.strip().lower()
        text = re.sub(r"\s+", "-", text)
        text = re.sub(r"[^a-z0-9\u0600-\u06FF-]", "", text)
        text = text.strip("-")

        if not text:
            return "charity"

        return text

    async def approve_profile(
        self,
        db: AsyncSession,
        profile_id: UUID,
    ) -> CharityProfile:
        profile = await self.repository.get_by_id(db=db, profile_id=profile_id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Charity profile not found",
            )

        if profile.status != CharityProfileStatus.pending_review:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending review profiles can be approved",
            )

        await self.repository.update_status(
            db=db,
            profile_id=profile_id,
            status=CharityProfileStatus.active,
        )

        profile = await self.repository.update_is_published(
            db=db,
            profile_id=profile_id,
            is_published=True,
        )

        await self.notification_service.create_notification(
            db=db,
            user_id=profile.user_id,
            title="پروفایل خیریه تایید شد",
            message="پروفایل خیریه شما تایید شد و اکنون منتشر شده است.",
            type="charity_profile_approved",
        )

        await db.commit()
        await db.refresh(profile)

        return profile

    async def reject_profile(
        self,
        db: AsyncSession,
        profile_id: UUID,
    ) -> CharityProfile:
        profile = await self.repository.get_by_id(db=db, profile_id=profile_id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Charity profile not found",
            )

        if profile.status != CharityProfileStatus.pending_review:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending review profiles can be rejected",
            )

        await self.repository.update_status(
            db=db,
            profile_id=profile_id,
            status=CharityProfileStatus.rejected,
        )

        profile = await self.repository.update_is_published(
            db=db,
            profile_id=profile_id,
            is_published=False,
        )

        await self.notification_service.create_notification(
            db=db,
            user_id=profile.user_id,
            title="پروفایل خیریه رد شد",
            message="پروفایل خیریه شما رد شد. لطفاً اطلاعات را بررسی و دوباره ارسال کنید.",
            type="charity_profile_rejected",
        )

        await db.commit()
        await db.refresh(profile)

        return profile
