from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app import dependencies as deps
from app.core.database import get_db
from app.domain.profile_schemas import UserProfileResponse


VALID_PASSWORD = "Valid@123"

ADMIN_ID = UUID("11111111-1111-1111-1111-111111111111")
DONOR_ID = UUID("22222222-2222-2222-2222-222222222222")
TARGET_USER_ID = UUID("33333333-3333-3333-3333-333333333333")
MISSING_USER_ID = UUID("40404040-4040-4040-4040-404040404040")


@dataclass
class FakeUser:
    user_id: UUID
    full_name: str
    email: str
    role: str = "donor"
    status: str = "active"
    is_verified: bool = True
    last_login: datetime | None = None
    created_at: datetime | None = None
    onboarding_token: str | None = None
    onboarding_link: str | None = None
    must_change_password: bool = False
    password_hash: str = "hashed-password"


def make_user(
    *,
    user_id: UUID | None = None,
    role: str = "donor",
    email: str | None = None,
    full_name: str | None = None,
    status: str = "active",
    is_verified: bool = True,
) -> FakeUser:
    if user_id is None:
        user_id = ADMIN_ID if role == "admin" else DONOR_ID

    return FakeUser(
        user_id=user_id,
        full_name=full_name or f"{role.title()} User",
        email=email or f"{role}@gmail.com",
        role=role,
        status=status,
        is_verified=is_verified,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def user_response_dict(
    *,
    user_id: UUID | None = None,
    email: str = "user@gmail.com",
    full_name: str = "Test User",
    role: str = "donor",
    status_value: str = "active",
    is_verified: bool = True,
) -> dict[str, Any]:
    return {
        "user_id": str(user_id or uuid4()),
        "full_name": full_name,
        "email": email,
        "role": role,
        "status": status_value,
        "last_login": None,
        "created_at": "2026-01-01T00:00:00Z",
        "is_verified": is_verified,
        "onboarding_token": None,
        "onboarding_link": None,
    }


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, Any] = {}
        self.counts: dict[str, int] = {}
        self.expirations: dict[str, int] = {}

    async def ping(self) -> bool:
        return True

    async def incr(self, key: str) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    async def expire(self, key: str, seconds: int) -> bool:
        self.expirations[key] = seconds
        return True

    async def ttl(self, key: str) -> int:
        return self.expirations.get(key, 60)

    async def get(self, key: str) -> Any | None:
        return self.values.get(key)

    async def setex(self, key: str, *args, **kwargs) -> bool:
        if "value" in kwargs:
            value = kwargs["value"]
            ttl = int(kwargs.get("time", kwargs.get("ttl", 60)))
        elif len(args) == 2:
            ttl, value = args
        else:
            raise TypeError("setex expects key, ttl, value")

        self.values[key] = value
        self.expirations[key] = int(ttl)
        return True

    async def delete(self, *keys: str) -> int:
        deleted = 0

        for key in keys:
            if key in self.values or key in self.counts:
                deleted += 1

            self.values.pop(key, None)
            self.counts.pop(key, None)
            self.expirations.pop(key, None)

        return deleted

    async def exists(self, key: str) -> int:
        return int(key in self.values)


class FakeDBSession:
    async def execute(self, *_args, **_kwargs):
        return None


class FakeRegisterService:
    async def register_user(self, user_data):
        if user_data.email == "exists@gmail.com":
            raise HTTPException(status_code=400, detail="User already exists")

        return {
            "success": True,
            "message": "OTP sent to email",
        }

    async def verify_user(self, verify_schema):
        if verify_schema.email == "expired@gmail.com":
            raise HTTPException(
                status_code=400,
                detail="Registration expired. Please register again.",
            )

        if verify_schema.otp in {"0000", "bad", "999999"}:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")

        return {
            "success": True,
            "verified": True,
            "message": "User created successfully",
            "user": user_response_dict(email=verify_schema.email),
        }

    async def resend_otp(self, resend_schema):
        if resend_schema.email == "nopending@gmail.com":
            raise HTTPException(
                status_code=400,
                detail="No pending registration for this email",
            )

        if resend_schema.email == "cooldown@gmail.com":
            raise HTTPException(
                status_code=429,
                detail="OTP already sent. Please wait before requesting again.",
            )

        return {
            "success": True,
            "message": "OTP resent successfully",
        }


class FakeLoginService:
    async def authenticate_user(self, login_data):
        if login_data.email == "missing@gmail.com":
            raise HTTPException(status_code=400, detail="User does not exist")

        if login_data.email == "unverified@gmail.com":
            raise HTTPException(status_code=400, detail="User is not verified")

        if login_data.email == "suspended@gmail.com":
            raise HTTPException(status_code=403, detail="User account is not active")

        if login_data.password != VALID_PASSWORD:
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        return {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "token_type": "bearer",
            "user_id": str(DONOR_ID),
            "email": login_data.email,
            "role": "donor",
            "must_change_password": False,
        }


class FakeJWTService:
    async def refresh(self, refresh_token: str):
        if refresh_token == "revoked-refresh":
            raise HTTPException(status_code=401, detail="Refresh token revoked")

        if refresh_token == "access-token":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        if refresh_token != "valid-refresh":
            raise HTTPException(status_code=401, detail="Invalid token")

        return {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "token_type": "bearer",
            "role": "donor",
            "user_id": str(DONOR_ID),
        }

    async def decode_token(self, token: str):
        if token == "access-token":
            return {
                "sub": str(DONOR_ID),
                "role": "donor",
                "type": "access",
                "jti": "access-jti",
            }

        if token == "valid-refresh":
            return {
                "sub": str(DONOR_ID),
                "role": "donor",
                "type": "refresh",
                "jti": "refresh-jti",
                "exp": 9999999999,
            }

        raise HTTPException(status_code=401, detail="Invalid token")


class FakePasswordResetService:
    async def start(self, email: str):
        return {
            "success": True,
            "message": "If email exists, OTP sent",
        }

    async def verify(self, email: str, otp: str):
        if otp in {"0000", "999999"}:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        return {
            "success": True,
            "message": "OTP verified",
        }

    async def complete(self, email: str, new_password: str):
        if email == "expired@gmail.com":
            raise HTTPException(status_code=403, detail="Reset session expired")

        if email == "missing@gmail.com":
            raise HTTPException(status_code=400, detail="User not found")

        return {
            "success": True,
            "message": "Password reset successful",
        }

    async def resend(self, email: str):
        if email == "wait@gmail.com":
            raise HTTPException(
                status_code=429,
                detail="Please wait before requesting new OTP",
            )

        return {
            "success": True,
            "message": "If email exists, new OTP sent",
        }


class FakeProfileService:
    async def get_profile(self, user_id: UUID):
        return UserProfileResponse(
            email="donor@gmail.com",
            full_name="Donor User",
            last_login=None,
        )

    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ):
        if current_password == "wrong-password":
            raise HTTPException(status_code=400, detail="Invalid current password")

        return None


class FakeLogoutService:
    async def logout(self, refresh_token: str):
        if refresh_token == "access-token":
            raise HTTPException(status_code=400, detail="Invalid token type")

        if refresh_token == "invalid-token":
            raise HTTPException(status_code=401, detail="Invalid token")

        return None


class FakeUserService:
    def list_roles(self) -> list[str]:
        return ["donor", "charity", "verifier", "admin"]

    async def list_users(self):
        return [
            make_user(
                user_id=TARGET_USER_ID,
                role="donor",
                email="donor@gmail.com",
            ),
            make_user(
                user_id=uuid4(),
                role="verifier",
                email="verifier@gmail.com",
            ),
        ]

    async def get_user_detail(self, user_id: UUID):
        if user_id == MISSING_USER_ID:
            raise ValueError("User not found")

        return make_user(
            user_id=user_id,
            role="donor",
            email="target@gmail.com",
        )

    async def suspend_user_by_id(self, user_id: UUID, actor_user: FakeUser):
        if user_id == actor_user.user_id:
            raise ValueError("Admin cannot suspend own account")

        if user_id == MISSING_USER_ID:
            raise ValueError("User not found")

        return make_user(
            user_id=user_id,
            role="donor",
            email="target@gmail.com",
            status="suspended",
        )

    async def activate_user_by_id(self, user_id: UUID, actor_user: FakeUser):
        if user_id == MISSING_USER_ID:
            raise ValueError("User not found")

        return make_user(
            user_id=user_id,
            role="donor",
            email="target@gmail.com",
            status="active",
        )

    async def update_user_role(
        self,
        user_id: UUID,
        new_role: str,
        actor_user: FakeUser,
    ):
        if user_id == MISSING_USER_ID:
            raise ValueError("User not found")

        if user_id == actor_user.user_id:
            raise ValueError("Admin cannot change own role")

        return make_user(
            user_id=user_id,
            role=new_role,
            email="target@gmail.com",
        )

    async def create_verifier(self, user_body, actor_user: FakeUser):
        if user_body.email == "exists@gmail.com":
            raise ValueError("A user with this email already exists")

        return user_response_dict(
            email=user_body.email,
            full_name=user_body.full_name,
            role="verifier",
            status_value="active",
            is_verified=True,
        )

    async def complete_verifier_onboarding(
        self,
        token: str,
        new_password: str,
    ):
        if token == "bad-token":
            raise ValueError("Invalid onboarding token")

        return None


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def client(fake_redis: FakeRedis):
    app.dependency_overrides.clear()

    async def override_redis():
        return fake_redis

    async def override_db():
        return FakeDBSession()

    app.dependency_overrides[deps.get_redis_client] = override_redis
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[deps.get_register_service] = lambda: FakeRegisterService()
    app.dependency_overrides[deps.get_login_service] = lambda: FakeLoginService()
    app.dependency_overrides[deps.get_jwt_service] = lambda: FakeJWTService()
    app.dependency_overrides[deps.get_password_reset_service] = (
        lambda: FakePasswordResetService()
    )
    app.dependency_overrides[deps.get_profile_service] = lambda: FakeProfileService()
    app.dependency_overrides[deps.get_logout_service] = lambda: FakeLogoutService()
    app.dependency_overrides[deps.get_user_service] = lambda: FakeUserService()
    app.dependency_overrides[deps.get_current_user] = lambda: make_user(role="donor")

    test_client = TestClient(app)

    yield test_client

    test_client.close()
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {
        "Authorization": "Bearer access-token",
    }


def set_current_user(
    *,
    role: str = "donor",
    user_id: UUID | None = None,
    status_value: str = "active",
    is_verified: bool = True,
) -> FakeUser:
    user = make_user(
        user_id=user_id,
        role=role,
        status=status_value,
        is_verified=is_verified,
    )

    app.dependency_overrides[deps.get_current_user] = lambda: user

    return user