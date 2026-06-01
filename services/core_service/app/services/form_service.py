import uuid
from loguru import logger
from fastapi import Depends, HTTPException, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_db
from app.repository.form_repository import FormRepository, get_form_repository


class FormService:
    def __init__(
        self,
        repository: FormRepository = Depends(get_form_repository)
    ):
        self.repository = repository

    async def create_new_form(self, creator_id: UUID, title: str):
        logger.info(f"Creating new form '{title}' for creator {creator_id}")

        # ✅ 1. چک تکراری بودن فرم
        existing = await self.repository.get_by_creator_and_title(
            creator_id=creator_id,
            title=title
        )

        if existing:
            logger.warning(
                f"Duplicate form attempt by creator {creator_id} for title '{title}'"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have a form with this title"
            )

        # ✅ 2. تولید اسلاگ یکتا
        slug = self._generate_slug(title)
        logger.debug(f"Generated slug: {slug}")

        # ✅ 3. ساخت فرم
        survey = await self.repository.create_survey(
            creator_id=creator_id,
            title=title,
            slug=slug
        )

        # ✅ 4. commit نهایی
        try:
            await self.repository.session.commit()
        except Exception:
            await self.repository.session.rollback()
            raise

        await self.repository.session.refresh(survey)

        logger.info(f"Form {survey.survey_id} created successfully")
        return survey

    def _generate_slug(self, title: str) -> str:
        safe_title = title.strip().replace(" ", "-")[:50]
        random_suffix = uuid.uuid4().hex[:6]
        return f"{safe_title}-{random_suffix}"

    async def get_my_forms(self, creator_id: UUID):
        return await self.repository.get_forms_by_creator(creator_id)
    


    async def soft_delete_form(self, survey_id: UUID, user_id: UUID):
        # 1️⃣ چک مالکیت
        form = await self.repository.get_owned_form(
            survey_id=survey_id,
            user_id=user_id,
        )

        if not form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found or access denied",
            )

        # 2️⃣ حذف
        await self.repository.soft_delete(form)

        return {
            "message": "Form deleted successfully",
            "survey_id": survey_id,
        }    
    

    async def update_form_name(self, survey_id, data):
        form = await self.repository.get_by_id(survey_id)

        if not form:
            raise HTTPException(status_code=404, detail="Form not found")

        form.title = data.title

        await self.repository.save(form)

        return {
            "message": "Form name updated successfully",
            "title": form.title,
        } 
    async def restore_form(self, survey_id: UUID, user_id: UUID):
        # 1️⃣ چک مالکیت
        form = await self.repository.get_deleted_owned_form(
            survey_id=survey_id,
            user_id=user_id,
        )

        if not form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found or access denied",
            )

        # 2️⃣ بازیابی
        form.is_deleted = False
        form.deleted_at = None
        await self.repository.session.commit()

        return {
            "message": "Form restored successfully",
            "survey_id": survey_id,
        }
    
    
    async def get_form(self, survey_id):
        form = await self.repository.get_by_id(survey_id)
        if not form:
            raise HTTPException(status_code=404)
        return {
           "survey_id": form.survey_id,
           "title": form.title,
    }
    async def list_deleted_forms(self, user_id: UUID):
        """
        🗑️ Get all soft-deleted forms (Trash Bin)
        """
        return await self.repository.get_deleted_forms(user_id)  
    
    async def hard_delete_form(self, survey_id: UUID, user_id: UUID):
      form = await self.repository.get_deleted_owned_form(
        survey_id=survey_id,
        user_id=user_id,
     )

      if not form:
        raise HTTPException(
            status_code=404,
            detail="Deleted form not found or access denied",
        )

      await self.repository.session.delete(form)
      await self.repository.session.commit()

      return {
        "message": "Form permanently deleted",
        "survey_id": survey_id,
    }

    
  




def get_form_service(
    session: AsyncSession = Depends(get_db),
) -> FormService:
    form_repo = FormRepository(session)
    return FormService(form_repo)