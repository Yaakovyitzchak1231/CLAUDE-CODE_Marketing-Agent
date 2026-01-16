"""
OpenAI LLM Provider

Provides access to OpenAI models (GPT-4, GPT-4o-mini, etc.)
"""

from typing import Dict, Any
import structlog

from .base_provider import BaseLLMProvider

logger = structlog.get_logger()


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI LLM Provider.

    Supports:
    - GPT-4o-mini (default, fast and cost-effective)
    - GPT-4o (more capable)
    - GPT-4-turbo
    - Function calling
    - Streaming
    """

    name = "openai"
    description = "OpenAI GPT models (GPT-4o-mini, GPT-4o)"
    supports_streaming = True
    supports_function_calling = True

    def __init__(self):
        """Initialize OpenAI provider."""
        from config import settings
        self.settings = settings
        self._llm = None

    def is_available(self) -> bool:
        """
        Check if OpenAI is configured.

        Returns:
            True if OPENAI_API_KEY is set
        """
        return bool(self.settings.OPENAI_API_KEY)

    def get_llm(self):
        """
        Get OpenAI LLM instance.

        Returns:
            ChatOpenAI instance
        """
        if self._llm is not None:
            return self._llm

        if not self.is_available():
            raise RuntimeError("OpenAI API key not configured")

        try:
            from langchain_openai import ChatOpenAI

            self._llm = ChatOpenAI(
                model=self.settings.OPENAI_MODEL,
                temperature=self.settings.LLM_TEMPERATURE,
                max_tokens=self.settings.LLM_MAX_TOKENS,
                api_key=self.settings.OPENAI_API_KEY
            )

            logger.info(
                "openai_llm_created",
                model=self.settings.OPENAI_MODEL,
                temperature=self.settings.LLM_TEMPERATURE
            )

            return self._llm

        except ImportError:
            raise RuntimeError(
                "langchain-openai not installed. "
                "Run: pip install langchain-openai"
            )

    def get_info(self) -> Dict[str, Any]:
        """
        Get OpenAI provider information.

        Returns:
            Dict with provider configuration
        """
        return {
            'name': self.name,
            'description': self.description,
            'model': self.settings.OPENAI_MODEL,
            'temperature': self.settings.LLM_TEMPERATURE,
            'max_tokens': self.settings.LLM_MAX_TOKENS,
            'api_key_configured': bool(self.settings.OPENAI_API_KEY),
            'supports_streaming': self.supports_streaming,
            'supports_function_calling': self.supports_function_calling,
            'available_models': [
                'gpt-4o-mini',
                'gpt-4o',
                'gpt-4-turbo',
                'gpt-4',
                'gpt-3.5-turbo'
            ]
        }
