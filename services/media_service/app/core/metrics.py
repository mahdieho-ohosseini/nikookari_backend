import time
from collections import defaultdict
from threading import Lock


class MetricsCollector:
    def __init__(self) -> None:
        self._lock = Lock()
        self.started_at = time.time()

        self.total_requests = 0
        self.total_errors = 0
        self.total_duration_seconds = 0.0

        self.requests_by_route = defaultdict(int)
        self.requests_by_status = defaultdict(int)
        self.duration_by_route = defaultdict(float)

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        route_key = f"{method} {path}"
        status_key = str(status_code)

        with self._lock:
            self.total_requests += 1
            self.total_duration_seconds += duration_seconds
            self.requests_by_route[route_key] += 1
            self.requests_by_status[status_key] += 1
            self.duration_by_route[route_key] += duration_seconds

            if status_code >= 500:
                self.total_errors += 1

    def render_prometheus_metrics(self) -> str:
        with self._lock:
            uptime_seconds = round(time.time() - self.started_at, 3)
            average_duration = 0.0

            if self.total_requests > 0:
                average_duration = self.total_duration_seconds / self.total_requests

            lines = [
                "# HELP media_service_uptime_seconds Media service uptime in seconds",
                "# TYPE media_service_uptime_seconds gauge",
                f"media_service_uptime_seconds {uptime_seconds}",
                "",
                "# HELP media_http_requests_total Total HTTP requests",
                "# TYPE media_http_requests_total counter",
                f"media_http_requests_total {self.total_requests}",
                "",
                "# HELP media_http_errors_total Total HTTP 5xx errors",
                "# TYPE media_http_errors_total counter",
                f"media_http_errors_total {self.total_errors}",
                "",
                "# HELP media_http_request_duration_seconds_total Total request duration in seconds",
                "# TYPE media_http_request_duration_seconds_total counter",
                f"media_http_request_duration_seconds_total {round(self.total_duration_seconds, 6)}",
                "",
                "# HELP media_http_request_duration_seconds_average Average request duration in seconds",
                "# TYPE media_http_request_duration_seconds_average gauge",
                f"media_http_request_duration_seconds_average {round(average_duration, 6)}",
                "",
                "# HELP media_http_requests_by_route_total Total requests grouped by route",
                "# TYPE media_http_requests_by_route_total counter",
            ]

            for route_key, count in self.requests_by_route.items():
                method, path = route_key.split(" ", 1)
                lines.append(
                    f'media_http_requests_by_route_total{{method="{method}",path="{path}"}} {count}'
                )

            lines.extend(
                [
                    "",
                    "# HELP media_http_requests_by_status_total Total requests grouped by status code",
                    "# TYPE media_http_requests_by_status_total counter",
                ]
            )

            for status_code, count in self.requests_by_status.items():
                lines.append(
                    f'media_http_requests_by_status_total{{status_code="{status_code}"}} {count}'
                )

            return "\n".join(lines) + "\n"


metrics_collector = MetricsCollector()