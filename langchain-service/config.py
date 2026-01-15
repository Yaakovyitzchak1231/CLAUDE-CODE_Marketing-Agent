"""
Configuration management for LangChain service
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Service
    SERVICE_NAME: str = "marketing-automation-ai"
    DEBUG: bool = False

    # Database
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "marketing"
    POSTGRES_USER: str = "marketing_user"
    POSTGRES_PASSWORD: str

    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None

    # Chroma Vector DB
    CHROMA_HOST: str = "chroma"
    CHROMA_PORT: int = 8000

    # Ollama LLM
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    # SearXNG Search
    SEARXNG_BASE_URL: str = "http://searxng:8080"

    # OpenAI (for DALL-E 3)
    OPENAI_API_KEY: Optional[str] = None

    # Midjourney (alternative)
    MIDJOURNEY_API_KEY: Optional[str] = None
    MIDJOURNEY_API_URL: Optional[str] = "https://api.midjourney-api.com/v1"

    # Runway ML (for video)
    RUNWAY_API_KEY: Optional[str] = None

    # Pika (alternative)
    PIKA_API_KEY: Optional[str] = None
    PIKA_API_URL: Optional[str] = "https://api.pika.art/v1"

    # LinkedIn Publishing
    LINKEDIN_ACCESS_TOKEN: Optional[str] = None

    # WordPress Publishing
    WORDPRESS_URL: Optional[str] = None
    WORDPRESS_USERNAME: Optional[str] = None
    WORDPRESS_PASSWORD: Optional[str] = None

    # Email Publishing
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # Agent Configuration
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TIMEOUT: int = 300  # seconds

    # LLM Settings
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048

    # Vector Store
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get PostgreSQL connection URL"""
    return (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )


def get_redis_url() -> str:
    """Get Redis connection URL"""
    if settings.REDIS_PASSWORD:
        return f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}"
    return f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"


def get_chroma_url() -> str:
    """Get Chroma vector DB URL"""
    return f"http://{settings.CHROMA_HOST}:{settings.CHROMA_PORT}"
