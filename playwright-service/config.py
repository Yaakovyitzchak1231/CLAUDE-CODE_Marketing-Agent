"""
Configuration Management for Playwright Service
Uses pydantic-settings to load environment variables
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Playwright service settings"""

    # Service settings
    SERVICE_PORT: int = 8002
    SERVICE_HOST: str = "0.0.0.0"

    # Browser settings
    BROWSER_TYPE: str = "chromium"
    HEADLESS: bool = True
    DEFAULT_TIMEOUT: int = 30000
    DEFAULT_VIEWPORT_WIDTH: int = 1920
    DEFAULT_VIEWPORT_HEIGHT: int = 1080

    # User agent
    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Performance
    MAX_CONCURRENT_CONTEXTS: int = 10
    BROWSER_POOL_SIZE: int = 2

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
