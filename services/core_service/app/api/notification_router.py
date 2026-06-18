# app/presentation/api/v1/routes/notification_router.py

from uuid import UUID
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas.notification_schema import NotificationResponse
from app.services.notification_service import NotificationService
from app.core.database import get_db
from app.core.dependencies import get_current_user


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)

notification_service = NotificationService()


@router.get("", response_model=List[NotificationResponse])
async def get_my_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = UUID(current_user["user_id"])

    return await notification_service.get_my_notifications(
        db=db,
        user_id=user_id,
        skip=skip,
        limit=limit,
    )


@router.patch("/read-all")
async def mark_all_notifications_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = UUID(current_user["user_id"])

    return await notification_service.mark_all_as_read(
        db=db,
        user_id=user_id,
    )


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = UUID(current_user["user_id"])

    return await notification_service.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=user_id,
    )

