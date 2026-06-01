import random
import string
from typing import Any

from fastapi import Depends, HTTPException, status
from loguru import logger

from app.core.circuit_breaker import CircuitBreakerOpenError
from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.services1.auth_services.email_service import get_email_service


class OTPService:
    def __init__(
        self,
        redis_client: Any = Depends(get_redis_client),
        email_service: Any = Depends(get_email_service),
    ):
        self.redis = redis_client
        self.email_service = email_service
        self.settings = get_settings()

    def _generate_otp(self) -> str:
        return "".join(random.choices(string.digits, k=4))

    async def send_otp(self, email: str) -> str:
        otp = self._generate_otp()

        otp_ttl = int(self.settings.OTP_EXPIRE_TIME)
        await self.redis.setex(f"otp:{email}", otp_ttl, otp)

        subject = "Your OTP Code"
        body = f"Your verification code is: {otp}"

        print(f"OTP for {email}: {otp}")

        try:
            await self.email_service.send_email(
                email,
                subject,
                body,
            )

            logger.info(f"OTP email sent to {email}")
            print(f"OTP email sent to {email}")

        except CircuitBreakerOpenError as error:
            logger.error(
                f"OTP email blocked by circuit breaker | "
                f"email={email} | retry_after={error.retry_after_seconds}s"
            )

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "message": "Email service is temporarily unavailable. Please try again later.",
                    "retry_after_seconds": error.retry_after_seconds,
                },
            )

        except Exception as error:
            logger.error(f"Email sending failed for {email}: {error}")
            print(f"Email sending failed for {email}: {error}")
            print("Using terminal OTP instead.")

        return otp

    async def verify_otp(self, email: str, otp: str) -> bool:
        stored_otp = await self.redis.get(f"otp:{email}")

        if not stored_otp:
            return False

        if isinstance(stored_otp, bytes):
            stored_otp = stored_otp.decode("utf-8")

        if stored_otp == otp:
            await self.redis.delete(f"otp:{email}")
            return True

        return False

    async def check_exist(self, email: str) -> bool:
        exists = await self.redis.exists(f"otp:{email}")
        return exists > 0