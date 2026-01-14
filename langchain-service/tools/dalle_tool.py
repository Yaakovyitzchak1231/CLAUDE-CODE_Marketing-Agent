"""
DALL-E 3 Image Generation Tool
Wrapper for OpenAI DALL-E 3 API
"""

import requests
from typing import Dict, List, Optional, Any
import base64
from pathlib import Path
import structlog
from config import settings

logger = structlog.get_logger()


class DallETool:
    """
    DALL-E 3 image generation wrapper

    Features:
    - Text-to-image generation
    - Multiple size options
    - Quality settings (standard/hd)
    - Style options (vivid/natural)
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize DALL-E tool

        Args:
            api_key: OpenAI API key (defaults to env variable)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        self.base_url = "https://api.openai.com/v1/images/generations"

        logger.info("dalle_tool_initialized")

    def generate(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        n: int = 1
    ) -> Dict[str, Any]:
        """
        Generate image with DALL-E 3

        Args:
            prompt: Image description (max 4000 chars)
            size: Image size (1024x1024, 1024x1792, 1792x1024)
            quality: Quality (standard, hd)
            style: Style (vivid, natural)
            n: Number of images (1 only for DALL-E 3)

        Returns:
            Dict with image URLs and metadata
        """
        # Validate parameters
        valid_sizes = ["1024x1024", "1024x1792", "1792x1024"]
        if size not in valid_sizes:
            logger.warning("invalid_size", size=size, valid=valid_sizes)
            size = "1024x1024"

        valid_qualities = ["standard", "hd"]
        if quality not in valid_qualities:
            logger.warning("invalid_quality", quality=quality)
            quality = "standard"

        valid_styles = ["vivid", "natural"]
        if style not in valid_styles:
            logger.warning("invalid_style", style=style)
            style = "vivid"

        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "dall-e-3",
            "prompt": prompt[:4000],  # Max 4000 chars
            "size": size,
            "quality": quality,
            "style": style,
            "n": 1  # DALL-E 3 only supports n=1
        }

        try:
            logger.info("generating_image", prompt_length=len(prompt), size=size, quality=quality)

            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            data = response.json()

            # Calculate cost
            cost = self._calculate_cost(size, quality)

            result = {
                "success": True,
                "images": data.get("data", []),
                "prompt": prompt,
                "revised_prompt": data.get("data", [{}])[0].get("revised_prompt", prompt),
                "size": size,
                "quality": quality,
                "style": style,
                "cost": cost,
                "provider": "dalle3"
            }

            logger.info(
                "image_generated",
                image_count=len(result["images"]),
                cost=cost
            )

            return result

        except requests.exceptions.RequestException as e:
            logger.error("dalle_generation_error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }

    def _calculate_cost(self, size: str, quality: str) -> float:
        """
        Calculate cost based on size and quality

        DALL-E 3 pricing (as of 2024):
        - Standard 1024x1024: $0.040
        - Standard 1024x1792 or 1792x1024: $0.080
        - HD 1024x1024: $0.080
        - HD 1024x1792 or 1792x1024: $0.120
        """
        if quality == "hd":
            if size == "1024x1024":
                return 0.080
            else:  # 1024x1792 or 1792x1024
                return 0.120
        else:  # standard
            if size == "1024x1024":
                return 0.040
            else:
                return 0.080

    def download_image(self, url: str, save_path: Path) -> bool:
        """
        Download image from URL

        Args:
            url: Image URL from DALL-E response
            save_path: Path to save image

        Returns:
            Success status
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(response.content)

            logger.info("image_downloaded", path=str(save_path))
            return True

        except Exception as e:
            logger.error("download_error", error=str(e), url=url)
            return False

    def generate_variations(
        self,
        base_prompt: str,
        variations: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple variations of a prompt

        Args:
            base_prompt: Base description
            variations: List of variation modifiers
            **kwargs: Additional parameters for generate()

        Returns:
            List of generation results
        """
        results = []

        for variation in variations:
            full_prompt = f"{base_prompt}, {variation}"
            result = self.generate(prompt=full_prompt, **kwargs)
            results.append(result)

        return results


def create_dalle_langchain_tool():
    """Create LangChain-compatible DALL-E tool"""
    from langchain.tools import Tool

    dalle = DallETool()

    def dalle_wrapper(prompt: str) -> str:
        """Generate image with DALL-E 3"""
        result = dalle.generate(prompt=prompt)

        if result.get("success"):
            images = result.get("images", [])
            if images:
                url = images[0].get("url", "")
                revised_prompt = result.get("revised_prompt", prompt)
                cost = result.get("cost", 0)

                return f"""Image generated successfully!

URL: {url}
Revised Prompt: {revised_prompt}
Cost: ${cost:.3f}
Size: {result.get('size')}
Quality: {result.get('quality')}

Download this URL to view the image."""
            else:
                return "Image generation succeeded but no images returned."
        else:
            return f"Image generation failed: {result.get('error', 'Unknown error')}"

    return Tool(
        name="DALLE_Image_Generator",
        func=dalle_wrapper,
        description="Generate high-quality images using DALL-E 3. "
                    "Input should be a detailed image description. "
                    "Returns image URL and generation details. "
                    "Costs $0.04-$0.12 per image depending on size and quality."
    )


if __name__ == "__main__":
    # Test DALL-E tool
    dalle = DallETool()

    result = dalle.generate(
        prompt="Professional business team collaborating in modern office, bright natural lighting, diverse team members, blue and white corporate colors",
        size="1024x1024",
        quality="standard"
    )

    if result.get("success"):
        print(f"✓ Image generated: {result['images'][0]['url']}")
        print(f"Cost: ${result['cost']:.3f}")
    else:
        print(f"✗ Generation failed: {result.get('error')}")
