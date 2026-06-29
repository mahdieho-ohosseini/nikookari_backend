from uuid import UUID

from fastapi import Depends, Request, HTTPException, status


def get_current_user(request: Request):
    user_id = getattr(request.state, "user_id", None)
    role = getattr(request.state, "user_role", None)
    user = getattr(request.state, "user", None)

    if not user_id or not role or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    return {
        "user_id": user_id,
        "role": role,
        "payload": user,
    }


def require_roles(*allowed_roles: str):
    def checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="شما دسترسی لازم برای انجام این عملیات را ندارید.",
            )
        return current_user

    return checker


def require_admin():
    return require_roles("admin")


def require_verifier():
    return require_roles("verifier")


def require_verifier_or_admin():
    return require_roles("verifier", "admin")


def require_charity():
    return require_roles("charity")


def require_donor():
    return require_roles("donor")


def get_current_user_id(current_user: dict = Depends(get_current_user)) -> UUID:
    return UUID(str(current_user["user_id"]))


def get_current_user_role(current_user: dict = Depends(get_current_user)) -> str:
    return str(current_user["role"])


def is_admin(current_user: dict) -> bool:
    return current_user.get("role") == "admin"


def is_verifier(current_user: dict) -> bool:
    return current_user.get("role") == "verifier"


def is_charity(current_user: dict) -> bool:
    return current_user.get("role") == "charity"


def is_donor(current_user: dict) -> bool:
    return current_user.get("role") == "donor"


def is_owner(current_user: dict, owner_user_id: UUID | str) -> bool:
    current_user_id = current_user.get("user_id")
    if current_user_id is None or owner_user_id is None:
        return False

    return str(current_user_id) == str(owner_user_id)


def can_manage_owned_resource(
    current_user: dict,
    owner_user_id: UUID | str,
    *,
    admin_allowed: bool = True,
) -> bool:
    if admin_allowed and is_admin(current_user):
        return True

    return is_owner(current_user, owner_user_id)