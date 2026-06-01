from uuid import UUID
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import RefreshToken

class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def delete_all_by_user_id(self, user_id: UUID) -> None:
        stmt = delete(RefreshToken).where(
            RefreshToken.user_id == user_id
        )
        await self.session.execute(stmt)
