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

