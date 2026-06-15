from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.cache import get_json_cache, set_json_cache
from app.dependencies import (
    get_redis_client,
    get_user_service,
    require_admin,
)
from app.domain.user_schemas import (
    CreateVerifierSchema,
    RoleResponseSchema,
    UserResponseSchema,
    UserRoleUpdateSchema,
)
from app.logging.audit_logger import audit_log
from app.services1.user_service import UserService


admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


ROLES_CACHE_KEY = "admin:roles"
ROLES_CACHE_TTL_SECONDS = 3600


@admin_router.get(
    "/users",
    response_model=list[UserResponseSchema],
    summary="Admin can list all users",
)
async def list_users(
    current_admin=Depends(require_admin()),
    user_service: UserService = Depends(get_user_service),
):
    audit_log(
        event="admin_list_users",
        outcome="success",
        actor_id=str(current_admin.user_id),
        actor_email=current_admin.email,
        actor_role=current_admin.role,
    )

    return await user_service.list_users()


@admin_router.get(
    "/users/{user_id}",
    response_model=UserResponseSchema,
    summary=" Admin can get user details",
)
async def get_user_detail(
    user_id: UUID,
    current_admin=Depends(require_admin()),
    user_service: UserService = Depends(get_user_service),
):
    try:
        result = await user_service.get_user_detail(user_id)

        audit_log(
            event="admin_get_user_detail",
            outcome="success",
            actor_id=str(current_admin.user_id),
            actor_email=current_admin.email,
            actor_role=current_admin.role,
            target_id=str(user_id),
            target_email=result.email,
        )

        return result

    except ValueError as error:
        audit_log(
            event="admin_get_user_detail",
            outcome="failure",
            actor_id=str(current_admin.user_id),
            actor_email=current_admin.email,
            actor_role=current_admin.role,
            target_id=str(user_id),
            details={"reason": str(error)},
        )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )


@admin_router.patch(
    "/users/{user_id}/suspend",
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
    summary=" Admin can suspend a user",
)
async def suspend_user(
    user_id: UUID,
    current_admin=Depends(require_admin()),
    user_service: UserService = Depends(get_user_service),
):
    try:
        result = await user_service.suspend_user_by_id(
            user_id,
            current_admin,
        )

        audit_log(
            event="admin_suspend_user",
            outcome="success",
            actor_id=str(current_admin.user_id),
            actor_email=current_admin.email,
            actor_role=current_admin.role,
            target_id=str(user_id),
            target_email=result.email,
        )

        return result

    except ValueError as error:
        audit_log(
            event="admin_suspend_user",
            outcome="failure",
            actor_id=str(current_admin.user_id),
            actor_email=current_admin.email,
            actor_role=current_admin.role,
            target_id=str(user_id),
            details={"reason": str(error)},
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@admin_router.patch(
    "/users/{user_id}/activate",
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Admin can activate a user",
)
async def activate_user(
    user_id: UUID,
    current_admin=Depends(require_admin()),
    user_service: UserService = Depends(get_user_service),
):
    try:
        result = await user_service.activate_user_by_id(
            user_id,
            current_admin,
        )

        audit_log(
            event="admin_activate_user",
            outcome="success",
            actor_id=str(current_admin.user_id),
            actor_email=current_admin.email,
            actor_role=current_admin.role,
            target_id=str(user_id),
            target_email=result.email,
        )

        return result

    except ValueError as error:
        audit_log(
            event="admin_activate_user",
            outcome="failure",
            actor_id=str(current_admin.user_id),
            actor_email=current_admin.email,
            actor_role=current_admin.role,
            target_id=str(user_id),
            details={"reason": str(error)},
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@admin_router.get(
    "/roles",
    response_model=RoleResponseSchema,
    summary=" List available roles with Redis cache",
)
async def list_roles(
    current_admin=Depends(require_admin()),
    user_service: UserService = Depends(get_user_service),
    redis_client=Depends(get_redis_client),
):
    audit_log(
        event="admin_list_roles",
        outcome="success",
        actor_id=str(current_admin.user_id),
        actor_email=current_admin.email,
        actor_role=current_admin.role,
    )

    cached_roles = await get_json_cache(
        redis_client,
        ROLES_CACHE_KEY,
    )

    if cached_roles:
        return cached_roles

    roles_payload = {
        "roles": user_service.list_roles(),
    }

    await set_json_cache(
        redis_client=redis_client,
        key=ROLES_CACHE_KEY,
        value=roles_payload,
        ttl_seconds=ROLES_CACHE_TTL_SECONDS,
    )

    return roles_payload


@admin_router.patch(
    "/users/{user_id}/role",
    response_model=UserResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Admin can change user role",
)
async def update_user_role(
    user_id: UUID,
    payload: UserRoleUpdateSchema,
    current_admin=Depends(require_admin()),
    user_service: UserService = Depends(get_user_service),
):
    try:
        result = await user_service.update_user_role(
            user_id=user_id,
            new_role=payload.role,
            actor_user=current_admin,
        )

        audit_log(
            event="admin_update_user_role",
            outcome="success",
            actor_id=str(current_admin.user_id),
            actor_email=current_admin.email,
            actor_role=current_admin.role,
            target_id=str(user_id),
            target_email=result.email,
            details={"new_role": payload.role},
        )

        return result

    except ValueError as error:
        audit_log(
            event="admin_update_user_role",
            outcome="failure",
            actor_id=str(current_admin.user_id),
            actor_email=current_admin.email,
            actor_role=current_admin.role,
            target_id=str(user_id),
            details={
                "new_role": payload.role,
                "reason": str(error),
            },
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@admin_router.post(
    "/verifiers",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Admin can create verifier user",
)
async def create_verifier(
    payload: CreateVerifierSchema,
    current_admin=Depends(require_admin()),
    user_service: UserService = Depends(get_user_service),
):
    try:
        result = await user_service.create_verifier(
            user_body=payload,
            actor_user=current_admin,
        )

        audit_log(
            event="admin_create_verifier",
            outcome="success",
            actor_id=str(current_admin.user_id),
            actor_email=current_admin.email,
            actor_role=current_admin.role,
            target_id=str(result.user_id),
            target_email=result.email,
            details={"assigned_role": "verifier"},
        )

        return result

    except ValueError as error:
        audit_log(
            event="admin_create_verifier",
            outcome="failure",
            actor_id=str(current_admin.user_id),
            actor_email=current_admin.email,
            actor_role=current_admin.role,
            details={
                "email": payload.email,
                "reason": str(error),
            },
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )
