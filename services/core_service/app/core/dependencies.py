from fastapi import Request, HTTPException, status


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


def require_roles(*allowed_roles):
    def dependency(request: Request):
        role = getattr(request.state, "user_role", None)
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
        return True

    return dependency
