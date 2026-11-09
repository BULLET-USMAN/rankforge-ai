from typing import List, Optional, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized configuration for RankForge AI backend.
    Loads from environment variables or falls back to secure defaults.
    """

    PROJECT_NAME: str = "RankForge AI API"
    VERSION: str = "0.2.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Security & JWT
    SECRET_KEY: str = "rf_dev_secret_key_change_in_production_894172498172938471"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3002",
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

    # Supabase Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    SUPABASE_JWT_AUDIENCE: str = "authenticated"
    SUPABASE_JWT_ISSUER: Optional[str] = None

    # Database
    DATABASE_URL: str = (
        "postgresql+psycopg://rankforge:rankforge_dev_password@localhost:5432/rankforge_db"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if not v:
            return v
        # Standardize PostgreSQL dialect to psycopg v3 (psycopg[binary]>=3.2.0)
        if v.startswith("postgres://"):
            return "postgresql+psycopg://" + v[len("postgres://") :]
        if v.startswith("postgresql://") and not v.startswith("postgresql+"):
            return "postgresql+psycopg://" + v[len("postgresql://") :]
        return v

    # Public URLs for production routing and OAuth callbacks
    PUBLIC_API_URL: Optional[str] = None
    FRONTEND_URL: str = "http://localhost:3000"

    # Google Search Console OAuth 2.0 Integration
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    GOOGLE_SEARCH_CONSOLE_SCOPE: str = (
        "openid email https://www.googleapis.com/auth/webmasters.readonly"
    )

    def get_google_redirect_uri(self) -> str:
        """Determines the exact Google OAuth callback URI based on configuration."""
        if self.GOOGLE_REDIRECT_URI:
            return self.GOOGLE_REDIRECT_URI
        if self.PUBLIC_API_URL:
            return (
                f"{self.PUBLIC_API_URL.rstrip('/')}{self.API_V1_STR}/integrations/google/callback"
            )
        return f"http://localhost:8000{self.API_V1_STR}/integrations/google/callback"

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Crawler & Preflight SSRF Safeguards
    CRAWLER_MAX_RESPONSE_BYTES: int = 5 * 1024 * 1024  # 5MB
    CRAWLER_TIMEOUT_SECONDS: float = 10.0
    CRAWLER_MAX_REDIRECTS: int = 3
    MAX_REQUEST_BODY_BYTES: int = 2 * 1024 * 1024  # 2MB request body safeguard

    # Invitation settings
    INVITATION_EXPIRY_DAYS: int = 7

    # AI Engine & Gemini Configuration
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    AI_PROVIDER: str = "gemini"  # "gemini" or "mock"
    AI_MAX_OUTPUT_TOKENS: int = 2048
    AI_REQUEST_TIMEOUT_SECONDS: int = 30
    AI_MAX_RETRIES: int = 3
    AI_DAILY_ORG_REQUEST_LIMIT: int = 100
    AI_MONTHLY_ORG_TOKEN_LIMIT: int = 500000
    AI_MAX_BATCH_SIZE: int = 20
    AI_MAX_CONCURRENT_JOBS_PER_ORG: int = 3
    AI_ESTIMATED_INPUT_COST_PER_MILLION: float = 0.075
    AI_ESTIMATED_OUTPUT_COST_PER_MILLION: float = 0.30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
