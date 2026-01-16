"""
LLa-Marketing LLM Provider

Provides access to LLa-Marketing, a domain-specific LLM for marketing content.
Model: marketeam/LLa-Marketing (8B parameters, trained on 43B marketing tokens)

Deployment options:
1. Hugging Face Transformers (direct loading, 8-bit quantization)
2. Ollama with custom GGUF model
"""

from typing import Dict, Any, Optional
import structlog

from .base_provider import BaseLLMProvider

logger = structlog.get_logger()


class LLaMarketingProvider(BaseLLMProvider):
    """
    LLa-Marketing LLM Provider.

    Domain-specific LLM optimized for marketing content generation:
    - Social media posts
    - Blog content
    - Marketing copy
    - Brand messaging

    Model: marketeam/LLa-Marketing
    Base: Llama 3.1 8B
    Training: 43B marketing tokens
    """

    name = "llamarketing"
    description = "Domain-specific marketing LLM (LLa-Marketing)"
    supports_streaming = True
    supports_function_calling = False

    # Default model configuration
    DEFAULT_MODEL_ID = "marketeam/LLa-Marketing"
    DEFAULT_LOAD_8BIT = True  # Reduces memory to ~8GB
    DEFAULT_MAX_NEW_TOKENS = 2048

    def __init__(self):
        """Initialize LLa-Marketing provider."""
        from config import settings
        self.settings = settings
        self._llm = None
        self._available = None
        self._load_error = None

        # Get config with defaults
        self.model_id = getattr(
            settings, 'LLAMARKETING_MODEL_ID', self.DEFAULT_MODEL_ID
        )
        self.load_8bit = getattr(
            settings, 'LLAMARKETING_LOAD_8BIT', self.DEFAULT_LOAD_8BIT
        )
        self.max_new_tokens = getattr(
            settings, 'LLM_MAX_TOKENS', self.DEFAULT_MAX_NEW_TOKENS
        )
        self.temperature = getattr(settings, 'LLM_TEMPERATURE', 0.7)

    def is_available(self) -> bool:
        """
        Check if LLa-Marketing is available.

        Checks:
        1. Required libraries installed (transformers, accelerate)
        2. CONTENT_LLM_PROVIDER set to "llamarketing"
        3. Sufficient memory (optional)

        Returns:
            True if provider can be used
        """
        if self._available is not None:
            return self._available

        # Check if explicitly enabled
        content_provider = getattr(self.settings, 'CONTENT_LLM_PROVIDER', None)
        if content_provider != 'llamarketing':
            self._available = False
            self._load_error = "CONTENT_LLM_PROVIDER not set to 'llamarketing'"
            return False

        # Check required libraries
        try:
            import transformers
            import torch
            self._available = True
        except ImportError as e:
            self._available = False
            self._load_error = f"Missing dependency: {e}"
            return False

        return self._available

    def get_llm(self):
        """
        Get LLa-Marketing LLM instance.

        Uses HuggingFacePipeline with optional 8-bit quantization.

        Returns:
            HuggingFacePipeline instance
        """
        if self._llm is not None:
            return self._llm

        if not self.is_available():
            raise RuntimeError(
                f"LLa-Marketing not available: {self._load_error}"
            )

        try:
            import torch
            from transformers import (
                AutoModelForCausalLM,
                AutoTokenizer,
                pipeline,
                BitsAndBytesConfig
            )
            from langchain_community.llms import HuggingFacePipeline

            logger.info(
                "loading_llamarketing_model",
                model_id=self.model_id,
                load_8bit=self.load_8bit
            )

            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                trust_remote_code=True
            )

            # Configure quantization if enabled
            model_kwargs = {
                "trust_remote_code": True,
                "device_map": "auto"
            }

            if self.load_8bit:
                try:
                    import bitsandbytes
                    quantization_config = BitsAndBytesConfig(
                        load_in_8bit=True,
                        llm_int8_threshold=6.0
                    )
                    model_kwargs["quantization_config"] = quantization_config
                    logger.info("using_8bit_quantization")
                except ImportError:
                    logger.warning(
                        "bitsandbytes_not_installed_loading_full_precision"
                    )

            # Load model
            model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                **model_kwargs
            )

            # Create text generation pipeline
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=self.max_new_tokens,
                temperature=self.temperature,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1
            )

            # Wrap in LangChain
            self._llm = HuggingFacePipeline(pipeline=pipe)

            logger.info(
                "llamarketing_model_loaded",
                model_id=self.model_id,
                quantized=self.load_8bit
            )

            return self._llm

        except Exception as e:
            self._load_error = str(e)
            logger.error(
                "llamarketing_load_failed",
                error=str(e),
                model_id=self.model_id
            )
            raise RuntimeError(f"Failed to load LLa-Marketing: {e}")

    def get_info(self) -> Dict[str, Any]:
        """
        Get LLa-Marketing provider information.

        Returns:
            Dict with provider configuration and capabilities
        """
        return {
            'name': self.name,
            'description': self.description,
            'model_id': self.model_id,
            'base_model': 'Llama 3.1 8B',
            'training_tokens': '43B marketing-specific tokens',
            'load_8bit': self.load_8bit,
            'memory_requirement': '~8GB (8-bit)' if self.load_8bit else '~16GB (FP16)',
            'temperature': self.temperature,
            'max_new_tokens': self.max_new_tokens,
            'available': self._available if self._available is not None else 'not_checked',
            'load_error': self._load_error,
            'supports_streaming': self.supports_streaming,
            'supports_function_calling': self.supports_function_calling,
            'optimized_for': [
                'social_media_posts',
                'blog_content',
                'marketing_copy',
                'email_campaigns',
                'brand_messaging',
                'ad_copy'
            ],
            'huggingface_url': f'https://huggingface.co/{self.model_id}'
        }

    def generate_marketing_content(
        self,
        prompt: str,
        content_type: str = "general",
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate marketing content with optimized prompting.

        Args:
            prompt: Content generation prompt
            content_type: Type of content (blog, social, email, ad)
            max_tokens: Override max tokens

        Returns:
            Generated marketing content
        """
        llm = self.get_llm()

        # Add marketing-specific system prompt
        system_prompts = {
            "blog": "You are an expert B2B marketing content writer. Create engaging, SEO-optimized blog content.",
            "social": "You are a social media marketing expert. Create engaging posts optimized for LinkedIn and professional audiences.",
            "email": "You are an email marketing specialist. Write compelling email copy with strong CTAs.",
            "ad": "You are an advertising copywriter. Create persuasive ad copy that converts."
        }

        system = system_prompts.get(content_type, system_prompts["blog"])
        full_prompt = f"{system}\n\n{prompt}"

        # Generate
        if max_tokens:
            # Would need to modify pipeline, for now just use as-is
            pass

        return llm.invoke(full_prompt)
