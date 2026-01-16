"""
Base LLM Provider Interface

Provides abstract interface and registry for LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import structlog

logger = structlog.get_logger()


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement:
    - get_llm(): Return a LangChain-compatible LLM instance
    - is_available(): Check if provider is configured and available
    - get_info(): Return provider metadata
    """

    name: str = "base"
    description: str = "Base LLM Provider"
    supports_streaming: bool = False
    supports_function_calling: bool = False

    @abstractmethod
    def get_llm(self):
        """
        Get a LangChain-compatible LLM instance.

        Returns:
            LangChain LLM (ChatOpenAI, Ollama, HuggingFacePipeline, etc.)
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this provider is available and configured.

        Returns:
            True if provider can be used
        """
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """
        Get provider information and configuration.

        Returns:
            Dict with provider name, model, status, etc.
        """
        pass

    def get_model_name(self) -> str:
        """Get the current model name."""
        info = self.get_info()
        return info.get('model', 'unknown')


class LLMProviderRegistry:
    """
    Registry for LLM providers.

    Manages provider instances and selection logic.
    """

    _providers: Dict[str, BaseLLMProvider] = {}
    _default_provider: Optional[str] = None
    _content_provider: Optional[str] = None
    _initialized: bool = False

    @classmethod
    def _ensure_initialized(cls):
        """Initialize providers if not already done."""
        if cls._initialized:
            return

        from config import settings

        # Register providers
        from .openai_provider import OpenAIProvider
        from .ollama_provider import OllamaProvider
        from .llamarketing_provider import LLaMarketingProvider

        cls._providers['openai'] = OpenAIProvider()
        cls._providers['ollama'] = OllamaProvider()
        cls._providers['llamarketing'] = LLaMarketingProvider()

        # Set default provider from config
        cls._default_provider = getattr(settings, 'LLM_PROVIDER', 'openai')
        cls._content_provider = getattr(settings, 'CONTENT_LLM_PROVIDER', None)

        cls._initialized = True
        logger.info(
            "llm_provider_registry_initialized",
            providers=list(cls._providers.keys()),
            default=cls._default_provider,
            content_provider=cls._content_provider
        )

    @classmethod
    def register(cls, name: str, provider: BaseLLMProvider):
        """
        Register a new provider.

        Args:
            name: Provider identifier
            provider: Provider instance
        """
        cls._providers[name] = provider
        logger.info("llm_provider_registered", name=name)

    @classmethod
    def get_provider(cls, name: str = None) -> Any:
        """
        Get an LLM instance from a provider.

        Args:
            name: Provider name, or None for default

        Returns:
            LangChain-compatible LLM instance
        """
        cls._ensure_initialized()

        provider_name = name or cls._default_provider

        # Try requested provider
        if provider_name in cls._providers:
            provider = cls._providers[provider_name]
            if provider.is_available():
                logger.info("using_llm_provider", provider=provider_name)
                return provider.get_llm()
            else:
                logger.warning(
                    "llm_provider_not_available",
                    provider=provider_name,
                    reason="not configured or dependencies missing"
                )

        # Fallback chain: openai -> ollama
        fallback_order = ['openai', 'ollama']
        for fallback in fallback_order:
            if fallback in cls._providers and fallback != provider_name:
                provider = cls._providers[fallback]
                if provider.is_available():
                    logger.info(
                        "using_fallback_llm_provider",
                        requested=provider_name,
                        fallback=fallback
                    )
                    return provider.get_llm()

        raise RuntimeError(
            f"No LLM provider available. Tried: {provider_name}, {fallback_order}"
        )

    @classmethod
    def get_content_llm(cls) -> Any:
        """
        Get the specialized LLM for content generation.

        Uses CONTENT_LLM_PROVIDER if set, otherwise default.

        Returns:
            LangChain-compatible LLM instance
        """
        cls._ensure_initialized()

        # Try content-specific provider first
        if cls._content_provider and cls._content_provider in cls._providers:
            provider = cls._providers[cls._content_provider]
            if provider.is_available():
                logger.info(
                    "using_content_llm_provider",
                    provider=cls._content_provider
                )
                return provider.get_llm()

        # Fall back to default
        return cls.get_provider()

    @classmethod
    def list_providers(cls) -> Dict[str, Any]:
        """
        List all providers and their status.

        Returns:
            Dict with provider information
        """
        cls._ensure_initialized()

        result = {
            'default_provider': cls._default_provider,
            'content_provider': cls._content_provider,
            'providers': {}
        }

        for name, provider in cls._providers.items():
            result['providers'][name] = {
                'available': provider.is_available(),
                'info': provider.get_info()
            }

        return result

    @classmethod
    def reset(cls):
        """Reset registry (for testing)."""
        cls._providers = {}
        cls._default_provider = None
        cls._content_provider = None
        cls._initialized = False
