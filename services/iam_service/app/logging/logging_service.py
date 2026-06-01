import sys
from pathlib import Path

from loguru import logger


def configure_logger() -> None:
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    logger.remove()

    logger.add(
        sys.stdout,
        level="INFO",
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    logger.add(
        logs_dir / "iam_service_info.log",
        level="INFO",
        rotation="5 MB",
        retention="7 days",
        encoding="utf-8",
        enqueue=True,
        filter=lambda record: (
            not record["extra"].get("request_log")
            and not record["extra"].get("audit")
        ),
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level} | "
            "{name}:{function}:{line} | {message}"
        ),
    )

    logger.add(
        logs_dir / "iam_service_error.log",
        level="ERROR",
        rotation="5 MB",
        retention="14 days",
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=False,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level} | "
            "{name}:{function}:{line} | {message}"
        ),
    )

    logger.add(
        logs_dir / "iam_request.log",
        level="INFO",
        rotation="5 MB",
        retention="7 days",
        encoding="utf-8",
        enqueue=True,
        filter=lambda record: record["extra"].get("request_log") is True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
    )

    logger.add(
        logs_dir / "iam_security_audit.log",
        level="INFO",
        rotation="5 MB",
        retention="30 days",
        encoding="utf-8",
        enqueue=True,
        filter=lambda record: record["extra"].get("audit") is True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
    )

    logger.info("Logger configured successfully.")