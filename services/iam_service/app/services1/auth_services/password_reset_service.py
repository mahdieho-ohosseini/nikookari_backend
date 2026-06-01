from typing import Any
from fastapi import Depends, HTTPException

from app.services1.auth_services.otp_service import OTPService
from app.services1.user_service import UserService
from app.core.redis import get_redis_client
from app.services1.auth_services.hash_service import HashService


class PasswordResetService:
    def __init__(
        self,
        user_service: UserService = Depends(),  # ✅ بدون Annotated
        otp_service: OTPService = Depends(),    # ✅ بدون Annotated
        redis_client: Any = Depends(get_redis_client),  # ✅ بدون Annotated
        hash_service: HashService = Depends(),  # ✅ بدون Annotated
    ):
        self.user_service = user_service
        self.otp_service = otp_service
        self.redis = redis_client
        self.hash_service = hash_service

    async def start(self, email: str):
        user = await self.user_service.get_user_by_email(email)

        if user:
            await self.otp_service.send_otp(email)

        return {
            "success": True,
            "message": "If email exists, OTP sent"
        }

    async def verify(self, email: str, otp: str):
        valid = await self.otp_service.verify_otp(email, otp)
        if not valid:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        await self.redis.setex(
            f"reset_session:{email}",
            600,
            "1"
        )

        return {
            "success": True,
            "message": "OTP verified"
        }
    

    async def complete(self, email: str, new_password: str):
     exists = await self.redis.exists(f"reset_session:{email}")
     if not exists:
        raise HTTPException(status_code=403, detail="Reset session expired")

     user = await self.user_service.get_user_by_email(email)
     if not user:
        raise HTTPException(status_code=400, detail="User not found")

    # ✅ hashing استاندارد

    # ✅ استفاده از user_id (نه id)
     await self.user_service.update_password(user.user_id, new_password)
     await self.user_service.invalidate_all_tokens(user.user_id)
 
     await self.redis.delete(f"reset_session:{email}")

     return {
         "success": True,
        "message": "Password reset successful"
      }
    async def resend(self, email: str):
     """
    ارسال مجدد OTP با محدودیت زمانی
    """
     from loguru import logger
    
     user = await self.user_service.get_user_by_email(email)
    
     if user:
        # چک کن OTP قبلی هنوز معتبره؟
        ttl = await self.redis.ttl(f"otp:{email}")
        
        if ttl > 60:  # اگر بیشتر از 60 ثانیه مونده
            logger.warning(f"⚠️ OTP still valid for {email}, {ttl}s remaining")
            raise HTTPException(
                status_code=429,  # Too Many Requests
                detail=f"Please wait {ttl} seconds before requesting new OTP"
            )
        
        # OTP منقضی شده یا کمتر از 60 ثانیه مونده - بفرست
        await self.otp_service.send_otp(email)
        logger.info(f"✅ OTP resent to: {email}")
     else:
        logger.warning(f"⚠️ Resend attempted for non-existent: {email}")
    
     return {
        "success": True,
        "message": "If email exists, new OTP sent"
    }

    