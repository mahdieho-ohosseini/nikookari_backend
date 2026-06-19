from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.domain.schemas.RegInstitute_schema import (
    CharityVerificationCancelResponseSchema,
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


@router.get(
    "/me/latest",
    response_model=CharityVerificationRequestResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_my_latest_charity_verification_request(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = CharityVerificationService(db)

    return await service.get_my_latest_request(
        user_id=current_user["user_id"],
    )


@router.delete(
    "/me/pending",
    response_model=CharityVerificationCancelResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def delete_my_pending_charity_verification_request(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = CharityVerificationService(db)

    return await service.delete_my_pending_request(
        user_id=current_user["user_id"],
    )