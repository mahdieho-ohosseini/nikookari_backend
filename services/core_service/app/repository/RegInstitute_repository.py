from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Depends

from app.core.database import get_db
from app.domain.models.RegInstitute_model import Institute


class InstituteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, institute_data: dict, user_id: int):
        db_institute = Institute(**institute_data, user_id=user_id)

        self.db.add(db_institute)
        await self.db.commit()
        await self.db.refresh(db_institute)

        return db_institute

    async def get_by_user_id(self, user_id: int):

        result = await self.db.execute(
            select(Institute).where(Institute.user_id == user_id)
        )

        return result.scalars().first()


# ✅ FastAPI Dependency
async def get_institute_repository(
    db: AsyncSession = Depends(get_db)
) -> InstituteRepository:
    return InstituteRepository(db)
