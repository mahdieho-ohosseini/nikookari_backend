from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    email: str | None = None
    role: str
    must_change_password: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str


    
#برای decode کردن JWT و استخراج user_id
class TokenDataSchema(BaseModel):
    user_id : int
    is_admin :bool
    is_verified: bool = False


class LogoutRequest(BaseModel):
    refresh_token: str

    