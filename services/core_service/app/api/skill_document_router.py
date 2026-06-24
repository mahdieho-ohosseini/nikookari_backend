from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.schemas.skill_document_schema import (
    SkillDocumentCreate,
    SkillDocumentResponse,
    SkillDocumentReview,
    SkillDocumentUpdate,
)
from app.services.jwt_middleware import get_current_user
from app.services.skill_document_service import SkillDocumentService


router = APIRouter(tags=["Skill Documents"])


@router.post(
    "/me/skill-documents",
    response_model=SkillDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_skill_document(
    data: SkillDocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = SkillDocumentService(db)
    return await service.create_document(data, current_user)


@router.get(
    "/me/skill-documents",
    response_model=list[SkillDocumentResponse],
)
async def list_my_skill_documents(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = SkillDocumentService(db)
    return await service.list_my_documents(current_user)


@router.get(
    "/skill-documents/{document_id}",
    response_model=SkillDocumentResponse,
)
async def get_skill_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = SkillDocumentService(db)
    return await service.get_document(document_id, current_user)


@router.patch(
    "/me/skill-documents/{document_id}",
    response_model=SkillDocumentResponse,
)
async def update_my_skill_document(
    document_id: UUID,
    data: SkillDocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = SkillDocumentService(db)
    return await service.update_document(document_id, data, current_user)


@router.delete("/me/skill-documents/{document_id}")
async def delete_my_skill_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = SkillDocumentService(db)
    return await service.delete_document(document_id, current_user)


@router.get(
    "/skill-contributions/{skill_contribution_id}/documents",
    response_model=list[SkillDocumentResponse],
)
async def list_documents_by_skill_contribution(
    skill_contribution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = SkillDocumentService(db)
    return await service.list_by_skill_contribution(skill_contribution_id, current_user)


@router.patch(
    "/skill-documents/{document_id}/review",
    response_model=SkillDocumentResponse,
)
async def review_skill_document(
    document_id: UUID,
    data: SkillDocumentReview,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = SkillDocumentService(db)
    return await service.review_document(document_id, data, current_user)