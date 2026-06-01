from fastapi import Depends, HTTPException, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_db
from uuid import UUID
from datetime import datetime, timezone

from app.repository.setting_repository import SettingRepository
from app.repository.form_repository import FormRepository
from app.repository.question_repository import QuestionRepository
from app.domain.setting_errors import (
    SettingNotFound,
    SettingForbidden,
    SettingValidationError,
)

class SettingService:
    def __init__(
        self,
        setting_repo: SettingRepository,
        form_repo: FormRepository,
        question_repo: QuestionRepository,
    ):
        self.setting_repo = setting_repo
        self.form_repo = form_repo
        self.question_repo = question_repo

    async def get_settings(self, survey_id: UUID, user_id: UUID):
        survey = await self.form_repo.get_by_id(survey_id)
        if not survey:
            raise SettingNotFound("Survey not found")

        user_uuid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
        if survey.creator_id != user_uuid:
            raise SettingForbidden("You are not the owner of this survey")

        setting = await self.setting_repo.get_by_survey_id(survey_id)
        if not setting:
            setting = await self.setting_repo.create_default(survey_id)

        return setting

    async def update_settings(
        self,
        survey_id: UUID,
        user_id: UUID,
        data: dict
    ):
        user_uuid = UUID(str(user_id)) if isinstance(user_id, str) else user_id

        survey = await self.form_repo.get_by_id(survey_id)
        if not survey:
            raise SettingNotFound("Survey not found")

        if survey.creator_id != user_uuid:
            raise SettingForbidden("You are not the owner of this survey")

        setting = await self.setting_repo.get_by_survey_id(survey_id)
        if not setting:
            raise SettingNotFound("Settings not found")

        # ✅ state نهایی
        final_start = data.get("start_date", setting.start_date)
        final_end = data.get("end_date", setting.end_date)
        final_active = data.get("is_active", setting.is_active)

        # ✅ ساختار تاریخ‌ها (فقط اگر هر دو وجود دارند)
        if final_start and final_end and final_start > final_end:
            raise SettingValidationError(
                "start_date must be before end_date"
            )

        # ✅ validation اجرایی فقط هنگام activation
        if final_active is True:
            now = datetime.now(timezone.utc)

            if final_start and now < final_start:
                raise SettingValidationError("Survey has not started yet")

            if final_end and now > final_end:
                raise SettingValidationError("Survey has already ended")

            count = await self.question_repo.count_by_survey_id(survey_id)
            if count == 0:
                raise SettingValidationError(
                    "Survey must have at least one question before activation"
                )

        return await self.setting_repo.update_partial(setting, data)



def get_setting_service(
    db: AsyncSession = Depends(get_db),
) -> SettingService:
    return SettingService(
        setting_repo=SettingRepository(db),
        form_repo=FormRepository(db),
        question_repo=QuestionRepository(db),
    )
