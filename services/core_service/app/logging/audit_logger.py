from typing import Any

from loguru import logger


def audit_log(
    *,
    event: str,
    outcome: str,
    actor_id: str | None = None,
    actor_role: str | None = None,
    target_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    logger.bind(audit=True).info(
        "event={} | outcome={} | actor_id={} | actor_role={} | "
        "target_id={} | details={}",
        event,
        outcome,
        actor_id,
        actor_role,
        target_id,
        details or {},
    )