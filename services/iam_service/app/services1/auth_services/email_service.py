import asyncio
import smtplib
from email.header import Header
from email.mime.text import MIMEText

from loguru import logger
from redis.asyncio import Redis

from app.core.circuit_breaker import CircuitBreaker
from app.core.config import get_settings
from app.services1.base_service import BaseService
from app.core.redis import get_redis


class EmailService(BaseService):
    def __init__(self, redis_client: Redis):
        super().__init__()
        self.settings = get_settings()
        self.redis = redis_client
        self.circuit_breaker = CircuitBreaker(
            redis_client=self.redis,
            name="email_service",
            failure_threshold=3,
            recovery_timeout_seconds=120,
            failure_window_seconds=300,
        )

    async def send_email(self, to_email: str, subject: str, body: str) -> None:
        await self.circuit_breaker.before_call()

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = str(Header(subject, "utf-8"))
        msg["From"] = self.settings.EMAIL_FROM
        msg["To"] = to_email

        def _send() -> None:
            email_host = self.settings.EMAIL_HOST
            email_port = int(self.settings.EMAIL_PORT)
            email_username = self.settings.EMAIL_USERNAME
            email_password = self.settings.EMAIL_PASSWORD.strip()
            email_from = self.settings.EMAIL_FROM

            if email_port == 465:
                with smtplib.SMTP_SSL(email_host, email_port, timeout=30) as smtp:
                    smtp.login(email_username, email_password)
                    smtp.sendmail(email_from, [to_email], msg.as_string())
            else:
                with smtplib.SMTP(email_host, email_port, timeout=30) as smtp:
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.ehlo()
                    smtp.login(email_username, email_password)
                    smtp.sendmail(email_from, [to_email], msg.as_string())

        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _send)
            await self.circuit_breaker.record_success()
            logger.info(f"Email sent successfully | to={to_email}")
        except Exception as error:
            await self.circuit_breaker.record_failure()
            logger.error(f"Email sending failed | to={to_email} | error={error}")
            raise

    async def send_verifier_welcome_email(
        self,
        email: str,
        full_name: str,
        onboarding_link: str,
    ) -> None:
        subject = "Welcome to Rahe Nikookari"
        body = f"""
               Hello {full_name},
               
               Your verifier account has been created.
               
               Please complete your account setup using the link below:
               
               {onboarding_link}
               
               This link expires in 24 hours.
               
               Regards,
               Rahe Nikookari Team
               """.strip()
               
        await self.send_email(
            to_email=email,
            subject=subject,
            body=body,
        )


async def get_email_service() -> EmailService:
    redis_client = await get_redis()
    return EmailService(redis_client=redis_client)

