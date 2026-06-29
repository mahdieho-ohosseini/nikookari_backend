from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.core.metrics import metrics_collector, render_circuit_breaker_metrics
from app.services.payment_provider import payment_provider


monitoring_router = APIRouter(tags=["Monitoring"])


@monitoring_router.get(
    "/metrics",
    response_class=PlainTextResponse,
    summary="Core Service Metrics",
)
async def get_metrics():
    zarinpal_state = payment_provider.circuit_breaker.get_state()

    return (
        metrics_collector.render_prometheus_metrics()
        + "\n"
        + render_circuit_breaker_metrics(zarinpal_state)
    )