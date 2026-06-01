from typing import Annotated, Any

from fastapi import APIRouter, Depends, Security, status
from fastapi.security import HTTPAuthorizationCredentials

from app.core.cache import delete_cache, get_json_cache, set_json_cache
from app.dependencies import (
    bearer_scheme,
    get_current_user,
    get_logout_service,
    get_profile_service,
    get_redis_client,
)
from app.domain.profile_schemas import (
    ChangePasswordRequest,
    UserProfileResponse,
)
from app.domain.token_schemas import LogoutRequest
from app.services1.auth_services.logout_service import LogoutService
from app.services1.profile_service import ProfileService


profile_router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
)


PROFILE_CACHE_TTL_SECONDS = 300


@profile_router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile with Redis cache",
)
async def get_profile(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    current_user: Any = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
    redis_client=Depends(get_redis_client),
):
    cache_key = f"profile:{current_user.user_id}"

    cached_profile = await get_json_cache(redis_client, cache_key)
    if cached_profile:
        return cached_profile

    profile = await service.get_profile(current_user.user_id)

    profile_data = profile.model_dump(mode="json")

    await set_json_cache(
        redis_client=redis_client,
        key=cache_key,
        value=profile_data,
        ttl_seconds=PROFILE_CACHE_TTL_SECONDS,
    )

    return profile_data


@profile_router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change current user password and invalidate profile cache",
)
async def change_password(
    payload: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    current_user: Any = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
    redis_client=Depends(get_redis_client),
):
    await service.change_password(
        current_user.user_id,
        payload.current_password,
        payload.new_password,
    )

    cache_key = f"profile:{current_user.user_id}"
    await delete_cache(redis_client, cache_key)

    return {
        "success": True,
        "message": "Password changed successfully",
    }


@profile_router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout user (invalidate refresh token)",
)
async def logout(
    body: LogoutRequest,
    logout_service: Annotated[LogoutService, Depends(get_logout_service)],
):
    await logout_service.logout(body.refresh_token)

    return {
        "message": "Logged out successfully",
    }