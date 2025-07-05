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

    # Supabase Configuration
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_key: str = Field(..., env="SUPABASE_ANON_KEY")
    supabase_service_key: Optional[str] = Field(None, env="SUPABASE_SERVICE_ROLE_KEY")

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

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()
