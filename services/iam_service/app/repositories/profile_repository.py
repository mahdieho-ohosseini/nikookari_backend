from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import UUID, select, update
from app.domain.models import User


class ProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> User:
        result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one()
    



