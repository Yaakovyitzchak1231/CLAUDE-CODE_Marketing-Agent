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

    # LLM Provider Selection
    # Options: "openai", "ollama"
    # If OPENAI_API_KEY is set and LLM_PROVIDER is "openai", uses OpenAI
    # Otherwise falls back to Ollama
    LLM_PROVIDER: str = "openai"  # Default to OpenAI for speed

    # Ollama LLM (fallback/local option)
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    # SearXNG Search
    SEARXNG_BASE_URL: str = "http://searxng:8080"

    # OpenAI (for LLM and DALL-E 3)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"  # Fast and cost-effective

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


# =============================================================================
# INDUSTRY ROUTING CONFIGURATION
# =============================================================================
# This configuration determines which data sources to use for each industry type.
# REGULATED industries use government data (SEC, FDA, BLS, Census).
# COMMERCIAL industries use market intelligence (Google Trends, industry pubs).
# =============================================================================

class IndustryConfig:
    """Industry classification and data source routing."""

    # Regulated industries - use government data sources
    REGULATED_INDUSTRIES = {
        'healthcare', 'hospitals', 'pharma', 'pharmaceutical', 'medical', 'biotech',
        'banking', 'finance', 'lending', 'mortgage', 'insurance', 'securities',
        'investment', 'wealth_management', 'credit_union'
    }

    # Commercial/niche industries - use commercial intelligence
    COMMERCIAL_INDUSTRIES = {
        'payments', 'credit_card_processing', 'merchant_services', 'pos',
        'ertc', 'erc', 'tax_credits', 'employee_retention_credit',
        'factoring', 'equipment_leasing', 'asset_based_lending',
        'marketing', 'advertising', 'technology', 'software', 'saas',
        'manufacturing', 'retail', 'ecommerce', 'logistics'
    }

    # Source credibility hierarchy (Tier 1 = Highest)
    SOURCE_CREDIBILITY = {
        'tier1': {
            'name': 'Government/Regulatory',
            'sources': ['sec.gov', 'bls.gov', 'census.gov', 'fda.gov', 'cms.gov', 'irs.gov'],
            'confidence': 'high',
            'description': 'Official government statistics and regulatory filings'
        },
        'tier2': {
            'name': 'Major Business News',
            'sources': ['reuters.com', 'bloomberg.com', 'wsj.com', 'ft.com'],
            'confidence': 'high',
            'description': 'Authoritative financial journalism'
        },
        'tier3': {
            'name': 'Industry Publications',
            'sources': ['pymnts.com', 'paymentsjournal.com', 'businesswire.com', 'prnewswire.com'],
            'confidence': 'medium',
            'description': 'Industry-specific trade publications and press releases'
        },
        'tier4': {
            'name': 'General News/Analysis',
            'sources': ['default'],
            'confidence': 'low',
            'description': 'General news and blog sources'
        },
        'tier5': {
            'name': 'LLM Generated',
            'sources': ['llm'],
            'confidence': 'requires_review',
            'description': 'AI-generated content without source verification'
        }
    }

    @classmethod
    def classify_industry(cls, industry: str) -> str:
        """
        Classify an industry as REGULATED or COMMERCIAL.

        Args:
            industry: Industry name or description

        Returns:
            'regulated' or 'commercial'
        """
        industry_lower = industry.lower().replace(' ', '_').replace('-', '_')

        # Check direct match
        if industry_lower in cls.REGULATED_INDUSTRIES:
            return 'regulated'
        if industry_lower in cls.COMMERCIAL_INDUSTRIES:
            return 'commercial'

        # Check partial match
        for regulated in cls.REGULATED_INDUSTRIES:
            if regulated in industry_lower or industry_lower in regulated:
                return 'regulated'

        for commercial in cls.COMMERCIAL_INDUSTRIES:
            if commercial in industry_lower or industry_lower in commercial:
                return 'commercial'

        # Default to commercial (safer - no compliance risk)
        return 'commercial'

    @classmethod
    def get_data_sources(cls, industry: str) -> dict:
        """
        Get recommended data sources for an industry.

        Args:
            industry: Industry name

        Returns:
            Dict with primary and secondary data sources
        """
        industry_type = cls.classify_industry(industry)

        if industry_type == 'regulated':
            return {
                'type': 'regulated',
                'primary_sources': ['gov_data_tool'],  # BLS, Census, SEC, FDA
                'secondary_sources': ['commercial_intel_tool', 'trends_tool'],
                'required_confidence': 'high',
                'source_priority': ['tier1', 'tier2', 'tier3'],
                'avoid_sources': ['tier5']  # No LLM-only insights for regulated
            }
        else:
            return {
                'type': 'commercial',
                'primary_sources': ['trends_tool', 'commercial_intel_tool'],
                'secondary_sources': ['gov_data_tool'],  # BLS for employment data
                'required_confidence': 'medium',
                'source_priority': ['tier2', 'tier3', 'tier1'],
                'avoid_sources': ['tier5']
            }

    @classmethod
    def get_confidence_level(cls, sources_used: list) -> str:
        """
        Calculate overall confidence based on sources used.

        Args:
            sources_used: List of source domains or tool names

        Returns:
            'high', 'medium', 'low', or 'requires_review'
        """
        tier1_count = 0
        tier2_count = 0
        tier3_count = 0

        for source in sources_used:
            source_lower = source.lower()
            if any(s in source_lower for s in cls.SOURCE_CREDIBILITY['tier1']['sources']):
                tier1_count += 1
            elif any(s in source_lower for s in cls.SOURCE_CREDIBILITY['tier2']['sources']):
                tier2_count += 1
            elif any(s in source_lower for s in cls.SOURCE_CREDIBILITY['tier3']['sources']):
                tier3_count += 1

        if tier1_count >= 2 or (tier1_count >= 1 and tier2_count >= 2):
            return 'high'
        elif tier1_count >= 1 or tier2_count >= 2 or tier3_count >= 3:
            return 'medium'
        elif tier2_count >= 1 or tier3_count >= 1:
            return 'low'
        else:
            return 'requires_review'


# Global industry config instance
industry_config = IndustryConfig()


# =============================================================================
# LLM INITIALIZATION
# =============================================================================

def create_llm():
    """
    Create LLM instance based on configuration.

    Priority:
    1. If LLM_PROVIDER="openai" and OPENAI_API_KEY is set -> Use OpenAI
    2. Otherwise -> Fall back to Ollama (local)

    Returns:
        LangChain LLM instance (OpenAI or Ollama)
    """
    import structlog
    logger = structlog.get_logger()

    if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                api_key=settings.OPENAI_API_KEY
            )
            logger.info(
                "llm_initialized",
                provider="openai",
                model=settings.OPENAI_MODEL
            )
            return llm
        except ImportError:
            logger.warning("langchain_openai_not_installed_falling_back_to_ollama")
        except Exception as e:
            logger.warning(f"openai_init_failed_falling_back_to_ollama: {e}")

    # Fallback to Ollama
    from langchain_community.llms import Ollama

    llm = Ollama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL
    )
    logger.info(
        "llm_initialized",
        provider="ollama",
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL
    )
    return llm
