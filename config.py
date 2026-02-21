"""Configuration file loading environment data"""

from typing import Any

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # Application
    APP_NAME: str = "habit-tracker"
    SECRET_KEY: str
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    VERSION: str = "2.0"

    # Admin credentials (for initial setup)
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str

    # JWT setting
    JWT_SECRET_KEY: str | None = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # AWS
    AWS_REGION: str = "eu-central-1"
    AWS_SQS_STACK_NAME: str
    AWS_S3_BUCKET_NAME: str
    AWS_SES_SENDER_EMAIL: str
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str

    # AI
    OLLAMA_URL: str

    @classmethod
    @field_validator("JWT_SECRET_KEY", mode="before")
    def set_jwt_secret(cls, v: str | None, info: ValidationInfo) -> str | Any | None:
        """Use SECRET_KEY if JWT_SECRET_KEY not provided"""
        return v or info.data.get("SECRET_KEY")

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
