from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.core.circuit_breaker import CircuitBreaker
from app.core.database import get_db
from app.dependencies import get_redis_client


health_router = APIRouter(
    tags=["Health Check"],
)


@health_router.get(
    "/health",
    summary="IAM Service Health Check",
)
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    health_status = {
        "service": "iam-service",
        "status": "ok",
        "database": "connected",
        "redis": "connected",
        "email_circuit_breaker": {
            "service": "email_service",
            "state": "closed",
        },
    }

    http_status = status.HTTP_200_OK

    try:
        await db.execute(text("SELECT 1"))
        logger.info("Health check: database is connected")
    except Exception as error:
        logger.error(f"Health check failed: database error: {error}")
        health_status["database"] = "disconnected"
        health_status["status"] = "degraded"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    try:
        await redis_client.ping()
        logger.info("Health check: redis is connected")
    except Exception as error:
        logger.error(f"Health check failed: redis error: {error}")
        health_status["redis"] = "disconnected"
        health_status["status"] = "degraded"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    try:
        email_circuit_breaker = CircuitBreaker(
            redis_client=redis_client,
            name="email_service",
            failure_threshold=3,
            recovery_timeout_seconds=120,
            failure_window_seconds=300,
        )

        circuit_state = await email_circuit_breaker.get_state()
        health_status["email_circuit_breaker"] = circuit_state

        if circuit_state["state"] == "open":
            health_status["status"] = "degraded"
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE

    except Exception as error:
        logger.error(f"Health check failed: circuit breaker status error: {error}")
        health_status["email_circuit_breaker"] = {
            "service": "email_service",
            "state": "unknown",
        }

    return JSONResponse(
        status_code=http_status,
        content=health_status,
    )