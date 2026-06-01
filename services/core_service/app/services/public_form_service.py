from datetime import datetime, timezone
from fastapi import HTTPException, status

from app.repository.form_repository import FormRepository
from app.repository.question_repository import QuestionRepository
from app.repository.setting_repository import SettingRepository
from app.domain.schemas.public_form_schema import PublicFormSchema

class PublicFormService:
    def __init__(
        self,
        form_repo: FormRepository,
        question_repo: QuestionRepository,
        setting_repo: SettingRepository,
    ):
        self.form_repo = form_repo
        self.question_repo = question_repo
        self.setting_repo = setting_repo

    async def get_public_form(self, code: str) -> PublicFormSchema:
        """دریافت فرم عمومی برای نمایش در UI"""

        form = await self.form_repo.get_by_public_code(code)
        if not form:
            raise HTTPException(status_code=404, detail="لینک فرم معتبر نیست یا حذف شده است.")

        # بارگیری تنظیمات
        setting = await self.setting_repo.get_by_survey_id(form.survey_id)

        # بررسی تاریخ‌ها
        now = datetime.now(timezone.utc)
        if setting:
            if setting.start_date and now < setting.start_date:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="فرم هنوز فعال نشده است."
                )
            if setting.end_date and now > setting.end_date:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="زمان ثبت پاسخ در این فرم به پایان رسیده است."
                )

        # بارگیری سوالات
        questions = await self.question_repo.list_by_survey_id(form.survey_id)

        # ساخت پاسخ نهایی برای UI
        return PublicFormSchema(
            title=form.title,
            public_code=form.public_code,
            settings=setting,
            questions=questions
        )
