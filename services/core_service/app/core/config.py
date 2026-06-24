from functools import lru_cache
from pathlib import Path

from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    DATABASE_DIALECT: str
    DATABASE_HOSTNAME: str
    DATABASE_NAME: str
    DATABASE_PASSWORD: str
    DATABASE_PORT: int
    DATABASE_USERNAME: str

    PROJECT_NAME: str = "Nikookari Core Service"
    PROJECT_VERSION: str = "1.0.0"

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str

    IAM_URL: str
    ZARINPAL_MERCHANT_ID: str

    # آدرس media_service برای ساخت لینک فایل‌ها
    MEDIA_SERVICE_URL: str = "http://127.0.0.1:8003"

    DEBUG_MODE: bool

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
    )


@lru_cache
@logger.catch
def get_settings():
    return Settings()