"""
LLM Provider Abstraction Layer

Provides a unified interface for multiple LLM providers:
- OpenAI (GPT-4, GPT-4o-mini)
- Ollama (Llama 3.1, local models)
- LLa-Marketing (Hugging Face, marketing-specialized)

Usage:
    from llm_providers import get_provider, get_content_llm

    # Get default provider
    llm = get_provider()

    # Get provider by name
    llm = get_provider("openai")

    # Get specialized content LLM (uses LLa-Marketing if available)
    content_llm = get_content_llm()
"""

from .base_provider import BaseLLMProvider, LLMProviderRegistry
from .openai_provider import OpenAIProvider
from .ollama_provider import OllamaProvider
from .llamarketing_provider import LLaMarketingProvider

__all__ = [
    'BaseLLMProvider',
    'LLMProviderRegistry',
    'OpenAIProvider',
    'OllamaProvider',
    'LLaMarketingProvider',
    'get_provider',
    'get_content_llm',
    'list_providers'
]


def get_provider(provider_name: str = None):
    """
    Get an LLM provider instance.

    Args:
        provider_name: Provider name ("openai", "ollama", "llamarketing")
                      If None, uses default from config

    Returns:
        LangChain-compatible LLM instance
    """
    return LLMProviderRegistry.get_provider(provider_name)


def get_content_llm():
    """
    Get the specialized LLM for content generation.

    Uses LLa-Marketing if available and configured,
    otherwise falls back to default provider.

    Returns:
        LangChain-compatible LLM instance
    """
    return LLMProviderRegistry.get_content_llm()


def list_providers() -> dict:
    """
    List all available LLM providers and their status.

    Returns:
        Dict with provider info and availability
    """
    return LLMProviderRegistry.list_providers()
