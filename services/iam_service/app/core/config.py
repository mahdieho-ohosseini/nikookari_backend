from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # Database
    DATABASE_DIALECT: str
    DATABASE_HOSTNAME: str
    DATABASE_NAME: str
    DATABASE_PASSWORD: str
    DATABASE_PORT: int
    DATABASE_USERNAME: str
    #Email service

    EMAIL_FROM: str = "your@email.com"
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: str = "your@gmail.com"
    EMAIL_PASSWORD: str = "your app password"
    # Project
    PROJECT_NAME: str = "QForm IAM Service"
    PROJECT_VERSION: str = "1.0.0"

    # Global settings
    DEBUG_MODE: bool

    # Redis
    REDIS_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS  : int=10
    # OTP
    OTP_EXPIRE_TIME: int

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8"
    )


@lru_cache
@logger.catch
def get_settings() -> Settings:
    return Settings()
