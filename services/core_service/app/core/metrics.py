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
                "# HELP core_service_uptime_seconds Core service uptime in seconds",
                "# TYPE core_service_uptime_seconds gauge",
                f"core_service_uptime_seconds {uptime_seconds}",
                "",
                "# HELP core_http_requests_total Total HTTP requests",
                "# TYPE core_http_requests_total counter",
                f"core_http_requests_total {self.total_requests}",
                "",
                "# HELP core_http_errors_total Total HTTP 5xx errors",
                "# TYPE core_http_errors_total counter",
                f"core_http_errors_total {self.total_errors}",
                "",
                "# HELP core_http_request_duration_seconds_total Total request duration in seconds",
                "# TYPE core_http_request_duration_seconds_total counter",
                f"core_http_request_duration_seconds_total {round(self.total_duration_seconds, 6)}",
                "",
                "# HELP core_http_request_duration_seconds_average Average request duration in seconds",
                "# TYPE core_http_request_duration_seconds_average gauge",
                f"core_http_request_duration_seconds_average {round(average_duration, 6)}",
                "",
                "# HELP core_http_requests_by_route_total Total requests grouped by route",
                "# TYPE core_http_requests_by_route_total counter",
            ]

            for route_key, count in self.requests_by_route.items():
                method, path = route_key.split(" ", 1)
                lines.append(
                    f'core_http_requests_by_route_total{{method="{method}",path="{path}"}} {count}'
                )

            lines.extend(
                [
                    "",
                    "# HELP core_http_requests_by_status_total Total requests grouped by status code",
                    "# TYPE core_http_requests_by_status_total counter",
                ]
            )

            for status_code, count in self.requests_by_status.items():
                lines.append(
                    f'core_http_requests_by_status_total{{status_code="{status_code}"}} {count}'
                )

            lines.extend(
                [
                    "",
                    "# HELP core_http_request_duration_by_route_seconds_total Total duration grouped by route",
                    "# TYPE core_http_request_duration_by_route_seconds_total counter",
                ]
            )

            for route_key, duration in self.duration_by_route.items():
                method, path = route_key.split(" ", 1)
                lines.append(
                    f'core_http_request_duration_by_route_seconds_total{{method="{method}",path="{path}"}} {round(duration, 6)}'
                )

            return "\n".join(lines) + "\n"


metrics_collector = MetricsCollector()


def render_circuit_breaker_metrics(
    state: dict,
    *,
    metric_prefix: str = "core",
) -> str:
    service = str(state.get("service", "unknown"))
    circuit_state = str(state.get("state", "unknown"))
    failures = int(state.get("failures", 0))
    failure_threshold = int(state.get("failure_threshold", 0))
    retry_after_seconds = int(state.get("retry_after_seconds", 0))
    is_open = 1 if circuit_state == "open" else 0

    lines = [
        f"# HELP {metric_prefix}_circuit_breaker_open Circuit breaker open state",
        f"# TYPE {metric_prefix}_circuit_breaker_open gauge",
        f'{metric_prefix}_circuit_breaker_open{{service="{service}"}} {is_open}',
        "",
        f"# HELP {metric_prefix}_circuit_breaker_failures Current circuit breaker failure count",
        f"# TYPE {metric_prefix}_circuit_breaker_failures gauge",
        f'{metric_prefix}_circuit_breaker_failures{{service="{service}"}} {failures}',
        "",
        f"# HELP {metric_prefix}_circuit_breaker_failure_threshold Circuit breaker failure threshold",
        f"# TYPE {metric_prefix}_circuit_breaker_failure_threshold gauge",
        f'{metric_prefix}_circuit_breaker_failure_threshold{{service="{service}"}} {failure_threshold}',
        "",
        f"# HELP {metric_prefix}_circuit_breaker_retry_after_seconds Circuit breaker retry-after seconds",
        f"# TYPE {metric_prefix}_circuit_breaker_retry_after_seconds gauge",
        f'{metric_prefix}_circuit_breaker_retry_after_seconds{{service="{service}"}} {retry_after_seconds}',
    ]

    return "\n".join(lines) + "\n"