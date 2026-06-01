from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domain.models.settings_model import Setting


class SettingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_survey_id(self, survey_id: UUID) -> Setting | None:
        result = await self.session.execute(
            select(Setting).where(Setting.survey_id == survey_id)
        )
        return result.scalar_one_or_none()

    async def create_default(self, survey_id: UUID) -> Setting:
        setting = Setting(
            survey_id=survey_id,
            is_active=False  # ✅ UX: فرم تازه = Draft
        )
        self.session.add(setting)
        await self.session.commit()
        await self.session.refresh(setting)
        return setting

    async def update_partial(self, setting: Setting, data: dict) -> Setting:
        for key, value in data.items():
                setattr(setting, key, value)

        await self.session.commit()
        await self.session.refresh(setting)
        return setting
