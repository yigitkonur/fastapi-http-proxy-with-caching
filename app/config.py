"""
Configuration management using Pydantic Settings.

Loads configuration from environment variables with sensible defaults.
Supports .env files for local development.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    app_name: str = Field(
        default="FastAPI Transparent Proxy",
        description="Application name for documentation"
    )
    app_version: str = Field(
        default="2.0.0",
        description="Application version"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode with verbose logging"
    )
    
    # Server
    host: str = Field(
        default="0.0.0.0",
        description="Host to bind the server"
    )
    port: int = Field(
        default=8000,
        description="Port to bind the server"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL (supports Upstash)"
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        description="Cache TTL in seconds (0 = no expiry)",
        ge=0
    )
    cache_prefix: str = Field(
        default="proxy:cache:",
        description="Prefix for all cache keys in Redis"
    )
    
    # Proxy
    proxy_timeout_seconds: float = Field(
        default=30.0,
        description="Timeout for proxied requests in seconds",
        gt=0
    )
    max_request_body_size: int = Field(
        default=10 * 1024 * 1024,  # 10 MB
        description="Maximum request body size in bytes"
    )
    
    # Headers to exclude when forwarding
    excluded_headers: list[str] = Field(
        default=[
            "host",
            "content-length", 
            "connection",
            "accept-encoding",
            "transfer-encoding",
        ],
        description="Headers to exclude when forwarding requests"
    )
    
    @field_validator("excluded_headers", mode="before")
    @classmethod
    def parse_excluded_headers(cls, v):
        """Parse comma-separated string to list if needed."""
        if isinstance(v, str):
            return [h.strip().lower() for h in v.split(",") if h.strip()]
        return [h.lower() for h in v]


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are loaded only once
    and reused across the application lifecycle.
    """
    return Settings()
