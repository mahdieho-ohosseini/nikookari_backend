from fastapi import Depends, HTTPException, status
import secrets
import string
from uuid import UUID
from sqlalchemy.orm import selectinload

from sqlalchemy import select

from app.domain.models.servey_model import Survey
from app.repository.form_repository import FormRepository, get_form_repository


class PublicLinkRepository:
    def __init__(
        self,
        survey_repo: FormRepository,
        
    ):
        self.survey_repo = survey_repo
        

    async def get_owned_survey(
        self,
        *,
        survey_id: UUID,
        user_id: UUID,
    ) -> Survey | None:
        return await self.survey_repo.get_owned_form(
            survey_id=survey_id,
            user_id=user_id,
        )
    
    async def save_public_link(self, survey: Survey) -> None:
        await self.survey_repo.session.commit()
        await self.survey_repo.session.refresh(survey)

    async def get_by_public_code(self, code: str) -> Survey | None:
        stmt = (
            select(Survey)
            .where(
                Survey.public_code == code,
                Survey.is_public == True,
                Survey.is_deleted == False,
            )
            .options(
                selectinload(Survey.settings),   # ✅ مهم
                selectinload(Survey.questions)
            )
        )
        result = await self.survey_repo.session.execute(stmt)
        return result.scalar_one_or_none()

