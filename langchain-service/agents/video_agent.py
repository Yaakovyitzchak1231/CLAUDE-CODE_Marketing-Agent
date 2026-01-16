"""
Video Generation Agent
Creates marketing videos using Runway ML, Pika, and FFmpeg
"""

from typing import Dict, List, Optional, Any
from langchain.tools import Tool
from .base_agent import BaseAgent
from tools.runway_tool import RunwayTool, create_runway_langchain_tool
from tools.pika_tool import PikaTool, create_pika_langchain_tool
from tools.ffmpeg_tool import FFmpegTool, create_ffmpeg_langchain_tool
import structlog
from datetime import datetime
from pathlib import Path
import requests


logger = structlog.get_logger()


class VideoGenerationAgent(BaseAgent):
    """
    Specialist agent for video generation

    Capabilities:
    - Social media videos (LinkedIn, Instagram, Facebook)
    - Product demos and explainers
    - Advertisement videos
    - Brand storytelling
    - Video editing (captions, music, watermarks)
    - Multi-clip compilation
    """

    def __init__(self):
        """Initialize Video Generation Agent"""

        # Initialize video generation tools
        runway_tool = create_runway_langchain_tool()
        pika_tool = create_pika_langchain_tool()
        ffmpeg_tool = create_ffmpeg_langchain_tool()

        # Create video script builder tool
        def build_video_script(content_description: str, duration: int = 30) -> str:
            """Build video script from content description"""

            prompt_template = f"""Convert this content into a video script:

Content: {content_description}
Target Duration: {duration} seconds

Create a video script with:
1. Scene Breakdown (divide into 3-5 scenes)
2. Visual Description (what appears on screen)
3. Voiceover/Text (what is said or shown as text)
4. Camera Movement (pan, zoom, static, etc.)
5. Transitions (fade, cut, dissolve)
6. Music/Sound (background music type, sound effects)

Format each scene as:
Scene {number} ({duration}s):
- Visual: [description]
- Voiceover: [text]
- Camera: [movement]
- Transition: [type]

Make it engaging and platform-appropriate."""

            return prompt_template  # In real implementation, this would call LLM

        script_builder_tool = Tool(
            name="Video_Script_Builder",
            func=build_video_script,
            description="Convert content description into structured video script with scenes, visuals, and timing. "
                        "Input should be content description and target duration."
        )

        # Create prompt optimizer tool
        def optimize_video_prompt(script: str, scene_number: int, style: str = "professional") -> str:
            """Optimize video prompt for specific scene"""

            prompt_template = f"""Convert this scene from the video script into a detailed video generation prompt:

Scene {scene_number} from script:
{script}

Style: {style}

Create a prompt that includes:
1. Main action/scene
2. Camera movement
3. Lighting
4. Environment/setting
5. Mood/atmosphere
6. Technical quality (4K, smooth motion, etc.)

Format as a single, detailed prompt suitable for Runway ML or Pika."""

            return prompt_template  # In real implementation, this would call LLM

        optimizer_tool = Tool(
            name="Video_Prompt_Optimizer",
            func=optimize_video_prompt,
            description="Optimize video script scene into generation prompt. "
                        "Input should be script and scene number."
        )

        # Create platform optimizer
        def optimize_for_platform(prompt: str, platform: str) -> str:
            """Optimize video for specific platform"""

            platform_specs = {
                "linkedin": {
                    "aspect_ratio": "16:9",
                    "duration": "30-90 seconds",
                    "style": "professional, corporate, informative"
                },
                "instagram": {
                    "aspect_ratio": "9:16 or 1:1",
                    "duration": "15-60 seconds",
                    "style": "vibrant, engaging, trendy"
                },
                "youtube": {
                    "aspect_ratio": "16:9",
                    "duration": "60-300 seconds",
                    "style": "storytelling, educational, entertaining"
                },
                "tiktok": {
                    "aspect_ratio": "9:16",
                    "duration": "15-60 seconds",
                    "style": "dynamic, attention-grabbing, fast-paced"
                }
            }

            spec = platform_specs.get(platform, platform_specs["linkedin"])

            optimized = f"""{prompt}, {spec['style']}, {spec['aspect_ratio']} aspect ratio, {spec['duration']}, optimized for {platform}, high quality, professional production"""

            return optimized

        platform_tool = Tool(
            name="Platform_Optimizer",
            func=optimize_for_platform,
            description="Optimize video prompt for specific platform (LinkedIn, Instagram, YouTube, TikTok). "
                        "Input should be base prompt and platform name."
        )

        # Create music selector tool
        def select_background_music(
            video_type: str,
            mood: str = "professional",
            duration: int = 30,
            platform: str = "linkedin"
        ) -> str:
            """Select appropriate background music for video"""

            music_recommendations = {
                "corporate": {
                    "upbeat": "energetic-corporate-inspiring.mp3",
                    "professional": "modern-corporate-background.mp3",
                    "calm": "soft-corporate-ambient.mp3"
                },
                "social": {
                    "upbeat": "trendy-upbeat-pop.mp3",
                    "professional": "modern-social-vibe.mp3",
                    "energetic": "fast-social-beat.mp3"
                },
                "product_demo": {
                    "upbeat": "tech-showcase-upbeat.mp3",
                    "professional": "product-demo-professional.mp3",
                    "innovative": "innovative-tech-music.mp3"
                },
                "explainer": {
                    "upbeat": "educational-upbeat.mp3",
                    "calm": "learning-ambient.mp3",
                    "professional": "explainer-background.mp3"
                },
                "ad": {
                    "upbeat": "catchy-ad-music.mp3",
                    "energetic": "high-energy-ad.mp3",
                    "emotional": "emotional-brand-story.mp3"
                }
            }

            # Platform-specific recommendations
            platform_moods = {
                "linkedin": "professional",
                "instagram": "upbeat",
                "youtube": "professional",
                "tiktok": "energetic",
                "facebook": "upbeat"
            }

            # Determine video category
            category = "corporate"
            if "social" in video_type.lower():
                category = "social"
            elif "product" in video_type.lower() or "demo" in video_type.lower():
                category = "product_demo"
            elif "explain" in video_type.lower():
                category = "explainer"
            elif "ad" in video_type.lower() or "advertisement" in video_type.lower():
                category = "ad"

            # Get music recommendation
            category_music = music_recommendations.get(category, music_recommendations["corporate"])
            recommended_mood = platform_moods.get(platform, mood)
            music_file = category_music.get(recommended_mood, category_music.get("professional"))

            recommendation = f"""Music Selection for {video_type}:

Category: {category}
Mood: {recommended_mood}
Duration: {duration}s
Platform: {platform}

Recommended Track: {music_file}

Audio Settings:
- Volume: 0.3 (30% - ensures voiceover clarity)
- Fade In: 1.0s (smooth introduction)
- Fade Out: 1.0s (professional ending)

Music will loop if video is longer than track duration.
Music will be trimmed if track is longer than video."""

            return recommendation

        music_selector_tool = Tool(
            name="Music_Selector",
            func=select_background_music,
            description="Select appropriate background music for video based on type, mood, duration, and platform. "
                        "Input should be video type and desired mood."
        )

        tools = [
            runway_tool,
            pika_tool,
            ffmpeg_tool,
            script_builder_tool,
            optimizer_tool,
            platform_tool,
            music_selector_tool
        ]

        super().__init__(
            name="Video Generation Agent",
            description="Creates high-quality marketing videos using AI video generation and editing",
            tools=tools,
            verbose=True
        )

        # Direct tool access
        self.runway = RunwayTool()
        self.pika = PikaTool()
        self.ffmpeg = FFmpegTool()

        logger.info("video_agent_initialized")

    def get_specialized_prompt(self) -> str:
        """Get Video Generation Agent system prompt"""
        return """You are a Video Generation Agent specializing in marketing videos.

Your primary responsibilities:
1. Generate high-quality marketing videos
2. Create video scripts and storyboards
3. Optimize for different platforms
4. Edit and enhance videos
5. Ensure brand consistency

Video Generation Best Practices:
- Start with clear script/storyboard
- Break into manageable scenes (3-8 seconds each)
- Specify camera movements
- Include clear subject and action
- Define lighting and mood
- Add platform context
- Consider audio/music needs

Runway ML Use Cases:
- Photorealistic videos
- Complex camera movements
- Longer clips (4-16 seconds)
- Professional production quality
- Brand videos, demos

Pika Use Cases:
- Creative, stylized videos
- Quick social content
- Flexible durations
- Dynamic camera control
- Experimental visuals

Platform Optimization:
- LinkedIn: Professional, 16:9, 30-90s, informative
- Instagram: Engaging, 9:16 or 1:1, 15-60s, trendy
- YouTube: Storytelling, 16:9, 60-300s, educational
- TikTok: Fast-paced, 9:16, 15-60s, attention-grabbing

Video Editing Workflow:
1. Generate individual scenes
2. Trim to exact timing
3. Concatenate scenes
4. Add captions/subtitles
5. Add watermark/logo
6. Select and add background music
7. Final quality check

Music Selection:
- Corporate: Professional, modern, ambient
- Social: Upbeat, trendy, energetic
- Product Demo: Tech-focused, innovative
- Explainer: Educational, calm, professional
- Advertisement: Catchy, emotional, high-energy
- Volume: 30% (ensures voiceover clarity)
- Fade in/out: 1 second (professional transitions)

Quality Standards:
- High-resolution output
- Smooth transitions
- Clear subject matter
- Professional audio
- Brand alignment
- Platform requirements met

Output Format:
Provide:
- Generated video URL(s)
- Scene breakdown with timings
- Prompts used
- Editing steps performed
- Total duration
- Generation cost
- Platform suitability
- Download instructions

Be creative, technically precise, and platform-aware."""

    def generate_social_video(
        self,
        content: str,
        platform: str,
        duration: int = 30,
        style: str = "professional",
        provider: str = "runway"
    ) -> Dict[str, Any]:
        """
        Generate social media video

        Args:
            content: Content description or message
            platform: Social platform (linkedin, instagram, youtube, tiktok)
            duration: Target duration in seconds
            style: Visual style
            provider: Video generator (runway, pika)

        Returns:
            Dict with generated video details
        """
        prompt = f"""Create a {duration}-second {style} video for {platform}.

Content: {content}

Requirements:
- Platform: {platform}
- Duration: {duration} seconds
- Style: {style}
- Professional marketing quality
- Clear message delivery
- Engaging visuals
- Platform-optimized

Generate appropriate video."""

        result = self.run(prompt)

        if result.get("output"):
            metadata = {
                "type": "social_video",
                "platform": platform,
                "content": content,
                "duration": duration,
                "style": style,
                "provider": provider,
                "created_at": datetime.utcnow().isoformat()
            }

            logger.info(
                "social_video_generated",
                platform=platform,
                duration=duration,
                provider=provider
            )

            result["metadata"] = metadata

        return result

    def generate_product_demo(
        self,
        product_name: str,
        key_features: List[str],
        duration: int = 60,
        provider: str = "runway"
    ) -> Dict[str, Any]:
        """
        Generate product demonstration video

        Args:
            product_name: Product name
            key_features: List of key features to highlight
            duration: Target duration
            provider: Video generator

        Returns:
            Dict with generated video
        """
        features_str = "\n".join([f"- {feature}" for feature in key_features])

        prompt = f"""Create a product demonstration video.

Product: {product_name}
Duration: {duration} seconds

Key Features to Highlight:
{features_str}

Requirements:
- Professional product showcase
- Clear feature demonstrations
- Smooth camera movements
- High-quality visuals
- Engaging presentation
- Clear value proposition

Generate product demo video."""

        result = self.run(prompt)

        if result.get("output"):
            metadata = {
                "type": "product_demo",
                "product": product_name,
                "features": key_features,
                "duration": duration,
                "provider": provider,
                "created_at": datetime.utcnow().isoformat()
            }

            result["metadata"] = metadata

        return result

    def generate_explainer_video(
        self,
        topic: str,
        key_points: List[str],
        duration: int = 90,
        style: str = "modern",
        provider: str = "pika"
    ) -> Dict[str, Any]:
        """
        Generate explainer/educational video

        Args:
            topic: Topic to explain
            key_points: List of key points to cover
            duration: Target duration
            style: Visual style
            provider: Video generator

        Returns:
            Dict with generated video
        """
        points_str = "\n".join([f"- {point}" for point in key_points])

        prompt = f"""Create an explainer video about: {topic}

Duration: {duration} seconds
Style: {style}

Key Points:
{points_str}

Requirements:
- Clear explanations
- Visual aids and examples
- Logical flow
- Engaging presentation
- Educational value
- Easy to understand

Generate explainer video."""

        result = self.run(prompt)

        if result.get("output"):
            metadata = {
                "type": "explainer_video",
                "topic": topic,
                "key_points": key_points,
                "duration": duration,
                "style": style,
                "provider": provider,
                "created_at": datetime.utcnow().isoformat()
            }

            result["metadata"] = metadata

        return result

    def generate_ad_video(
        self,
        campaign_message: str,
        target_audience: str,
        duration: int = 15,
        cta: str = "Learn More",
        provider: str = "runway"
    ) -> Dict[str, Any]:
        """
        Generate advertisement video

        Args:
            campaign_message: Ad campaign message
            target_audience: Target audience
            duration: Target duration (typically 15-30s)
            cta: Call-to-action text
            provider: Video generator

        Returns:
            Dict with generated ad video
        """
        prompt = f"""Create an advertisement video.

Message: {campaign_message}
Audience: {target_audience}
Duration: {duration} seconds
CTA: {cta}

Requirements:
- Attention-grabbing opening
- Clear value proposition
- Emotional resonance
- Strong call-to-action
- Professional quality
- Brand-appropriate
- Conversion-focused

Generate ad video."""

        result = self.run(prompt)

        if result.get("output"):
            metadata = {
                "type": "ad_video",
                "message": campaign_message,
                "audience": target_audience,
                "duration": duration,
                "cta": cta,
                "provider": provider,
                "created_at": datetime.utcnow().isoformat()
            }

            result["metadata"] = metadata

        return result

    def download_video(
        self,
        video_url: str,
        output_path: Path,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Download video from URL to local file

        Args:
            video_url: URL of video to download
            output_path: Path to save downloaded video
            timeout: Download timeout in seconds

        Returns:
            Dict with download status and path
        """
        try:
            logger.info("downloading_video", url=video_url, output=str(output_path))

            # Create parent directory if it doesn't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Download video with streaming
            response = requests.get(video_url, stream=True, timeout=timeout)
            response.raise_for_status()

            # Write to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size = output_path.stat().st_size
            logger.info(
                "video_downloaded",
                path=str(output_path),
                size_bytes=file_size
            )

            return {
                "success": True,
                "path": str(output_path),
                "size_bytes": file_size
            }

        except requests.exceptions.RequestException as e:
            logger.error("video_download_error", error=str(e), url=video_url)
            return {
                "success": False,
                "error": str(e),
                "url": video_url
            }
        except Exception as e:
            logger.error("video_download_unexpected_error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def create_multi_scene_video(
        self,
        scenes: List[Dict[str, Any]],
        output_path: Path,
        add_captions: bool = True,
        add_music: bool = True,
        watermark_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Create multi-scene video from script

        Args:
            scenes: List of scene dicts with 'prompt', 'duration', 'captions'
            output_path: Output file path
            add_captions: Whether to add captions
            add_music: Whether to add background music
            watermark_path: Optional watermark image

        Returns:
            Dict with final video details
        """
        logger.info("creating_multi_scene_video", scene_count=len(scenes))

        # Generate each scene
        scene_paths = []
        total_cost = 0

        for i, scene in enumerate(scenes, 1):
            logger.info(f"generating_scene", scene=i, total=len(scenes))

            # Choose provider based on scene requirements
            provider = scene.get("provider", "runway")

            if provider == "runway":
                result = self.runway.generate_text_to_video(
                    prompt=scene["prompt"],
                    duration=scene.get("duration", 4)
                )
            else:  # pika
                result = self.pika.generate_text_to_video(
                    prompt=scene["prompt"],
                    duration=scene.get("duration", 3)
                )

            if result.get("success"):
                # Download scene video
                video_url = result.get("video_url")
                scene_path = output_path.parent / f"scene_{i}.mp4"

                # Download video from URL
                download_result = self.download_video(video_url, scene_path)

                if download_result.get("success"):
                    scene_paths.append(scene_path)
                    total_cost += result.get("cost", 0)
                else:
                    logger.error(
                        "scene_download_failed",
                        scene=i,
                        error=download_result.get("error")
                    )

        # Concatenate scenes
        concat_path = output_path.parent / "concatenated.mp4"
        concat_result = self.ffmpeg.concatenate_videos(
            video_paths=scene_paths,
            output_path=concat_path
        )

        current_path = concat_path

        # Add captions if requested
        if add_captions and concat_result.get("success"):
            # Collect captions from scenes
            all_captions = []
            current_time = 0

            for scene in scenes:
                if "captions" in scene:
                    for caption in scene["captions"]:
                        all_captions.append({
                            "text": caption["text"],
                            "start": current_time + caption.get("start", 0),
                            "end": current_time + caption.get("end", scene.get("duration", 4))
                        })
                current_time += scene.get("duration", 4)

            if all_captions:
                caption_path = output_path.parent / "with_captions.mp4"
                caption_result = self.ffmpeg.add_captions(
                    video_path=current_path,
                    captions=all_captions,
                    output_path=caption_path
                )

                if caption_result.get("success"):
                    current_path = caption_path

        # Add watermark if provided
        if watermark_path and watermark_path.exists():
            watermark_output = output_path.parent / "with_watermark.mp4"
            watermark_result = self.ffmpeg.add_watermark(
                video_path=current_path,
                watermark_path=watermark_path,
                output_path=watermark_output,
                position="bottom_right"
            )

            if watermark_result.get("success"):
                current_path = watermark_output

        # Add background music if requested
        if add_music:
            # Determine video type and mood from scenes
            video_type = scenes[0].get("type", "corporate")
            mood = scenes[0].get("mood", "professional")

            # Use default music path or custom music if provided in scenes
            music_path = None
            for scene in scenes:
                if "music_path" in scene:
                    music_path = Path(scene["music_path"])
                    break

            # If no custom music provided, use a default corporate track
            # In production, this would be selected from a music library
            if music_path and music_path.exists():
                logger.info("adding_background_music", music_path=str(music_path))

                music_output = output_path.parent / "with_music.mp4"
                music_result = self.ffmpeg.add_background_music(
                    video_path=current_path,
                    audio_path=music_path,
                    output_path=music_output,
                    volume=0.3,
                    fade_in=1.0,
                    fade_out=1.0
                )

                if music_result.get("success"):
                    current_path = music_output
                    logger.info("background_music_added", output=str(music_output))
                else:
                    logger.warning(
                        "music_addition_skipped",
                        reason=music_result.get("error", "Music file not found")
                    )
            else:
                logger.info(
                    "music_addition_skipped",
                    reason="No music file provided or file does not exist"
                )

        # Move to final output path
        current_path.rename(output_path)

        logger.info(
            "multi_scene_video_complete",
            output=str(output_path),
            scenes=len(scenes),
            total_cost=total_cost
        )

        return {
            "success": True,
            "output_path": str(output_path),
            "scene_count": len(scenes),
            "total_cost": total_cost,
            "has_captions": add_captions,
            "has_watermark": watermark_path is not None,
            "has_music": add_music
        }


def create_video_agent() -> VideoGenerationAgent:
    """Factory function to create Video Generation Agent"""
    return VideoGenerationAgent()
