from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.schemas.charity_profile_schema import (
    CharityProfileResponse,
    CharityProfileSubmitResponse,
    CharityProfileUpdate,
    MyCharityProfileResponse,
)
from app.services.charity_profile_service import CharityProfileService

router = APIRouter(
    prefix="/charity/profile",
    tags=["Charity Profile"],
)

charity_profile_service = CharityProfileService()


def get_current_user_id(request: Request) -> UUID:
    return UUID(str(request.state.user_id))


@router.get(
    "/me",
    response_model=MyCharityProfileResponse,
)
async def get_my_charity_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = get_current_user_id(request)

    return await charity_profile_service.get_my_profile(
        db=db,
        user_id=user_id,
    )


@router.patch(
    "/{profile_id}",
    response_model=CharityProfileResponse,
)
async def update_charity_profile(
    profile_id: UUID,
    payload: CharityProfileUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = get_current_user_id(request)

    return await charity_profile_service.update_my_profile(
        db=db,
        profile_id=profile_id,
        user_id=user_id,
        payload=payload,
    )


@router.post(
    "/{profile_id}/submit",
    response_model=CharityProfileSubmitResponse,
)
async def submit_charity_profile(
    profile_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_id = get_current_user_id(request)

    profile = await charity_profile_service.submit_my_profile(
        db=db,
        profile_id=profile_id,
        user_id=user_id,
    )

    return {
        "id": profile.id,
        "status": profile.status,
        "message": "Charity profile submitted for review",
    }
