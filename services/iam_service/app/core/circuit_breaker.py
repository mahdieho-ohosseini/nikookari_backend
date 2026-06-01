import time
from dataclasses import dataclass

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
        redis_client,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout_seconds: int = 120,
        failure_window_seconds: int = 300,
    ):
        self.redis = redis_client
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.failure_window_seconds = failure_window_seconds

        self.failure_key = f"circuit_breaker:{self.name}:failures"
        self.opened_until_key = f"circuit_breaker:{self.name}:opened_until"

    async def _reset(self) -> None:
        await self.redis.delete(self.failure_key)
        await self.redis.delete(self.opened_until_key)

        logger.info(f"Circuit breaker reset | service={self.name}")

    async def before_call(self) -> None:
        opened_until = await self.redis.get(self.opened_until_key)

        if not opened_until:
            return

        now = int(time.time())

        try:
            opened_until = int(opened_until)
        except ValueError:
            await self._reset()
            return

        if opened_until > now:
            retry_after = opened_until - now

            logger.warning(
                f"Circuit breaker is OPEN | service={self.name} | "
                f"retry_after={retry_after}s"
            )

            raise CircuitBreakerOpenError(
                service_name=self.name,
                retry_after_seconds=retry_after,
            )

        # Recovery time passed, so close the circuit and clear old failures.
        await self._reset()

    async def record_success(self) -> None:
        await self._reset()

        logger.info(f"Circuit breaker reset after success | service={self.name}")

    async def record_failure(self) -> None:
        failure_count = await self.redis.incr(self.failure_key)

        if failure_count == 1:
            await self.redis.expire(self.failure_key, self.failure_window_seconds)

        logger.warning(
            f"Circuit breaker failure recorded | service={self.name} | "
            f"failures={failure_count}/{self.failure_threshold}"
        )

        if failure_count >= self.failure_threshold:
            opened_until = int(time.time()) + self.recovery_timeout_seconds

            await self.redis.setex(
                self.opened_until_key,
                self.recovery_timeout_seconds,
                opened_until,
            )

            logger.error(
                f"Circuit breaker OPENED | service={self.name} | "
                f"recovery_timeout={self.recovery_timeout_seconds}s"
            )

    async def get_state(self) -> dict:
        opened_until = await self.redis.get(self.opened_until_key)
        failures = await self.redis.get(self.failure_key)

        now = int(time.time())
        retry_after = 0
        state = "closed"

        if opened_until:
            try:
                opened_until_int = int(opened_until)

                if opened_until_int > now:
                    state = "open"
                    retry_after = opened_until_int - now
                else:
                    # Recovery time passed, so clean stale failure count.
                    await self._reset()
                    failures = 0

            except ValueError:
                await self._reset()
                failures = 0

        return {
            "service": self.name,
            "state": state,
            "failures": int(failures or 0),
            "failure_threshold": self.failure_threshold,
            "retry_after_seconds": retry_after,
        }