import json
from typing import Any

from loguru import logger


def audit_log(
    event: str,
    outcome: str,
    actor_id: str | None = None,
    actor_email: str | None = None,
    actor_role: str | None = None,
    target_id: str | None = None,
    target_email: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    payload = {
        "event": event,
        "outcome": outcome,
        "actor_id": actor_id,
        "actor_email": actor_email,
        "actor_role": actor_role,
        "target_id": target_id,
        "target_email": target_email,
        "details": details or {},
    }

    logger.bind(audit=True).info(
        json.dumps(payload, ensure_ascii=False)
    )