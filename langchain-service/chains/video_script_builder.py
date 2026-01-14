"""
Video Script Builder Chain
Sequential chain for converting content to video scripts with scene breakdowns
"""

from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate
from typing import Dict, Any, Optional, List
import structlog
import json

logger = structlog.get_logger()


class VideoScriptBuilderChain:
    """
    Sequential chain for building video scripts

    Process:
    1. Analyze content and define video structure
    2. Create narrative arc
    3. Break into scenes with timing
    4. Write detailed scene descriptions
    5. Add voiceover/dialogue
    6. Specify camera movements
    7. Add music/sound recommendations
    8. Generate prompts for each scene
    """

    def __init__(self, llm):
        """
        Initialize Video Script Builder Chain

        Args:
            llm: Language model instance
        """
        self.llm = llm
        self.chain = self._build_chain()

        logger.info("video_script_builder_initialized")

    def _build_chain(self) -> SequentialChain:
        """Build sequential video script building chain"""

        # Step 1: Video Structure Analysis
        structure_prompt = PromptTemplate(
            input_variables=["content", "duration", "video_type"],
            template="""Analyze content and define video structure:

Content:
{content}

Target Duration: {duration} seconds
Video Type: {video_type}

Define:
1. Video objective (what should viewers learn/feel/do)
2. Target audience
3. Key messages (3-5 main points)
4. Call-to-action
5. Optimal number of scenes (based on duration)
6. Pacing strategy (fast, moderate, slow)

VIDEO STRUCTURE:"""
        )

        structure_chain = LLMChain(
            llm=self.llm,
            prompt=structure_prompt,
            output_key="video_structure"
        )

        # Step 2: Narrative Arc
        narrative_prompt = PromptTemplate(
            input_variables=["video_structure", "content"],
            template="""Create narrative arc for video:

Video Structure:
{video_structure}

Content:
{content}

Create narrative arc following this structure:
1. Hook (first 3-5 seconds): Grab attention immediately
2. Context (5-10%): Establish problem/situation
3. Content (60-70%): Deliver main value/information
4. Climax/Resolution (10-15%): Key insight or solution
5. Call-to-Action (last 5-10%): Clear next step

For each section, describe:
- Purpose
- Key message
- Emotional tone
- Transition to next section

NARRATIVE ARC:"""
        )

        narrative_chain = LLMChain(
            llm=self.llm,
            prompt=narrative_prompt,
            output_key="narrative_arc"
        )

        # Step 3: Scene Breakdown
        scene_breakdown_prompt = PromptTemplate(
            input_variables=["narrative_arc", "duration", "video_type"],
            template="""Break narrative into specific scenes:

Narrative Arc:
{narrative_arc}

Total Duration: {duration} seconds
Video Type: {video_type}

Create scene-by-scene breakdown:

For each scene, specify:
- Scene number
- Duration (in seconds)
- Purpose (what this scene accomplishes)
- Main action/content
- Transition to next scene

Aim for 3-8 scenes total (each scene 3-15 seconds).
First and last scenes should be shorter (hook and CTA).

Format:
Scene 1 (X seconds): [Purpose]
- [Description]
- Transition: [type]

SCENE BREAKDOWN:"""
        )

        scene_breakdown_chain = LLMChain(
            llm=self.llm,
            prompt=scene_breakdown_prompt,
            output_key="scene_breakdown"
        )

        # Step 4: Detailed Scene Descriptions
        scene_details_prompt = PromptTemplate(
            input_variables=["scene_breakdown", "video_type", "style"],
            template="""Write detailed scene descriptions:

Scene Breakdown:
{scene_breakdown}

Video Type: {video_type}
Visual Style: {style}

For each scene, provide:
1. Visual Description
   - What appears on screen
   - Environment/setting
   - Characters/objects (if any)
   - Visual style and aesthetics

2. Camera Work
   - Shot type (close-up, medium, wide, etc.)
   - Camera movement (static, pan, zoom, tracking, etc.)
   - Angle (eye-level, high angle, low angle, etc.)

3. Lighting & Mood
   - Lighting type and direction
   - Color temperature
   - Mood/atmosphere

Format each scene clearly with these sections.

DETAILED SCENE DESCRIPTIONS:"""
        )

        scene_details_chain = LLMChain(
            llm=self.llm,
            prompt=scene_details_prompt,
            output_key="scene_details"
        )

        # Step 5: Voiceover/Text Overlay
        voiceover_prompt = PromptTemplate(
            input_variables=["scene_details", "narrative_arc"],
            template="""Write voiceover and text overlays:

Scene Details:
{scene_details}

Narrative Arc:
{narrative_arc}

For each scene, provide:
1. Voiceover Script (if applicable)
   - Natural, conversational tone
   - Matches visual pacing
   - Clear and concise

2. On-Screen Text (if applicable)
   - Key messages or statistics
   - Captions for emphasis
   - Title cards

3. Timing Notes
   - When text appears/disappears
   - Emphasis points

Keep voiceover concise - aim for 2-3 seconds of speech per second of video.

VOICEOVER & TEXT:"""
        )

        voiceover_chain = LLMChain(
            llm=self.llm,
            prompt=voiceover_prompt,
            output_key="voiceover_text"
        )

        # Step 6: Music and Sound Design
        sound_prompt = PromptTemplate(
            input_variables=["narrative_arc", "scene_details", "video_type"],
            template="""Recommend music and sound design:

Narrative Arc:
{narrative_arc}

Scene Details:
{scene_details}

Video Type: {video_type}

Recommend:
1. Background Music
   - Genre/style
   - Tempo/energy level
   - Mood
   - When it starts/stops/changes

2. Sound Effects
   - Key sound effects needed
   - Timing for each

3. Audio Levels
   - Music volume (relative to voiceover)
   - Fade in/out timing

MUSIC & SOUND DESIGN:"""
        )

        sound_chain = LLMChain(
            llm=self.llm,
            prompt=sound_prompt,
            output_key="sound_design"
        )

        # Step 7: Transitions
        transitions_prompt = PromptTemplate(
            input_variables=["scene_breakdown", "video_type"],
            template="""Define transitions between scenes:

Scene Breakdown:
{scene_breakdown}

Video Type: {video_type}

For each transition, specify:
1. Transition Type
   - Cut (instant)
   - Fade (dissolve)
   - Wipe
   - Zoom
   - Creative transition

2. Duration (typically 0.5-1 second)
3. Purpose (why this transition fits)

Match transition style to video type:
- Professional/corporate: Clean cuts, simple fades
- Creative/social: More dynamic transitions
- Educational: Logical flow transitions

TRANSITIONS:"""
        )

        transitions_chain = LLMChain(
            llm=self.llm,
            prompt=transitions_prompt,
            output_key="transitions"
        )

        # Step 8: Scene Prompts for Generation
        prompts_prompt = PromptTemplate(
            input_variables=["scene_details", "style"],
            template="""Generate video generation prompts for each scene:

Scene Details:
{scene_details}

Visual Style: {style}

For each scene, create a detailed prompt suitable for Runway ML or Pika:

Include:
- Main action/subject
- Camera movement
- Lighting and environment
- Mood/atmosphere
- Technical quality specs (4K, smooth motion, etc.)

Format as numbered prompts (one per scene).

SCENE GENERATION PROMPTS:"""
        )

        prompts_chain = LLMChain(
            llm=self.llm,
            prompt=prompts_prompt,
            output_key="generation_prompts"
        )

        # Build sequential chain
        sequential_chain = SequentialChain(
            chains=[
                structure_chain,
                narrative_chain,
                scene_breakdown_chain,
                scene_details_chain,
                voiceover_chain,
                sound_chain,
                transitions_chain,
                prompts_chain
            ],
            input_variables=["content", "duration", "video_type", "style"],
            output_variables=[
                "video_structure",
                "narrative_arc",
                "scene_breakdown",
                "scene_details",
                "voiceover_text",
                "sound_design",
                "transitions",
                "generation_prompts"
            ],
            verbose=True
        )

        return sequential_chain

    def build_script(
        self,
        content: str,
        duration: int = 30,
        video_type: str = "social_media",
        style: str = "professional",
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build video script from content

        Args:
            content: Content or message to convey
            duration: Target duration in seconds
            video_type: Type of video (social_media, explainer, demo, ad, etc.)
            style: Visual style (professional, casual, dynamic, etc.)
            platform: Optional platform for optimization

        Returns:
            Dict with complete video script and components
        """
        # Apply platform-specific optimization
        if platform:
            platform_specs = self._get_platform_specs(platform)
            duration = min(duration, platform_specs['max_duration'])
            style = f"{style}, {platform_specs['style']}"

        logger.info(
            "building_video_script",
            duration=duration,
            video_type=video_type,
            platform=platform
        )

        try:
            # Run script building chain
            result = self.chain({
                "content": content,
                "duration": duration,
                "video_type": video_type,
                "style": style
            })

            # Add structured scene data
            result["structured_scenes"] = self._parse_scenes(
                result.get("scene_breakdown", ""),
                result.get("generation_prompts", "")
            )

            # Add metadata
            result["metadata"] = {
                "content": content,
                "duration": duration,
                "video_type": video_type,
                "style": style,
                "platform": platform,
                "scene_count": len(result["structured_scenes"])
            }

            logger.info(
                "video_script_built",
                scene_count=len(result["structured_scenes"])
            )

            return result

        except Exception as e:
            logger.error("script_building_error", error=str(e))
            return {
                "error": str(e),
                "structured_scenes": []
            }

    def _get_platform_specs(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific specifications"""
        specs = {
            "linkedin": {
                "max_duration": 90,
                "optimal_duration": 60,
                "aspect_ratio": "16:9",
                "style": "professional, informative"
            },
            "instagram_feed": {
                "max_duration": 60,
                "optimal_duration": 30,
                "aspect_ratio": "1:1 or 4:5",
                "style": "engaging, vibrant"
            },
            "instagram_story": {
                "max_duration": 15,
                "optimal_duration": 15,
                "aspect_ratio": "9:16",
                "style": "dynamic, attention-grabbing"
            },
            "instagram_reel": {
                "max_duration": 90,
                "optimal_duration": 30,
                "aspect_ratio": "9:16",
                "style": "fast-paced, trendy"
            },
            "youtube_short": {
                "max_duration": 60,
                "optimal_duration": 30,
                "aspect_ratio": "9:16",
                "style": "hook-driven, fast"
            },
            "youtube": {
                "max_duration": 300,
                "optimal_duration": 120,
                "aspect_ratio": "16:9",
                "style": "storytelling, educational"
            },
            "tiktok": {
                "max_duration": 60,
                "optimal_duration": 15,
                "aspect_ratio": "9:16",
                "style": "dynamic, fast-paced"
            },
            "facebook": {
                "max_duration": 120,
                "optimal_duration": 60,
                "aspect_ratio": "1:1 or 16:9",
                "style": "relatable, friendly"
            },
            "twitter": {
                "max_duration": 140,
                "optimal_duration": 45,
                "aspect_ratio": "16:9",
                "style": "concise, impactful"
            }
        }

        return specs.get(platform, {
            "max_duration": 60,
            "optimal_duration": 30,
            "aspect_ratio": "16:9",
            "style": "professional"
        })

    def _parse_scenes(self, scene_breakdown: str, generation_prompts: str) -> List[Dict[str, Any]]:
        """Parse scene breakdown into structured data"""
        scenes = []

        # Split scenes (simple parsing - could be enhanced)
        scene_lines = scene_breakdown.split('\n')
        prompt_lines = generation_prompts.split('\n')

        scene_num = 1
        for line in scene_lines:
            if line.strip().startswith('Scene'):
                # Extract duration if present
                duration_match = line.find('(')
                if duration_match != -1:
                    duration_end = line.find('seconds', duration_match)
                    if duration_end != -1:
                        try:
                            duration_str = line[duration_match+1:duration_end].strip()
                            duration = int(duration_str.split()[0])
                        except:
                            duration = 5  # Default
                    else:
                        duration = 5
                else:
                    duration = 5

                # Find corresponding prompt
                prompt = ""
                for pline in prompt_lines:
                    if pline.strip().startswith(f'Scene {scene_num}') or pline.strip().startswith(f'{scene_num}.'):
                        prompt = pline.split(':', 1)[-1].strip() if ':' in pline else pline
                        break

                scenes.append({
                    "scene_number": scene_num,
                    "duration": duration,
                    "description": line.strip(),
                    "prompt": prompt if prompt else "Scene content"
                })

                scene_num += 1

        return scenes

    def build_social_video_script(
        self,
        message: str,
        platform: str,
        duration: int = 30
    ) -> Dict[str, Any]:
        """
        Build script for social media video

        Args:
            message: Core message to convey
            platform: Social platform
            duration: Target duration

        Returns:
            Video script optimized for platform
        """
        return self.build_script(
            content=message,
            duration=duration,
            video_type="social_media",
            style="engaging",
            platform=platform
        )

    def build_explainer_script(
        self,
        topic: str,
        key_points: List[str],
        duration: int = 90
    ) -> Dict[str, Any]:
        """
        Build script for explainer video

        Args:
            topic: Topic to explain
            key_points: Key points to cover
            duration: Target duration

        Returns:
            Explainer video script
        """
        content = f"{topic}\n\nKey Points:\n" + "\n".join([f"- {point}" for point in key_points])

        return self.build_script(
            content=content,
            duration=duration,
            video_type="explainer",
            style="educational"
        )

    def build_product_demo_script(
        self,
        product_name: str,
        features: List[str],
        duration: int = 60
    ) -> Dict[str, Any]:
        """
        Build script for product demo video

        Args:
            product_name: Product name
            features: Features to demonstrate
            duration: Target duration

        Returns:
            Product demo script
        """
        content = f"{product_name}\n\nFeatures:\n" + "\n".join([f"- {feature}" for feature in features])

        return self.build_script(
            content=content,
            duration=duration,
            video_type="product_demo",
            style="professional"
        )


def create_video_script_builder(llm) -> VideoScriptBuilderChain:
    """
    Factory function to create Video Script Builder Chain

    Args:
        llm: Language model instance

    Returns:
        VideoScriptBuilderChain instance
    """
    return VideoScriptBuilderChain(llm)


# Example usage
if __name__ == "__main__":
    from langchain_community.llms import Ollama

    # Initialize LLM
    llm = Ollama(model="llama3", base_url="http://localhost:11434")

    # Create script builder
    builder = create_video_script_builder(llm)

    # Build script for LinkedIn video
    result = builder.build_social_video_script(
        message="Introducing our new AI-powered marketing automation platform that helps B2B teams generate content 10x faster while maintaining quality and brand consistency.",
        platform="linkedin",
        duration=45
    )

    print("\n=== VIDEO SCRIPT BUILDING RESULTS ===\n")
    print(f"Video Structure:\n{result['video_structure']}\n")
    print(f"Narrative Arc:\n{result['narrative_arc']}\n")
    print(f"Scene Breakdown:\n{result['scene_breakdown']}\n")
    print(f"\nStructured Scenes: {len(result['structured_scenes'])} scenes")
    print(f"\nGeneration Prompts:\n{result['generation_prompts']}\n")
