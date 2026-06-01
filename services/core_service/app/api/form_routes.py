from fastapi import APIRouter, Depends, HTTPException, Request, status
from uuid import UUID
from loguru import logger
from fastapi import Header

from app.domain.schemas.form_schema import (
    CreateFormRequest,
    CreateFormResponse,
    DeletedFormListResponse,
    SoftDeleteFormActionResponse,
    SeeFormsResponseSchema,
    UpdateFormNameSchema)
from app.services.form_service import FormService, get_form_service
from app.repository.form_repository import get_form_repository, FormRepository

router = APIRouter(prefix="/forms", tags=["Form Builder"])


@router.post(
    "/create",
    response_model=CreateFormResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_form(
    request: Request,
    payload: CreateFormRequest,
    form_repository: FormRepository = Depends(get_form_repository)
):
    """
    🎯 API برای ساخت فرم جدید
        """
    # 1️⃣ گرفتن user_id از request.state (که Middleware ست کرده)
    user_id_str = request.state.user_id
    
    # 2️⃣ تبدیل به UUID (اگه string بود)
    try:
        creator_id = UUID(user_id_str) if isinstance(user_id_str, str) else user_id_str
    except ValueError:
        logger.error(f"❌ Invalid UUID format: {user_id_str}")
        raise HTTPException(
            status_code=400,
            detail="Invalid user ID format"
        )
    
    logger.info(f"📝 Creating form for user {creator_id}")
    
    # 3️⃣ راه‌اندازی سرویس
    service = FormService(repository=form_repository)
    
    # 4️⃣ ساخت فرم
    new_survey = await service.create_new_form(
        creator_id=creator_id,
        title=payload.title,
    

    )
    
    logger.info(f"✅ Form created: {new_survey.survey_id}")
    
    # 5️⃣ بازگشت پاسخ
    return CreateFormResponse(
        survey_id=new_survey.survey_id,
        title=new_survey.title,
        slug=new_survey.slug,
        status="PUBLISHED" if new_survey.is_public else "DRAFT",
        created_at=new_survey.created_at
    )

@router.get(
    "/my",
    response_model=list[SeeFormsResponseSchema],
)
async def get_my_forms(
    request: Request,
    form_repository: FormRepository = Depends(get_form_repository)
):
    # ✅ 1. گرفتن user_id از JWT middleware
    user_id_str = request.state.user_id

    if not user_id_str:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    # ✅ 2. صدا زدن سرویس
    service = FormService(repository=form_repository)
    return await service.get_my_forms(user_id)

# ======================================================
# 🗑️ Trash Bin – Deleted Forms
# GET /forms/trash
# ======================================================
@router.get(
    "/trash",
    response_model=DeletedFormListResponse,
)
async def list_deleted_forms(
    request: Request,
    form_repository: FormRepository = Depends(get_form_repository),
):
    user_id_str = request.state.user_id

    if not user_id_str:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    service = FormService(repository=form_repository)

    forms = await service.list_deleted_forms(user_id)
    return DeletedFormListResponse(items=forms)

# ======================================================
# 🔄 Restore Form
# PATCH /forms/{survey_id}/restore
# ======================================================
@router.patch(
    "/{survey_id}/restore",
    response_model=SoftDeleteFormActionResponse,
)
async def restore_form(
    request: Request,
    survey_id: UUID,
    form_repository: FormRepository = Depends(get_form_repository),
):
    user_id_str = request.state.user_id

    if not user_id_str:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    service = FormService(repository=form_repository)

    return await service.restore_form(
        survey_id=survey_id,
        user_id=user_id,
    )

# ======================================================
# ☠️ Hard Delete Form
# DELETE /forms/{survey_id}/hard
# ======================================================
@router.delete(
    "/{survey_id}/hard",
    response_model=SoftDeleteFormActionResponse,
)
async def hard_delete_form(
    request: Request,
    survey_id: UUID,
    form_repository: FormRepository = Depends(get_form_repository),
):
    user_id_str = request.state.user_id

    if not user_id_str:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    service = FormService(repository=form_repository)

    return await service.hard_delete_form(
        survey_id=survey_id,
        user_id=user_id,
    )



# ======================================================
# ❌ Soft Delete Form
# DELETE /forms/{survey_id}
# ======================================================
@router.delete(
    "/{survey_id}",
    response_model=SoftDeleteFormActionResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_form(
    request: Request,
    survey_id: UUID,
    form_repository: FormRepository = Depends(get_form_repository),
):
    user_id_str = request.state.user_id

    if not user_id_str:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    service = FormService(repository=form_repository)

    return await service.soft_delete_form(
        survey_id=survey_id,
        user_id=user_id,
    )

# ======================================================
# ✏️ Update Name
# PATCH /forms/{survey_id}/name
# ======================================================
@router.patch("/{survey_id}/name")
async def update_form_name(
    survey_id: UUID,
    data: UpdateFormNameSchema,
    service: FormService = Depends(get_form_service),
):
    return await service.update_form_name(survey_id, data)


# ======================================================
# 📄 Get Form (LAST)
# GET /forms/{survey_id}
# ======================================================
@router.get("/{survey_id}")
async def get_form(
    survey_id: UUID,
    service: FormService = Depends(get_form_service),
):
    return await service.get_form(survey_id)
