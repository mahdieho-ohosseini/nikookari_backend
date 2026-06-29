import uuid
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

import requests
from fastapi import HTTPException, status
from loguru import logger

from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from app.core.config import get_settings


@dataclass
class PaymentRequestResult:
    authority: str
    payment_url: str
    callback_url: str


class ZarinpalPaymentProvider:
    provider_name = "zarinpal"

    REQUEST_URL = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
    VERIFY_URL = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
    STARTPAY_URL = "https://sandbox.zarinpal.com/pg/StartPay/"
    circuit_breaker = CircuitBreaker(name="zarinpal")

    def _log_payment_error(
        self,
        *,
        operation: str,
        message: str,
        transaction_id: UUID | None = None,
        authority: str | None = None,
        status_code: int | None = None,
        error: str | None = None,
    ) -> None:
        logger.bind(payment_error=True).error(
            "provider={} | operation={} | message={} | transaction_id={} | "
            "authority={} | status_code={} | error={} | circuit_breaker={}",
            self.provider_name,
            operation,
            message,
            transaction_id,
            authority,
            status_code,
            error,
            self.circuit_breaker.get_state(),
        )

    def create_payment(
        self,
        *,
        transaction_id: UUID,
        amount: Decimal,
        callback_url: str,
        base_url: str,
    ) -> PaymentRequestResult:
        settings = get_settings()

        payload = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "amount": int(amount),
            "callback_url": callback_url,
            "description": f"Nikookari donation payment {transaction_id}",
        }

        try:
            self.circuit_breaker.before_call()

            response = requests.post(
                self.REQUEST_URL,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=20,
            )

            result = response.json()

            if response.status_code >= 400:
                self.circuit_breaker.record_failure()
                self._log_payment_error(
                    operation="create_payment",
                    message="Zarinpal request returned upstream HTTP error",
                    transaction_id=transaction_id,
                    status_code=response.status_code,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail={
                        "message": "Zarinpal request failed",
                        "status_code": response.status_code,
                        "payload": payload,
                        "zarinpal_response": result,
                    },
                )

            self.circuit_breaker.record_success()

        except HTTPException:
            raise

        except CircuitBreakerOpenError as exc:
            self._log_payment_error(
                operation="create_payment",
                message="Circuit breaker blocked Zarinpal request",
                transaction_id=transaction_id,
                error=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Zarinpal request failed: {str(exc)}",
            )

        except Exception as exc:
            self.circuit_breaker.record_failure()
            self._log_payment_error(
                operation="create_payment",
                message="Zarinpal request failed with exception",
                transaction_id=transaction_id,
                error=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Zarinpal request failed: {str(exc)}",
            )

        data = result.get("data") or {}
        authority = data.get("authority")
        code = data.get("code")

        if code != 100 or not authority:
            self._log_payment_error(
                operation="create_payment",
                message="Zarinpal payment request was not successful",
                transaction_id=transaction_id,
                error=f"code={code}, authority={authority}",
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Zarinpal payment request was not successful",
                    "payload": payload,
                    "zarinpal_response": result,
                },
            )

        return PaymentRequestResult(
            authority=authority,
            payment_url=f"{self.STARTPAY_URL}{authority}",
            callback_url=callback_url,
        )

    def verify_payment(self, *, authority: str, amount: Decimal) -> str:
        settings = get_settings()

        payload = {
            "merchant_id": settings.ZARINPAL_MERCHANT_ID,
            "authority": authority,
            "amount": int(amount),
        }

        try:
            self.circuit_breaker.before_call()

            response = requests.post(
                self.VERIFY_URL,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=20,
            )

            result = response.json()

            if response.status_code >= 400:
                self.circuit_breaker.record_failure()
                self._log_payment_error(
                    operation="verify_payment",
                    message="Zarinpal verify returned upstream HTTP error",
                    authority=authority,
                    status_code=response.status_code,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail={
                        "message": "Zarinpal verify failed",
                        "status_code": response.status_code,
                        "payload": payload,
                        "zarinpal_response": result,
                    },
                )

            self.circuit_breaker.record_success()

        except HTTPException:
            raise

        except CircuitBreakerOpenError as exc:
            self._log_payment_error(
                operation="verify_payment",
                message="Circuit breaker blocked Zarinpal verify",
                authority=authority,
                error=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Zarinpal verify failed: {str(exc)}",
            )

        except Exception as exc:
            self.circuit_breaker.record_failure()
            self._log_payment_error(
                operation="verify_payment",
                message="Zarinpal verify failed with exception",
                authority=authority,
                error=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Zarinpal verify failed: {str(exc)}",
            )

        data = result.get("data") or {}
        code = data.get("code")

        if code in [100, 101]:
            return str(data.get("ref_id") or uuid.uuid4())

        self._log_payment_error(
            operation="verify_payment",
            message="Zarinpal payment verification failed",
            authority=authority,
            error=f"code={code}",
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Zarinpal payment verification failed",
                "payload": payload,
                "zarinpal_response": result,
            },
        )


payment_provider = ZarinpalPaymentProvider()