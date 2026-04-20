"""
Application settings and configuration.
"""
import os
from typing import Optional

from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""
    
    model_config = SettingsConfigDict(
        env_file=(".env", "env.template"),
        env_file_encoding='utf-8',
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=True
    )
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "EndureIT API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "EndureIT Fitness Tracking Application API"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: str = ""
    
    @property
    def cors_origins(self) -> list[str]:
        """Get CORS origins as list."""
        if not self.BACKEND_CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

    # Database Configuration
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> PostgresDsn:
        """Build database URL from individual components or use provided URL."""
        if isinstance(v, str) and v:
            return PostgresDsn(v)
        
        # Get values from the model data
        data = info.data
        
        # Build the PostgreSQL URL from individual components
        return PostgresDsn.build(
            scheme="postgresql+psycopg2",
            username=data.get("POSTGRES_USER"),
            password=data.get("POSTGRES_PASSWORD"),
            host=data.get("POSTGRES_SERVER"),
            port=data.get("POSTGRES_PORT"),
            path=data.get("POSTGRES_DB"),
        )

    # Security Configuration
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days for development
    ALGORITHM: str = "HS256"

    # Redis Configuration (optional, for caching)
    REDIS_URL: Optional[str] = "redis://redis:6379"

    # Email Configuration (optional)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # Environment Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Logging Configuration
    LOG_LEVEL: str = "DEBUG"

    # Strava API Configuration
    STRAVA_CLIENT_ID: Optional[str] = None
    STRAVA_CLIENT_SECRET: Optional[str] = None
    STRAVA_ACCESS_TOKEN: Optional[str] = None
    STRAVA_REFRESH_TOKEN: Optional[str] = None

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT.lower() in ("development", "dev", "local")

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT.lower() in ("production", "prod")

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.ENVIRONMENT.lower() in ("testing", "test")


def get_settings() -> Settings:
    """Get settings instance. Useful for dependency injection."""
    return Settings()


# Create a global settings instance
settings = get_settings()