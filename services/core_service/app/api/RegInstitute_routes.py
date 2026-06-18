# app/routers/charity_verification_router.py

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.domain.schemas.RegInstitute_schema import (
    CharityVerificationRequestCreateSchema,
    CharityVerificationRequestResponseSchema,
)
from app.services.RegInstitute_service import CharityVerificationService


router = APIRouter(
    prefix="/charity-verification-requests",
    tags=["Charity Verification Requests"],
)


@router.post(
    "",
    response_model=CharityVerificationRequestResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_charity_verification_request(
    payload: CharityVerificationRequestCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = CharityVerificationService(db)

    return await service.create_request(
        user_id=current_user["user_id"],
        payload=payload,
    )
