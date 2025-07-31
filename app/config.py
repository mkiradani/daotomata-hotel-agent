"""Configuration settings for the Hotel Bot API."""

import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    app_name: str = "Daotomata Hotel Bot API"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")

    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", env="OPENAI_MODEL")

    # Directus Configuration
    directus_url: str = Field(..., env="DIRECTUS_URL")
    directus_token: str = Field(..., env="DIRECTUS_TOKEN")
    directus_email: Optional[str] = Field(None, env="DIRECTUS_EMAIL")
    directus_password: Optional[str] = Field(None, env="DIRECTUS_PASSWORD")

    # Redis Configuration (for caching and sessions)
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")

    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    allowed_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:4321",  # Astro dev server
            "http://localhost:8080",
        ],
        env="ALLOWED_ORIGINS",
    )

    # Hotel Context
    current_domain: Optional[str] = Field(None, env="CURRENT_DOMAIN")

    # HITL (Human-In-The-Loop) Configuration
    hitl_enabled: bool = Field(default=True, env="HITL_ENABLED")
    hitl_confidence_threshold: float = Field(default=0.7, env="HITL_CONFIDENCE_THRESHOLD")
    hitl_evaluation_model: str = Field(default="gpt-4o-mini", env="HITL_EVALUATION_MODEL")

    # Chatwoot configuration removed - now stored per hotel in Directus

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()
