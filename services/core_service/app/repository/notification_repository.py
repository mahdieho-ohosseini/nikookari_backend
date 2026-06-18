
from uuid import UUID
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.notification_model import Notification


class NotificationRepository:

    async def create(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        title: str,
        message: str,
        type: str,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            is_read=False,
        )

        db.add(notification)
        await db.flush()
        await db.refresh(notification)
        return notification

    async def get_user_notifications(
        self,
        db: AsyncSession,
        user_id: UUID,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    async def mark_as_read(
        self,
        db: AsyncSession,
        notification_id: UUID,
        user_id: UUID,
    ) -> Notification | None:
        stmt = (
            select(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )

        result = await db.execute(stmt)
        notification = result.scalar_one_or_none()

        if not notification:
            return None

        notification.is_read = True
        db.add(notification)
        await db.flush()
        await db.refresh(notification)

        return notification

    async def mark_all_as_read(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> int:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
            .values(is_read=True)
        )

        result = await db.execute(stmt)
        await db.flush()

        return result.rowcount or 0
