"""
Runway ML Video Generation Tool
Wrapper for Runway ML Gen-2 and Gen-3 APIs
"""

import requests
from typing import Dict, List, Optional, Any
import time
import structlog
from config import settings

logger = structlog.get_logger()


class RunwayTool:
    """
    Runway ML video generation wrapper

    Features:
    - Text-to-video generation
    - Image-to-video animation
    - Video-to-video transformation
    - Multiple duration options
    - Quality settings
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Runway tool

        Args:
            api_key: Runway ML API key
        """
        self.api_key = api_key or settings.RUNWAY_API_KEY
        if not self.api_key:
            logger.warning("runway_api_key_not_set")

        self.base_url = "https://api.runwayml.com/v1"

        logger.info("runway_tool_initialized")

    def generate_text_to_video(
        self,
        prompt: str,
        duration: int = 4,
        resolution: str = "1280x768",
        model: str = "gen3",
        wait_for_completion: bool = True,
        timeout: int = 600
    ) -> Dict[str, Any]:
        """
        Generate video from text prompt

        Args:
            prompt: Video description
            duration: Video duration in seconds (4-16)
            resolution: Video resolution (1280x768, 1920x1080)
            model: Model version (gen2, gen3)
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
            "model": model,
            "prompt": prompt,
            "duration": duration,
            "resolution": resolution,
            "seed": None  # Random seed for variation
        }

        try:
            logger.info(
                "generating_runway_video",
                prompt_length=len(prompt),
                duration=duration,
                model=model
            )

            # Submit generation request
            response = requests.post(
                f"{self.base_url}/generations",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            task_id = data.get("id") or data.get("task_id")

            if not task_id:
                return {
                    "success": False,
                    "error": "No task ID returned",
                    "prompt": prompt
                }

            logger.info("runway_task_submitted", task_id=task_id)

            # Wait for completion if requested
            if wait_for_completion:
                return self._wait_for_completion(task_id, timeout)
            else:
                return {
                    "success": True,
                    "task_id": task_id,
                    "status": "submitted",
                    "prompt": prompt,
                    "duration": duration
                }

        except requests.exceptions.RequestException as e:
            logger.error("runway_generation_error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }

    def generate_image_to_video(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        duration: int = 4,
        motion_amount: int = 5,
        wait_for_completion: bool = True
    ) -> Dict[str, Any]:
        """
        Animate an image into video

        Args:
            image_url: URL of image to animate
            prompt: Optional motion description
            duration: Video duration in seconds
            motion_amount: Amount of motion (1-10)
            wait_for_completion: Wait for completion

        Returns:
            Dict with video result
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gen3",
            "image_url": image_url,
            "duration": duration,
            "motion_amount": motion_amount
        }

        if prompt:
            payload["prompt"] = prompt

        try:
            response = requests.post(
                f"{self.base_url}/generations/image-to-video",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            task_id = data.get("id") or data.get("task_id")

            if wait_for_completion:
                return self._wait_for_completion(task_id, timeout=600)
            else:
                return {
                    "success": True,
                    "task_id": task_id,
                    "status": "submitted"
                }

        except requests.exceptions.RequestException as e:
            logger.error("image_to_video_error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def _wait_for_completion(
        self,
        task_id: str,
        timeout: int = 600
    ) -> Dict[str, Any]:
        """
        Poll for task completion

        Args:
            task_id: Task identifier
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
                    f"{self.base_url}/generations/{task_id}",
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()

                data = response.json()
                status = data.get("status")

                logger.debug("task_status_check", task_id=task_id, status=status)

                if status == "succeeded":
                    # Calculate cost
                    duration = data.get("duration", 4)
                    cost = self._calculate_cost(duration, data.get("model", "gen3"))

                    return {
                        "success": True,
                        "task_id": task_id,
                        "status": "completed",
                        "video_url": data.get("url") or data.get("output_url"),
                        "thumbnail_url": data.get("thumbnail_url"),
                        "prompt": data.get("prompt"),
                        "duration": duration,
                        "resolution": data.get("resolution"),
                        "cost": cost,
                        "provider": "runway"
                    }

                elif status in ["failed", "error"]:
                    return {
                        "success": False,
                        "task_id": task_id,
                        "status": status,
                        "error": data.get("error", "Generation failed")
                    }

                # Still processing
                time.sleep(poll_interval)

            except requests.exceptions.RequestException as e:
                logger.error("task_status_error", error=str(e), task_id=task_id)
                time.sleep(poll_interval)

        # Timeout reached
        logger.warning("task_timeout", task_id=task_id, timeout=timeout)
        return {
            "success": False,
            "task_id": task_id,
            "status": "timeout",
            "error": f"Generation timeout after {timeout} seconds"
        }

    def _calculate_cost(self, duration: int, model: str) -> float:
        """
        Calculate cost based on duration and model

        Runway ML pricing (approximate):
        - Gen-2: ~$0.05 per second
        - Gen-3: ~$0.10 per second

        Actual pricing varies by subscription tier
        """
        if model == "gen3":
            return duration * 0.10
        else:  # gen2
            return duration * 0.05

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get status of generation task

        Args:
            task_id: Task identifier

        Returns:
            Task status info
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.get(
                f"{self.base_url}/generations/{task_id}",
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


def create_runway_langchain_tool():
    """Create LangChain-compatible Runway tool"""
    from langchain.tools import Tool

    runway = RunwayTool()

    def runway_wrapper(prompt: str) -> str:
        """Generate video with Runway ML"""
        result = runway.generate_text_to_video(
            prompt=prompt,
            duration=4,
            wait_for_completion=True,
            timeout=600
        )

        if result.get("success"):
            video_url = result.get("video_url", "")
            task_id = result.get("task_id", "")
            duration = result.get("duration", 0)
            cost = result.get("cost", 0)

            return f"""Video generated successfully!

Task ID: {task_id}
Video URL: {video_url}
Duration: {duration} seconds
Resolution: {result.get('resolution', 'N/A')}
Cost: ${cost:.2f}
Provider: Runway ML

Download the video from the URL above."""
        else:
            return f"Video generation failed: {result.get('error', 'Unknown error')}"

    return Tool(
        name="Runway_Video_Generator",
        func=runway_wrapper,
        description="Generate high-quality videos from text prompts using Runway ML Gen-3. "
                    "Input should be a detailed video description including motion, scene, and style. "
                    "Generates 4-16 second clips. "
                    "Cost: ~$0.10 per second of video."
    )


if __name__ == "__main__":
    # Test Runway tool
    runway = RunwayTool()

    result = runway.generate_text_to_video(
        prompt="Professional business team collaborating in modern office, camera slowly pans across room, natural lighting, 4K quality",
        duration=4,
        resolution="1280x768"
    )

    if result.get("success"):
        print(f"✓ Video generated: {result.get('video_url')}")
        print(f"Task ID: {result.get('task_id')}")
        print(f"Duration: {result.get('duration')}s")
        print(f"Cost: ${result.get('cost', 0):.2f}")
    else:
        print(f"✗ Generation failed: {result.get('error')}")
