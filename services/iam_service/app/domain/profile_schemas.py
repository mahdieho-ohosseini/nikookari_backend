from uuid import UUID  # ← این خط رو نداری!
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from datetime import datetime
import re


# =========================
# Response: Profile
# =========================
class UserProfileResponse(BaseModel):
    email: str
    full_name: str | None = None
    last_login: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# =========================
# Request: Change Password
# =========================
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

    model_config = ConfigDict(extra="forbid")

    # 🔐 Password Strength
    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str):
        if not re.search(r"[A-Z]", v):
            raise ValueError("رمز عبور باید حداقل یک حرف بزرگ (A-Z) داشته باشد")
        if not re.search(r"[a-z]", v):
            raise ValueError("رمز عبور باید حداقل یک حرف کوچک (a-z) داشته باشد")
        if not re.search(r"\d", v):
            raise ValueError("رمز عبور باید حداقل یک عدد (0-9) داشته باشد")
        if not re.search(r"[@$!%*?&.#^_+=-]", v):
            raise ValueError("رمز عبور باید حداقل یک کاراکتر خاص مثل @، #، ! داشته باشد")
        return v

    # ✅ Confirm Password Check
    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("رمز عبور و تکرار آن یکسان نیستند")
        return self


# =========================
# Simple success response
# =========================
class SimpleSuccessResponse(BaseModel):
    success: bool = True
    message: str



class MembershipInfoResponse(BaseModel):
    created_at: datetime
    member_since_gregorian: int
    member_since_jalali: int

    class Config:
        from_attributes = True