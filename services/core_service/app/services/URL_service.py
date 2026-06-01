from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status
from uuid import UUID
import secrets
import string

from app.domain.models.servey_model import Survey
from app.repository.form_repository import (
    FormRepository,
    get_form_repository,
)
from app.repository.URL_repository import PublicLinkRepository

def generate_public_code(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))

class SurveyPublicLinkService:
    def __init__(self, repo: PublicLinkRepository):
        self.repo = repo


    async def get_or_create_public_link(
        self,
        *,
        survey_id: UUID,
        user_id: UUID,
    ) -> str:
        survey: Survey | None = await self.repo.get_owned_survey(
            survey_id=survey_id,
            user_id=user_id,
        )

        if not survey:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this survey",
            )

        if survey.public_code:
            return survey.public_code

        survey.public_code = generate_public_code()
        survey.is_public = True

        await self.repo.save_public_link(survey)

        return survey.public_code
    

    async def regenerate_public_link(
        self,
        *,
        survey_id: UUID,
        user_id: UUID,
    ) -> str:
        survey: Survey | None = await self.repo.get_owned_survey(
            survey_id=survey_id,
            user_id=user_id,
        )

        if not survey:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this survey",
            )

        survey.public_code = generate_public_code()
        survey.is_public = True

        await self.repo.save_public_link(survey)

        return survey.public_code
    
    
    async def open(self, code: str):
        survey = await self.repo.get_by_public_code(code)

        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found or not public",
            )

        # ✅ اگر settings داری
        settings = survey.settings
        if settings:
            now = datetime.now(timezone.utc)


           
            if settings.start_date and now < settings.start_date:
                raise HTTPException(403, "Survey has not started yet")

            if settings.end_date and now > settings.end_date:
                raise HTTPException(403, "Survey has ended")

        return survey
    


def get_survey_public_link_service(
    survey_repo: FormRepository = Depends(get_form_repository),
) -> SurveyPublicLinkService:
    repo = PublicLinkRepository(survey_repo)
    return SurveyPublicLinkService(repo)


