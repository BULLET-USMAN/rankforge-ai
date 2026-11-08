from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized configuration for RankForge AI backend.
    Loads from environment variables or falls back to secure defaults.
    """
    PROJECT_NAME: str = "RankForge AI API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "rf_dev_secret_key_change_in_production_894172498172938471"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v  # type: ignore
        raise ValueError(v)

    # Database
    DATABASE_URL: str = (
        "postgresql+psycopg://rankforge:rankforge_dev_password@localhost:5432/rankforge_db"
    )

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Crawler & Preflight SSRF Safeguards
    CRAWLER_MAX_RESPONSE_BYTES: int = 5 * 1024 * 1024  # 5MB
    CRAWLER_TIMEOUT_SECONDS: float = 10.0
    CRAWLER_MAX_REDIRECTS: int = 3
    MAX_REQUEST_BODY_BYTES: int = 2 * 1024 * 1024  # 2MB request body safeguard

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
