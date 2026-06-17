import re
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, field_validator, constr


# ======================================================
# Shared Role Literal
# ======================================================

UserRoleLiteral = Literal["donor", "charity", "verifier", "admin"]


# ======================================================
# Base User Schemas
# ======================================================

class UserBaseSchema(BaseModel):
    full_name: str
    email: EmailStr


class UserCreateSchema(UserBaseSchema):
    password: constr(min_length=8, max_length=64)  # type: ignore[arg-type]

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, email: str):
        allowed_domains = {
            "gmail.com",
            "yahoo.com",
            "outlook.com",
            "hotmail.com",
            "icloud.com",
            "live.com",
        }

        blocked_domains = {
            "example.com",
            "test.com",
            "fake.com",
            "mailinator.com",
        }

        domain = email.split("@")[-1].lower()

        if domain in blocked_domains:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="دامنه ایمیل مجاز نیست.",
            )

        if domain not in allowed_domains:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"دامنه '{domain}' معتبر شناخته نشد. لطفاً از ایمیل معتبر استفاده کنید.",
            )

        return email

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, password: str):
        errors = []

        if not re.search(r"[A-Z]", password):
            errors.append("یک حرف بزرگ (A-Z)")

        if not re.search(r"[a-z]", password):
            errors.append("یک حرف کوچک (a-z)")

        if not re.search(r"[0-9]", password):
            errors.append("یک عدد (0-9)")

        if not re.search(r"[@$!%*?&.#^_+=-]", password):
            errors.append("یک کاراکتر خاص مثل @, #, !, %")

        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"رمز عبور باید شامل {('، '.join(errors))} باشد.",
            )

        return password


# ======================================================
# Login & User Response
# ======================================================

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserResponseSchema(BaseModel):
    user_id: UUID
    full_name: str
    email: EmailStr
    role: UserRoleLiteral
    status: str
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    is_verified: bool
    onboarding_token: Optional[str] = None
    onboarding_link: Optional[str] = None

    class Config:
        from_attributes = True


class UserRoleUpdateSchema(BaseModel):
    role: UserRoleLiteral


class RoleResponseSchema(BaseModel):
    roles: list[UserRoleLiteral]


# ======================================================
# Admin / ARBAC Schemas
# ======================================================

class CreateVerifierSchema(BaseModel):
    full_name: str
    email: EmailStr



# ======================================================
# OTP-Based Registration
# ======================================================

class RegisterStartResponse(BaseModel):
    success: bool
    message: str


class RegisterCompleteSchema(BaseModel):
    email: EmailStr
    otp: str


class RegisterCompleteResponse(BaseModel):
    success: bool
    verified: bool
    message: str
    user: UserResponseSchema


class ResendOTPSchema(BaseModel):
    email: EmailStr


class ResendOTPResponseSchema(BaseModel):
    success: bool
    message: str

class CompleteOnboardingSchema(BaseModel):
    token: str
    new_password: str
