from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.skill_document_model import SkillDocument


class SkillDocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, document: SkillDocument) -> SkillDocument:
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def get_by_id(self, document_id: UUID) -> SkillDocument | None:
        result = await self.db.execute(
            select(SkillDocument).where(SkillDocument.id == document_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID):
        result = await self.db.execute(
            select(SkillDocument)
            .where(SkillDocument.user_id == user_id)
            .order_by(SkillDocument.created_at.desc())
        )
        return result.scalars().all()

    async def list_by_skill_contribution(self, skill_contribution_id: UUID):
        result = await self.db.execute(
            select(SkillDocument)
            .where(SkillDocument.skill_contribution_id == skill_contribution_id)
            .order_by(SkillDocument.created_at.desc())
        )
        return result.scalars().all()

    async def update(self, document: SkillDocument, update_data: dict) -> SkillDocument:
        for key, value in update_data.items():
            setattr(document, key, value)

        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def delete(self, document: SkillDocument) -> None:
        await self.db.delete(document)
        await self.db.commit()