import uuid
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass
class PaymentRequestResult:
    authority: str
    payment_url: str
    callback_url: str


class MockPaymentProvider:
    """
    فعلاً به جای زرین‌پال واقعی استفاده می‌شود.
    بعداً فقط همین provider با ZarinpalProvider عوض می‌شود و API/DB ثابت می‌ماند.
    """

    provider_name = "mock"

    def create_payment(
        self,
        *,
        transaction_id: UUID,
        amount: Decimal,
        callback_url: str,
        base_url: str,
    ) -> PaymentRequestResult:
        authority = f"MOCK-{transaction_id}-{uuid.uuid4().hex[:8]}"
        base = base_url.rstrip("/")
        payment_url = f"{base}/api/v1/payments/mock/{transaction_id}/success"
        return PaymentRequestResult(
            authority=authority,
            payment_url=payment_url,
            callback_url=callback_url,
        )

    def verify_payment(self, *, authority: str, amount: Decimal) -> str:
        return f"MOCK-REF-{uuid.uuid4().hex[:12].upper()}"


payment_provider = MockPaymentProvider()
