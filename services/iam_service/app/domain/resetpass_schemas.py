from pydantic import BaseModel, EmailStr, constr

class PasswordResetStartSchema(BaseModel):
    email: EmailStr


class PasswordResetVerifySchema(BaseModel):
    email: EmailStr
    otp: constr(min_length=4, max_length=6)  # type: ignore


class PasswordResetCompleteSchema(BaseModel):
    email: EmailStr
    new_password: constr(min_length=8) # type: ignore


# ✅ Response مشترک
class PasswordResetResponseSchema(BaseModel):
    success: bool
    message: str

class PasswordResetResendSchema(BaseModel):
    email: EmailStr
