import time
from dataclasses import dataclass
from threading import Lock

from loguru import logger


@dataclass
class CircuitBreakerOpenError(Exception):
    service_name: str
    retry_after_seconds: int

    def __str__(self) -> str:
        return (
            f"Circuit breaker is open for {self.service_name}. "
            f"Retry after {self.retry_after_seconds} seconds."
        )


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout_seconds: int = 120,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self._failure_count = 0
        self._opened_until = 0.0
        self._lock = Lock()

    def before_call(self) -> None:
        with self._lock:
            now = time.time()

            if self._opened_until <= now:
                if self._opened_until:
                    self._reset_locked()
                return

            retry_after = int(self._opened_until - now)
            logger.warning(
                f"Circuit breaker is OPEN | service={self.name} | "
                f"retry_after={retry_after}s"
            )
            raise CircuitBreakerOpenError(
                service_name=self.name,
                retry_after_seconds=retry_after,
            )

    def record_success(self) -> None:
        with self._lock:
            self._reset_locked()
            logger.info(f"Circuit breaker reset after success | service={self.name}")

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            logger.warning(
                f"Circuit breaker failure recorded | service={self.name} | "
                f"failures={self._failure_count}/{self.failure_threshold}"
            )

            if self._failure_count >= self.failure_threshold:
                self._opened_until = time.time() + self.recovery_timeout_seconds
                logger.error(
                    f"Circuit breaker OPENED | service={self.name} | "
                    f"recovery_timeout={self.recovery_timeout_seconds}s"
                )

    def get_state(self) -> dict:
        with self._lock:
            now = time.time()
            retry_after = 0
            state = "closed"

            if self._opened_until > now:
                state = "open"
                retry_after = int(self._opened_until - now)
            elif self._opened_until:
                self._reset_locked()

            return {
                "service": self.name,
                "state": state,
                "failures": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "retry_after_seconds": retry_after,
            }

    def _reset_locked(self) -> None:
        self._failure_count = 0
        self._opened_until = 0.0