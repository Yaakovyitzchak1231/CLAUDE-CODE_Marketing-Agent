"""
Pika Video Generation Tool
Wrapper for Pika AI video generation API
"""

import requests
from typing import Dict, List, Optional, Any
import time
import structlog
from config import settings

logger = structlog.get_logger()


class PikaTool:
    """
    Pika AI video generation wrapper

    Features:
    - Text-to-video generation
    - Image-to-video animation
    - Video extension and editing
    - Flexible durations
    - Camera control
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Pika tool

        Args:
            api_key: Pika API key
        """
        self.api_key = api_key or settings.PIKA_API_KEY
        if not self.api_key:
            logger.warning("pika_api_key_not_set")

        self.base_url = settings.PIKA_API_URL or "https://api.pika.art/v1"

        logger.info("pika_tool_initialized")

    def generate_text_to_video(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        duration: int = 3,
        aspect_ratio: str = "16:9",
        motion_strength: int = 3,
        camera_motion: Optional[str] = None,
        wait_for_completion: bool = True,
        timeout: int = 600
    ) -> Dict[str, Any]:
        """
        Generate video from text prompt

        Args:
            prompt: Video description
            negative_prompt: What to avoid in video
            duration: Video duration in seconds (1-10)
            aspect_ratio: Aspect ratio (16:9, 9:16, 1:1, 4:3)
            motion_strength: Motion intensity (1-5)
            camera_motion: Camera movement (pan_left, pan_right, zoom_in, zoom_out, etc.)
            wait_for_completion: Wait for generation to complete
            timeout: Max wait time in seconds

        Returns:
            Dict with video URL and metadata
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt,
            "duration": duration,
            "aspectRatio": aspect_ratio,
            "motionStrength": motion_strength
        }

        if negative_prompt:
            payload["negativePrompt"] = negative_prompt

        if camera_motion:
            payload["cameraMotion"] = camera_motion

        try:
            logger.info(
                "generating_pika_video",
                prompt_length=len(prompt),
                duration=duration,
                aspect_ratio=aspect_ratio
            )

            # Submit generation request
            response = requests.post(
                f"{self.base_url}/generate",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            job_id = data.get("id") or data.get("jobId")

            if not job_id:
                return {
                    "success": False,
                    "error": "No job ID returned",
                    "prompt": prompt
                }

            logger.info("pika_job_submitted", job_id=job_id)

            # Wait for completion if requested
            if wait_for_completion:
                return self._wait_for_completion(job_id, timeout)
            else:
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": "submitted",
                    "prompt": prompt,
                    "duration": duration
                }

        except requests.exceptions.RequestException as e:
            logger.error("pika_generation_error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }

    def generate_image_to_video(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        duration: int = 3,
        motion_strength: int = 3,
        camera_motion: Optional[str] = None,
        wait_for_completion: bool = True
    ) -> Dict[str, Any]:
        """
        Animate an image into video

        Args:
            image_url: URL of image to animate
            prompt: Optional motion guidance
            duration: Video duration in seconds
            motion_strength: Motion intensity (1-5)
            camera_motion: Camera movement type
            wait_for_completion: Wait for completion

        Returns:
            Dict with video result
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "imageUrl": image_url,
            "duration": duration,
            "motionStrength": motion_strength
        }

        if prompt:
            payload["prompt"] = prompt

        if camera_motion:
            payload["cameraMotion"] = camera_motion

        try:
            response = requests.post(
                f"{self.base_url}/generate/image-to-video",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            job_id = data.get("id") or data.get("jobId")

            if wait_for_completion:
                return self._wait_for_completion(job_id, timeout=600)
            else:
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": "submitted"
                }

        except requests.exceptions.RequestException as e:
            logger.error("image_to_video_error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def extend_video(
        self,
        video_url: str,
        extend_seconds: int = 3,
        prompt: Optional[str] = None,
        wait_for_completion: bool = True
    ) -> Dict[str, Any]:
        """
        Extend existing video

        Args:
            video_url: URL of video to extend
            extend_seconds: Seconds to add
            prompt: Optional guidance for extension
            wait_for_completion: Wait for completion

        Returns:
            Dict with extended video result
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "videoUrl": video_url,
            "extendSeconds": extend_seconds
        }

        if prompt:
            payload["prompt"] = prompt

        try:
            response = requests.post(
                f"{self.base_url}/extend",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            job_id = data.get("id") or data.get("jobId")

            if wait_for_completion:
                return self._wait_for_completion(job_id, timeout=600)
            else:
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": "submitted"
                }

        except requests.exceptions.RequestException as e:
            logger.error("video_extend_error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def _wait_for_completion(
        self,
        job_id: str,
        timeout: int = 600
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
        poll_interval = 10  # seconds

        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f"{self.base_url}/jobs/{job_id}",
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()

                data = response.json()
                status = data.get("status")

                logger.debug("job_status_check", job_id=job_id, status=status)

                if status == "completed":
                    # Calculate cost
                    duration = data.get("duration", 3)
                    cost = self._calculate_cost(duration)

                    return {
                        "success": True,
                        "job_id": job_id,
                        "status": "completed",
                        "video_url": data.get("videoUrl") or data.get("url"),
                        "thumbnail_url": data.get("thumbnailUrl"),
                        "prompt": data.get("prompt"),
                        "duration": duration,
                        "aspect_ratio": data.get("aspectRatio"),
                        "cost": cost,
                        "provider": "pika"
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

    def _calculate_cost(self, duration: int) -> float:
        """
        Calculate cost based on duration

        Pika pricing (approximate):
        - Standard: ~$0.07 per second
        - Pro: ~$0.05 per second (subscription)

        Actual pricing varies by subscription tier
        """
        return duration * 0.07

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get status of generation job

        Args:
            job_id: Job identifier

        Returns:
            Job status info
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.get(
                f"{self.base_url}/jobs/{job_id}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error("status_check_error", error=str(e))
            return {
                "error": str(e)
            }


def create_pika_langchain_tool():
    """Create LangChain-compatible Pika tool"""
    from langchain.tools import Tool

    pika = PikaTool()

    def pika_wrapper(prompt: str) -> str:
        """Generate video with Pika"""
        result = pika.generate_text_to_video(
            prompt=prompt,
            duration=3,
            wait_for_completion=True,
            timeout=600
        )

        if result.get("success"):
            video_url = result.get("video_url", "")
            job_id = result.get("job_id", "")
            duration = result.get("duration", 0)
            cost = result.get("cost", 0)

            return f"""Video generated successfully!

Job ID: {job_id}
Video URL: {video_url}
Duration: {duration} seconds
Aspect Ratio: {result.get('aspect_ratio', 'N/A')}
Cost: ${cost:.2f}
Provider: Pika AI

Download the video from the URL above."""
        else:
            return f"Video generation failed: {result.get('error', 'Unknown error')}"

    return Tool(
        name="Pika_Video_Generator",
        func=pika_wrapper,
        description="Generate flexible, creative videos from text prompts using Pika AI. "
                    "Input should be a detailed video description with motion and camera details. "
                    "Generates 1-10 second clips. "
                    "Supports camera motions and aspect ratios. "
                    "Cost: ~$0.07 per second of video."
    )


if __name__ == "__main__":
    # Test Pika tool
    pika = PikaTool()

    result = pika.generate_text_to_video(
        prompt="Professional product showcase, slowly rotating product on clean background, studio lighting",
        duration=3,
        aspect_ratio="16:9",
        camera_motion="zoom_in"
    )

    if result.get("success"):
        print(f"✓ Video generated: {result.get('video_url')}")
        print(f"Job ID: {result.get('job_id')}")
        print(f"Duration: {result.get('duration')}s")
        print(f"Cost: ${result.get('cost', 0):.2f}")
    else:
        print(f"✗ Generation failed: {result.get('error')}")
