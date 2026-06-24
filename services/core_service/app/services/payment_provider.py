import uuid
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

import requests
from fastapi import HTTPException, status

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
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail={
                        "message": "Zarinpal request failed",
                        "status_code": response.status_code,
                        "payload": payload,
                        "zarinpal_response": result,
                    },
                )

        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Zarinpal request failed: {str(exc)}",
            )

        data = result.get("data") or {}
        authority = data.get("authority")
        code = data.get("code")

        if code != 100 or not authority:
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
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail={
                        "message": "Zarinpal verify failed",
                        "status_code": response.status_code,
                        "payload": payload,
                        "zarinpal_response": result,
                    },
                )

        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Zarinpal verify failed: {str(exc)}",
            )

        data = result.get("data") or {}
        code = data.get("code")

        if code in [100, 101]:
            return str(data.get("ref_id") or uuid.uuid4())

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Zarinpal payment verification failed",
                "payload": payload,
                "zarinpal_response": result,
            },
        )


payment_provider = ZarinpalPaymentProvider()