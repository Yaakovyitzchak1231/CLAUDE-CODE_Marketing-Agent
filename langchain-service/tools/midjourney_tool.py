"""
Midjourney Image Generation Tool
Wrapper for Midjourney API (unofficial)

Note: Midjourney doesn't have an official API.
This wrapper supports third-party API services like:
- midjourney-api.com
- thenextleg.io
- goapi.ai
"""

import requests
from typing import Dict, List, Optional, Any
import time
import structlog
from config import settings

logger = structlog.get_logger()


class MidjourneyTool:
    """
    Midjourney image generation wrapper

    Features:
    - Text-to-image generation
    - Upscaling
    - Variations
    - Custom aspect ratios
    - Style parameters
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None
    ):
        """
        Initialize Midjourney tool

        Args:
            api_key: Midjourney API key
            api_url: API endpoint URL
        """
        self.api_key = api_key or settings.MIDJOURNEY_API_KEY
        self.api_url = api_url or settings.MIDJOURNEY_API_URL or "https://api.midjourney-api.com/v1"

        if not self.api_key:
            logger.warning("midjourney_api_key_not_set")

        logger.info("midjourney_tool_initialized", api_url=self.api_url)

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        quality: str = "1",
        stylize: int = 100,
        chaos: int = 0,
        wait_for_completion: bool = True,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Generate image with Midjourney

        Args:
            prompt: Image description
            aspect_ratio: Aspect ratio (1:1, 16:9, 9:16, 4:3, 3:2, etc.)
            quality: Quality (0.25, 0.5, 1, 2)
            stylize: Stylization strength (0-1000, default 100)
            chaos: Variation amount (0-100, default 0)
            wait_for_completion: Wait for generation to complete
            timeout: Max wait time in seconds

        Returns:
            Dict with image URLs and metadata
        """
        # Build Midjourney prompt with parameters
        full_prompt = prompt

        if aspect_ratio != "1:1":
            full_prompt += f" --ar {aspect_ratio}"

        if quality != "1":
            full_prompt += f" --q {quality}"

        if stylize != 100:
            full_prompt += f" --stylize {stylize}"

        if chaos > 0:
            full_prompt += f" --chaos {chaos}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Submit generation request
        payload = {
            "prompt": full_prompt,
            "process_mode": "relax"  # or "fast" for priority queue
        }

        try:
            logger.info(
                "submitting_midjourney_request",
                prompt_length=len(prompt),
                aspect_ratio=aspect_ratio
            )

            # Submit job
            response = requests.post(
                f"{self.api_url}/imagine",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            job_id = data.get("job_id") or data.get("id")

            if not job_id:
                return {
                    "success": False,
                    "error": "No job ID returned",
                    "prompt": prompt
                }

            logger.info("midjourney_job_submitted", job_id=job_id)

            # Wait for completion if requested
            if wait_for_completion:
                return self._wait_for_completion(job_id, timeout)
            else:
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": "submitted",
                    "prompt": prompt
                }

        except requests.exceptions.RequestException as e:
            logger.error("midjourney_generation_error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }

    def _wait_for_completion(
        self,
        job_id: str,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Poll for job completion

        Args:
            job_id: Job identifier
            timeout: Maximum wait time

        Returns:
            Generation result
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        start_time = time.time()
        poll_interval = 5  # seconds

        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f"{self.api_url}/jobs/{job_id}",
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()

                data = response.json()
                status = data.get("status")

                logger.debug("job_status_check", job_id=job_id, status=status)

                if status == "completed":
                    # Calculate cost (example pricing)
                    cost = self._calculate_cost(data.get("process_mode", "relax"))

                    return {
                        "success": True,
                        "job_id": job_id,
                        "status": "completed",
                        "images": data.get("images", []),
                        "image_url": data.get("image_url") or (data.get("images", [{}])[0].get("url")),
                        "prompt": data.get("prompt"),
                        "cost": cost,
                        "provider": "midjourney"
                    }

                elif status in ["failed", "error"]:
                    return {
                        "success": False,
                        "job_id": job_id,
                        "status": status,
                        "error": data.get("error", "Generation failed")
                    }

                # Still processing
                time.sleep(poll_interval)

            except requests.exceptions.RequestException as e:
                logger.error("job_status_error", error=str(e), job_id=job_id)
                time.sleep(poll_interval)

        # Timeout reached
        logger.warning("job_timeout", job_id=job_id, timeout=timeout)
        return {
            "success": False,
            "job_id": job_id,
            "status": "timeout",
            "error": f"Generation timeout after {timeout} seconds"
        }

    def _calculate_cost(self, process_mode: str) -> float:
        """
        Estimate cost based on process mode

        Midjourney subscription tiers (approximate):
        - Relax mode: ~$10/month unlimited (but slower)
        - Fast mode: ~$30/month for 15 hours
        - Turbo mode: ~$60/month for 30 hours

        For API pricing, varies by provider
        """
        # Placeholder cost estimation
        if process_mode == "turbo":
            return 0.08
        elif process_mode == "fast":
            return 0.04
        else:  # relax
            return 0.01

    def upscale(
        self,
        job_id: str,
        index: int = 1,
        wait_for_completion: bool = True
    ) -> Dict[str, Any]:
        """
        Upscale a specific image from grid

        Args:
            job_id: Original generation job ID
            index: Image index to upscale (1-4)
            wait_for_completion: Wait for upscale to complete

        Returns:
            Upscaled image result
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "job_id": job_id,
            "index": index
        }

        try:
            response = requests.post(
                f"{self.api_url}/upscale",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            upscale_job_id = data.get("job_id") or data.get("id")

            if wait_for_completion:
                return self._wait_for_completion(upscale_job_id, timeout=180)
            else:
                return {
                    "success": True,
                    "job_id": upscale_job_id,
                    "status": "submitted"
                }

        except requests.exceptions.RequestException as e:
            logger.error("upscale_error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def create_variation(
        self,
        job_id: str,
        index: int = 1,
        wait_for_completion: bool = True
    ) -> Dict[str, Any]:
        """
        Create variation of specific image

        Args:
            job_id: Original generation job ID
            index: Image index for variation (1-4)
            wait_for_completion: Wait for variation to complete

        Returns:
            Variation result
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "job_id": job_id,
            "index": index
        }

        try:
            response = requests.post(
                f"{self.api_url}/variation",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            variation_job_id = data.get("job_id") or data.get("id")

            if wait_for_completion:
                return self._wait_for_completion(variation_job_id, timeout=300)
            else:
                return {
                    "success": True,
                    "job_id": variation_job_id,
                    "status": "submitted"
                }

        except requests.exceptions.RequestException as e:
            logger.error("variation_error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }


def create_midjourney_langchain_tool():
    """Create LangChain-compatible Midjourney tool"""
    from langchain.tools import Tool

    midjourney = MidjourneyTool()

    def midjourney_wrapper(prompt: str) -> str:
        """Generate image with Midjourney"""
        result = midjourney.generate(
            prompt=prompt,
            wait_for_completion=True,
            timeout=300
        )

        if result.get("success"):
            image_url = result.get("image_url", "")
            job_id = result.get("job_id", "")
            cost = result.get("cost", 0)

            return f"""Image generated successfully!

Job ID: {job_id}
URL: {image_url}
Cost: ${cost:.3f}
Provider: Midjourney

The image is a 2x2 grid. Use upscale or variation actions for specific images."""
        else:
            return f"Image generation failed: {result.get('error', 'Unknown error')}"

    return Tool(
        name="Midjourney_Image_Generator",
        func=midjourney_wrapper,
        description="Generate artistic, high-quality images using Midjourney. "
                    "Input should be a detailed, artistic image description. "
                    "Best for creative, stylized visuals. "
                    "Returns 2x2 grid of variations. "
                    "Cost varies by subscription tier."
    )


if __name__ == "__main__":
    # Test Midjourney tool
    midjourney = MidjourneyTool()

    result = midjourney.generate(
        prompt="Professional marketing team brainstorming, modern office, vibrant colors, digital art style",
        aspect_ratio="16:9",
        stylize=150
    )

    if result.get("success"):
        print(f"✓ Image generated: {result.get('image_url')}")
        print(f"Job ID: {result.get('job_id')}")
        print(f"Cost: ${result.get('cost', 0):.3f}")
    else:
        print(f"✗ Generation failed: {result.get('error')}")
