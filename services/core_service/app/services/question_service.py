from uuid import UUID
from fastapi import Depends, HTTPException, status

from app.repository.question_repository import (
    QuestionRepository,
    get_question_repository,
)
from app.repository.form_repository import (
    FormRepository,
    get_form_repository,
)

from app.domain.schemas.question_schema import (
    CreateTextQuestionRequest,
    DeleteQuestionResponse,
    QuestionListItemSchema,
    QuestionListResponse,
    QuestionUpdateSchema,
)


class QuestionService:
    def __init__(
        self,
        question_repo: QuestionRepository,
        form_repo: FormRepository,
    ):
        self.question_repo = question_repo
        self.form_repo = form_repo

    # =========================================================
    # CREATE — Add Text Question
    # =========================================================
    async def add_text_question(
        self,
        *,
        survey_id: UUID,
        user_id: UUID,
        payload: CreateTextQuestionRequest,
    ):
        # ✅ Ownership check
        form = await self.form_repo.get_owned_form(
            survey_id=survey_id,
            user_id=user_id,
        )
        if not form:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this form",
            )

        # ✅ Duplicate check
        exists = await self.question_repo.exists_question(
            survey_id=survey_id,
            question_text=payload.question_text,
        )
        if exists:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Question with same text already exists in this form",
            )

        # ✅ Calculate order_index
        last_order = await self.question_repo.get_last_order(survey_id)
        order_index = last_order + 1

        # ✅ Create question
        question = await self.question_repo.create_question(
            survey_id=survey_id,
            question_text=payload.question_text,
            description=payload.description,
            is_required=payload.is_required,
            min_length=payload.min_length,
            max_length=payload.max_length,
            order_index=order_index,
        )

        await self.question_repo.session.commit()
        await self.question_repo.session.refresh(question)

        return question

    # =========================================================
    # READ — List Questions
    # =========================================================
    async def list_questions(
        self,
        *,
        survey_id: UUID,
        user_id: UUID,
    ) -> QuestionListResponse:
        # ✅ Ownership check
        survey = await self.form_repo.get_owned_form(
            survey_id=survey_id,
            user_id=user_id,
        )
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this form",
            )

        questions = await self.question_repo.list_by_survey_id(survey_id)

        return QuestionListResponse(
            items=[
                QuestionListItemSchema.from_orm(q)
                for q in questions
            ]
        )

    # =========================================================
    # READ — Get Question For Edit
    # =========================================================
    async def get_question_for_edit(
        self,
        *,
        survey_id: UUID,
        question_id: UUID,
        user_id: UUID,
    ):
        # ✅ Ownership check
        survey = await self.form_repo.get_owned_form(
            survey_id=survey_id,
            user_id=user_id,
        )
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this form",
            )

        # ✅ Load question
        question = await self.question_repo.get_by_id_and_survey(
            question_id=question_id,
            survey_id=survey_id,
        )
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found",
            )

        return question

    # =========================================================
    # UPDATE — Update Question
    # =========================================================
    async def update_question(
        self,
        *,
        survey_id: UUID,
        question_id: UUID,
        user_id: UUID,
        data: QuestionUpdateSchema,
    ):
        # ✅ Ownership check
        survey = await self.form_repo.get_owned_form(
            survey_id=survey_id,
            user_id=user_id,
        )
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this form",
            )

        # ✅ Load question
        question = await self.question_repo.get_by_id_and_survey(
            question_id=question_id,
            survey_id=survey_id,
        )
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found",
            )

        # ✅ Update only provided fields
        if data.question_text is not None:
            question.question_text = data.question_text

        if data.description is not None:
            question.description = data.description

        if data.is_required is not None:
            question.is_required = data.is_required

        await self.question_repo.session.commit()
        await self.question_repo.session.refresh(question)

        return question

    # =========================================================
    # DELETE — Delete Question
    # =========================================================
    async def delete_question(
        self,
        *,
        survey_id: UUID,
        question_id: UUID,
        user_id: UUID,
    ) -> DeleteQuestionResponse:
        # ✅ Ownership check
        survey = await self.form_repo.get_owned_form(
            survey_id=survey_id,
            user_id=user_id,
        )
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this form",
            )

        # ✅ Load question
        question = await self.question_repo.get_by_id_and_survey(
            question_id=question_id,
            survey_id=survey_id,
        )
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found",
            )

        await self.question_repo.delete(question)
        await self.question_repo.session.commit()

        return DeleteQuestionResponse(
            success=True,
            message="Question deleted successfully",
            question_id=question_id,
        )


# =========================================================
# Dependency Factory
# =========================================================
def get_question_service(
    question_repo: QuestionRepository = Depends(get_question_repository),
    form_repo: FormRepository = Depends(get_form_repository),
) -> QuestionService:
    return QuestionService(
        question_repo=question_repo,
        form_repo=form_repo,
    )
