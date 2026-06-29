import time
import uuid

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.metrics import metrics_collector


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.perf_counter()
        client_ip = request.client.host if request.client else "unknown"

        try:
            response = await call_next(request)
            duration_seconds = time.perf_counter() - start_time
            duration_ms = round(duration_seconds * 1000, 2)

            response.headers["X-Request-ID"] = request_id

            metrics_collector.record_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_seconds=duration_seconds,
            )

            logger.bind(request_log=True).info(
                f"request_id={request_id} | "
                f"method={request.method} | "
                f"path={request.url.path} | "
                f"status_code={response.status_code} | "
                f"duration_ms={duration_ms} | "
                f"client_ip={client_ip}"
            )

            return response

        except Exception as error:
            duration_seconds = time.perf_counter() - start_time
            duration_ms = round(duration_seconds * 1000, 2)

            metrics_collector.record_request(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_seconds=duration_seconds,
            )

            logger.bind(request_log=True).exception(
                f"request_id={request_id} | "
                f"method={request.method} | "
                f"path={request.url.path} | "
                f"status_code=500 | "
                f"duration_ms={duration_ms} | "
                f"client_ip={client_ip} | "
                f"error={str(error)}"
            )

            raise