import os
import sys

from loguru import logger


def configure_logger() -> None:
    os.makedirs("logs", exist_ok=True)

    logger.remove()

    json_logging_format = {
        "rotation": "10 MB",
        "retention": "10 days",
        "serialize": True,
    }

    logger.add(
        "logs/media_service_info.log",
        level="INFO",
        filter=lambda record: (
            not record["extra"].get("request_log")
            and not record["extra"].get("audit")
        ),
        **json_logging_format,
    )

    logger.add(
        "logs/media_service_error.log",
        level="ERROR",
        **json_logging_format,
    )

    logger.add(
        "logs/media_request.log",
        level="INFO",
        filter=lambda record: record["extra"].get("request_log") is True,
        **json_logging_format,
    )

    logger.add(
        "logs/media_audit.log",
        level="INFO",
        filter=lambda record: record["extra"].get("audit") is True,
        **json_logging_format,
    )

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    logger.add(sys.stdout, level="INFO", format=log_format)
    logger.add(sys.stderr, level="ERROR", backtrace=True, diagnose=True, format=log_format)