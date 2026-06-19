from functools import lru_cache
from pathlib import Path

from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # Database
    DATABASE_DIALECT: str
    DATABASE_HOSTNAME: str
    DATABASE_NAME: str
    DATABASE_PASSWORD: str
    DATABASE_PORT: int
    DATABASE_USERNAME: str

    # Project
    PROJECT_NAME: str = "Nikookari Media Service"
    PROJECT_VERSION: str = "1.0.0"

    # Auth - must match IAM/Core JWT settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    # Storage
    STORAGE_BACKEND: str = "local"
    UPLOAD_DIR: str = "static/uploads"

    # Global
    DEBUG_MODE: bool = True

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
    )


@lru_cache
@logger.catch
def get_settings() -> Settings:
    return Settings()
