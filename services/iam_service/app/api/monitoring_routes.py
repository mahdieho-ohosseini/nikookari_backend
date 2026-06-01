from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.core.metrics import metrics_collector


monitoring_router = APIRouter(
    tags=["Monitoring"],
)


@monitoring_router.get(
    "/metrics",
    response_class=PlainTextResponse,
    summary="IAM Service Metrics",
)
async def get_metrics():
    return metrics_collector.render_prometheus_metrics()