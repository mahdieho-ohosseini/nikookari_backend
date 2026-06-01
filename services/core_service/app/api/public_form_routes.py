from fastapi import APIRouter, Depends
from app.services.public_form_service import PublicFormService
from app.repository.form_repository import get_form_repository, FormRepository
from app.repository.question_repository import get_question_repository, QuestionRepository
from app.repository.setting_repository import SettingRepository
from app.domain.schemas.public_form_schema import PublicFormSchema
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/public/forms",
    tags=["Public Forms"],
)

# Dependency Injection
async def get_public_form_service(
    db: AsyncSession = Depends(get_db),
) -> PublicFormService:
    form_repo = FormRepository(db)
    question_repo = QuestionRepository(db)
    setting_repo = SettingRepository(db)
    return PublicFormService(form_repo, question_repo, setting_repo)

@router.get("/s/{code}", response_model=PublicFormSchema)
async def get_public_form(
    code: str,
    service: PublicFormService = Depends(get_public_form_service)
):
    """نمایش فرم عمومی برای UI"""
    return await service.get_public_form(code)
