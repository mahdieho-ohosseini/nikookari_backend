from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.skill_document_model import SkillDocument
from app.domain.schemas.skill_document_schema import (
    SkillDocumentCreate,
    SkillDocumentReview,
    SkillDocumentUpdate,
)
from app.repository.skill_document_repository import SkillDocumentRepository


class SkillDocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = SkillDocumentRepository(db)

    def _user_id(self, current_user: dict) -> UUID:
        return UUID(str(current_user.get("user_id") or current_user.get("sub")))

    def _is_admin_or_verifier(self, current_user: dict) -> bool:
        return current_user.get("role") in ["admin", "verifier"]

    async def create_document(
        self,
        data: SkillDocumentCreate,
        current_user: dict,
    ) -> SkillDocument:
        document = SkillDocument(
            user_id=self._user_id(current_user),
            **data.model_dump(),
        )
        return await self.repository.create(document)

    async def list_my_documents(self, current_user: dict):
        return await self.repository.list_by_user(self._user_id(current_user))

    async def get_document(self, document_id: UUID, current_user: dict) -> SkillDocument:
        document = await self.repository.get_by_id(document_id)

        if not document:
            raise HTTPException(status_code=404, detail="Skill document not found")

        if document.user_id != self._user_id(current_user) and not self._is_admin_or_verifier(current_user):
            raise HTTPException(status_code=403, detail="You are not allowed to view this document")

        return document

    async def update_document(
        self,
        document_id: UUID,
        data: SkillDocumentUpdate,
        current_user: dict,
    ) -> SkillDocument:
        document = await self.repository.get_by_id(document_id)

        if not document:
            raise HTTPException(status_code=404, detail="Skill document not found")

        if document.user_id != self._user_id(current_user):
            raise HTTPException(status_code=403, detail="You are not allowed to update this document")

        update_data = data.model_dump(exclude_unset=True)
        return await self.repository.update(document, update_data)

    async def delete_document(self, document_id: UUID, current_user: dict) -> dict:
        document = await self.repository.get_by_id(document_id)

        if not document:
            raise HTTPException(status_code=404, detail="Skill document not found")

        if document.user_id != self._user_id(current_user):
            raise HTTPException(status_code=403, detail="You are not allowed to delete this document")

        await self.repository.delete(document)

        return {
            "status": "success",
            "message": "Skill document deleted successfully",
        }

    async def list_by_skill_contribution(
        self,
        skill_contribution_id: UUID,
        current_user: dict,
    ):
        if not self._is_admin_or_verifier(current_user):
            raise HTTPException(status_code=403, detail="Only admin or verifier can access this list")

        return await self.repository.list_by_skill_contribution(skill_contribution_id)

    async def review_document(
        self,
        document_id: UUID,
        data: SkillDocumentReview,
        current_user: dict,
    ) -> SkillDocument:
        if not self._is_admin_or_verifier(current_user):
            raise HTTPException(status_code=403, detail="Only admin or verifier can review documents")

        document = await self.repository.get_by_id(document_id)

        if not document:
            raise HTTPException(status_code=404, detail="Skill document not found")

        return await self.repository.update(
            document,
            {
                "status": data.status,
                "review_note": data.review_note,
            },
        )