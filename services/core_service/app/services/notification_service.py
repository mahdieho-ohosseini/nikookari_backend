from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository.notification_repository import NotificationRepository


class NotificationService:

    def __init__(self):
        self.repository = NotificationRepository()

    async def create_notification(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        title: str,
        message: str,
        type: str,
    ):
        return await self.repository.create(
            db=db,
            user_id=user_id,
            title=title,
            message=message,
            type=type,
        )

    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        title: str,
        message: str,
        type: str,
    ):
        notification = await self.create_notification(
            db=db,
            user_id=user_id,
            title=title,
            message=message,
            type=type,
        )

        await db.commit()
        await db.refresh(notification)

        return notification

    async def get_my_notifications(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        skip: int = 0,
        limit: int = 20,
    ):
        return await self.repository.get_user_notifications(
            db=db,
            user_id=user_id,
            skip=skip,
            limit=limit,
        )

    async def mark_as_read(
        self,
        db: AsyncSession,
        notification_id: UUID,
        user_id: UUID,
    ):
        notification = await self.repository.mark_as_read(
            db=db,
            notification_id=notification_id,
            user_id=user_id,
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="اعلان پیدا نشد.",
            )

        await db.commit()

        return notification

    async def mark_all_as_read(
        self,
        db: AsyncSession,
        user_id: UUID,
    ):
        count = await self.repository.mark_all_as_read(
            db=db,
            user_id=user_id,
        )

        await db.commit()

        return {
            "message": "همه اعلان‌ها خوانده شدند.",
            "updated_count": count,
        }
