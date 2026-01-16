"""
Ollama LLM Provider

Provides access to local LLMs via Ollama (Llama 3.1, Mistral, etc.)
"""

from typing import Dict, Any
import structlog

from .base_provider import BaseLLMProvider

logger = structlog.get_logger()


class OllamaProvider(BaseLLMProvider):
    """
    Ollama LLM Provider.

    Supports:
    - Llama 3.1 (default)
    - Mistral
    - Any Ollama-compatible model
    - Local/private deployment
    """

    name = "ollama"
    description = "Local LLMs via Ollama (Llama 3.1, Mistral)"
    supports_streaming = True
    supports_function_calling = False  # Limited function calling support

    def __init__(self):
        """Initialize Ollama provider."""
        from config import settings
        self.settings = settings
        self._llm = None
        self._available = None

    def is_available(self) -> bool:
        """
        Check if Ollama is available.

        Returns:
            True if Ollama server is reachable
        """
        if self._available is not None:
            return self._available

        # Check if Ollama is reachable
        try:
            import requests
            response = requests.get(
                f"{self.settings.OLLAMA_BASE_URL}/api/tags",
                timeout=5
            )
            self._available = response.status_code == 200
        except Exception:
            self._available = False

        return self._available

    def get_llm(self):
        """
        Get Ollama LLM instance.

        Returns:
            Ollama instance
        """
        if self._llm is not None:
            return self._llm

        try:
            from langchain_community.llms import Ollama

            self._llm = Ollama(
                model=self.settings.OLLAMA_MODEL,
                base_url=self.settings.OLLAMA_BASE_URL
            )

            logger.info(
                "ollama_llm_created",
                model=self.settings.OLLAMA_MODEL,
                base_url=self.settings.OLLAMA_BASE_URL
            )

            return self._llm

        except ImportError:
            raise RuntimeError(
                "langchain-community not installed. "
                "Run: pip install langchain-community"
            )

    def get_info(self) -> Dict[str, Any]:
        """
        Get Ollama provider information.

        Returns:
            Dict with provider configuration
        """
        # Get available models if Ollama is reachable
        available_models = []
        try:
            if self.is_available():
                import requests
                response = requests.get(
                    f"{self.settings.OLLAMA_BASE_URL}/api/tags",
                    timeout=5
                )
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    available_models = [m.get('name') for m in models]
        except Exception:
            pass

        return {
            'name': self.name,
            'description': self.description,
            'model': self.settings.OLLAMA_MODEL,
            'base_url': self.settings.OLLAMA_BASE_URL,
            'server_available': self.is_available(),
            'supports_streaming': self.supports_streaming,
            'supports_function_calling': self.supports_function_calling,
            'available_models': available_models or [
                'llama3.1:8b',
                'llama3.1:70b',
                'mistral:7b',
                'codellama:13b',
                'mixtral:8x7b'
            ]
        }
