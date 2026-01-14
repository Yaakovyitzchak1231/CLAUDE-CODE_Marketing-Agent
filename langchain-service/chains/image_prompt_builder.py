"""
Image Prompt Builder Chain
Sequential chain for converting content to optimized image generation prompts
"""

from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate
from typing import Dict, Any, Optional, List
import structlog

logger = structlog.get_logger()


class ImagePromptBuilderChain:
    """
    Sequential chain for building optimized image generation prompts

    Process:
    1. Analyze content and extract visual concepts
    2. Define composition and framing
    3. Specify style and aesthetic
    4. Add lighting and mood
    5. Include technical parameters
    6. Apply platform optimization
    7. Generate final prompts for DALL-E 3 and Midjourney
    """

    def __init__(self, llm):
        """
        Initialize Image Prompt Builder Chain

        Args:
            llm: Language model instance
        """
        self.llm = llm
        self.chain = self._build_chain()

        logger.info("image_prompt_builder_initialized")

    def _build_chain(self) -> SequentialChain:
        """Build sequential image prompt building chain"""

        # Step 1: Visual Concept Extraction
        concept_extraction_prompt = PromptTemplate(
            input_variables=["content_description", "image_purpose"],
            template="""Extract visual concepts from this content:

Content Description:
{content_description}

Image Purpose: {image_purpose}

Extract:
1. Main subject (what should be the focal point)
2. Supporting elements (what else should appear)
3. Environment/setting (where does this take place)
4. Action/emotion (what's happening or feeling conveyed)
5. Symbolic elements (icons, metaphors, abstract concepts)

VISUAL CONCEPTS:"""
        )

        concept_chain = LLMChain(
            llm=self.llm,
            prompt=concept_extraction_prompt,
            output_key="visual_concepts"
        )

        # Step 2: Composition and Framing
        composition_prompt = PromptTemplate(
            input_variables=["visual_concepts", "aspect_ratio"],
            template="""Define composition and framing:

Visual Concepts:
{visual_concepts}

Aspect Ratio: {aspect_ratio}

Define:
1. Framing (close-up, medium shot, wide shot, extreme wide)
2. Perspective (eye-level, bird's-eye, worm's-eye, isometric)
3. Rule of thirds application
4. Foreground/midground/background elements
5. Negative space usage
6. Symmetry vs asymmetry

COMPOSITION:"""
        )

        composition_chain = LLMChain(
            llm=self.llm,
            prompt=composition_prompt,
            output_key="composition"
        )

        # Step 3: Style and Aesthetic
        style_prompt = PromptTemplate(
            input_variables=["visual_concepts", "composition", "style_preference"],
            template="""Define visual style and aesthetic:

Visual Concepts:
{visual_concepts}

Composition:
{composition}

Style Preference: {style_preference}

Define:
1. Visual style (photorealistic, illustration, digital art, 3D render, etc.)
2. Art movement influence (if any: minimalist, modern, vintage, etc.)
3. Texture and detail level
4. Color scheme approach
5. Design trends to incorporate
6. Brand alignment considerations

STYLE & AESTHETIC:"""
        )

        style_chain = LLMChain(
            llm=self.llm,
            prompt=style_prompt,
            output_key="style_aesthetic"
        )

        # Step 4: Lighting and Mood
        lighting_prompt = PromptTemplate(
            input_variables=["visual_concepts", "style_aesthetic"],
            template="""Define lighting and mood:

Visual Concepts:
{visual_concepts}

Style & Aesthetic:
{style_aesthetic}

Define:
1. Lighting type (natural, studio, dramatic, soft, harsh, golden hour, etc.)
2. Light direction and intensity
3. Shadows and highlights
4. Mood/atmosphere (professional, warm, energetic, calm, mysterious, etc.)
5. Time of day (if relevant)
6. Weather/environmental conditions (if relevant)

LIGHTING & MOOD:"""
        )

        lighting_chain = LLMChain(
            llm=self.llm,
            prompt=lighting_prompt,
            output_key="lighting_mood"
        )

        # Step 5: Color Palette
        color_prompt = PromptTemplate(
            input_variables=["style_aesthetic", "lighting_mood", "brand_colors"],
            template="""Define color palette:

Style & Aesthetic:
{style_aesthetic}

Lighting & Mood:
{lighting_mood}

Brand Colors: {brand_colors}

Define:
1. Primary colors (2-3 dominant colors)
2. Secondary colors (supporting palette)
3. Color temperature (warm, cool, neutral)
4. Color contrast strategy
5. Brand color integration
6. Color psychology alignment with message

COLOR PALETTE:"""
        )

        color_chain = LLMChain(
            llm=self.llm,
            prompt=color_prompt,
            output_key="color_palette"
        )

        # Step 6: Technical Parameters
        technical_prompt = PromptTemplate(
            input_variables=["composition", "style_aesthetic"],
            template="""Define technical parameters:

Composition:
{composition}

Style & Aesthetic:
{style_aesthetic}

Specify:
1. Resolution/quality indicators (4K, high-resolution, sharp, crisp, etc.)
2. Camera-related terms (if photorealistic: lens type, depth of field, etc.)
3. Rendering quality (if digital art: professional, polished, detailed, etc.)
4. Detail level (intricate details, clean, minimalist, etc.)
5. Production quality indicators

TECHNICAL PARAMETERS:"""
        )

        technical_chain = LLMChain(
            llm=self.llm,
            prompt=technical_prompt,
            output_key="technical_params"
        )

        # Step 7: DALL-E 3 Prompt Generation
        dalle_prompt = PromptTemplate(
            input_variables=[
                "visual_concepts",
                "composition",
                "style_aesthetic",
                "lighting_mood",
                "color_palette",
                "technical_params"
            ],
            template="""Generate DALL-E 3 optimized prompt:

Visual Concepts:
{visual_concepts}

Composition:
{composition}

Style & Aesthetic:
{style_aesthetic}

Lighting & Mood:
{lighting_mood}

Color Palette:
{color_palette}

Technical Parameters:
{technical_params}

Create a single, detailed DALL-E 3 prompt (max 4000 characters) that:
- Starts with the main subject
- Is descriptive and specific
- Uses natural language
- Includes all visual elements
- Avoids negativity (what NOT to include)
- Flows naturally as a single description

DALL-E 3 PROMPT:"""
        )

        dalle_chain = LLMChain(
            llm=self.llm,
            prompt=dalle_prompt,
            output_key="dalle_prompt"
        )

        # Step 8: Midjourney Prompt Generation
        midjourney_prompt = PromptTemplate(
            input_variables=[
                "visual_concepts",
                "composition",
                "style_aesthetic",
                "lighting_mood",
                "color_palette",
                "technical_params"
            ],
            template="""Generate Midjourney optimized prompt:

Visual Concepts:
{visual_concepts}

Composition:
{composition}

Style & Aesthetic:
{style_aesthetic}

Lighting & Mood:
{lighting_mood}

Color Palette:
{color_palette}

Technical Parameters:
{technical_params}

Create a Midjourney prompt that:
- Uses comma-separated descriptive phrases
- Includes specific artistic styles and techniques
- Leverages Midjourney's strengths (artistic, stylized)
- Uses power words and modifiers
- Can include artist references if relevant
- Keep concise but descriptive

Do NOT include Midjourney parameters (--ar, --v, --q) - just the core prompt.

MIDJOURNEY PROMPT:"""
        )

        midjourney_chain = LLMChain(
            llm=self.llm,
            prompt=midjourney_prompt,
            output_key="midjourney_prompt"
        )

        # Build sequential chain
        sequential_chain = SequentialChain(
            chains=[
                concept_chain,
                composition_chain,
                style_chain,
                lighting_chain,
                color_chain,
                technical_chain,
                dalle_chain,
                midjourney_chain
            ],
            input_variables=[
                "content_description",
                "image_purpose",
                "aspect_ratio",
                "style_preference",
                "brand_colors"
            ],
            output_variables=[
                "visual_concepts",
                "composition",
                "style_aesthetic",
                "lighting_mood",
                "color_palette",
                "technical_params",
                "dalle_prompt",
                "midjourney_prompt"
            ],
            verbose=True
        )

        return sequential_chain

    def build_prompt(
        self,
        content_description: str,
        image_purpose: str = "social media post",
        aspect_ratio: str = "1:1",
        style_preference: str = "professional",
        brand_colors: Optional[List[str]] = None,
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build optimized image prompts

        Args:
            content_description: Description of content or message
            image_purpose: Purpose of image (social media, blog header, ad, etc.)
            aspect_ratio: Desired aspect ratio (1:1, 16:9, 9:16, etc.)
            style_preference: Visual style preference
            brand_colors: List of brand colors
            platform: Optional platform for optimization (linkedin, instagram, etc.)

        Returns:
            Dict with prompts and visual breakdown
        """
        # Prepare brand colors string
        if brand_colors:
            brand_colors_str = ", ".join(brand_colors)
        else:
            brand_colors_str = "flexible, choose appropriate colors"

        # Apply platform-specific optimization
        if platform:
            platform_specs = self._get_platform_specs(platform)
            image_purpose = f"{image_purpose} for {platform}"
            style_preference = f"{style_preference}, {platform_specs['style']}"
            aspect_ratio = platform_specs['aspect_ratio']

        logger.info(
            "building_image_prompt",
            purpose=image_purpose,
            aspect_ratio=aspect_ratio,
            style=style_preference
        )

        try:
            # Run prompt building chain
            result = self.chain({
                "content_description": content_description,
                "image_purpose": image_purpose,
                "aspect_ratio": aspect_ratio,
                "style_preference": style_preference,
                "brand_colors": brand_colors_str
            })

            # Add metadata
            result["metadata"] = {
                "content_description": content_description,
                "image_purpose": image_purpose,
                "aspect_ratio": aspect_ratio,
                "style_preference": style_preference,
                "brand_colors": brand_colors,
                "platform": platform
            }

            logger.info("image_prompt_built_successfully")

            return result

        except Exception as e:
            logger.error("prompt_building_error", error=str(e))
            return {
                "error": str(e),
                "dalle_prompt": content_description,  # Fallback to basic description
                "midjourney_prompt": content_description
            }

    def _get_platform_specs(self, platform: str) -> Dict[str, str]:
        """Get platform-specific specifications"""
        specs = {
            "linkedin": {
                "aspect_ratio": "16:9",
                "style": "professional, corporate, clean"
            },
            "instagram": {
                "aspect_ratio": "1:1",
                "style": "vibrant, engaging, trendy"
            },
            "instagram_story": {
                "aspect_ratio": "9:16",
                "style": "dynamic, attention-grabbing, mobile-first"
            },
            "facebook": {
                "aspect_ratio": "1.91:1",
                "style": "friendly, approachable, relatable"
            },
            "twitter": {
                "aspect_ratio": "16:9",
                "style": "concise, impactful, current"
            },
            "blog_header": {
                "aspect_ratio": "16:9",
                "style": "thematic, professional, informative"
            },
            "pinterest": {
                "aspect_ratio": "2:3",
                "style": "aspirational, beautiful, vertical"
            },
            "youtube_thumbnail": {
                "aspect_ratio": "16:9",
                "style": "bold, eye-catching, expressive"
            }
        }

        return specs.get(platform, {
            "aspect_ratio": "1:1",
            "style": "professional"
        })

    def build_batch_prompts(
        self,
        content_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build prompts for multiple content items

        Args:
            content_items: List of dicts with content_description and parameters

        Returns:
            List of prompt results
        """
        results = []

        for i, item in enumerate(content_items, 1):
            logger.info(f"building_batch_prompt", index=i, total=len(content_items))

            result = self.build_prompt(
                content_description=item.get("content_description", ""),
                image_purpose=item.get("image_purpose", "social media post"),
                aspect_ratio=item.get("aspect_ratio", "1:1"),
                style_preference=item.get("style_preference", "professional"),
                brand_colors=item.get("brand_colors"),
                platform=item.get("platform")
            )

            results.append(result)

        logger.info("batch_prompts_built", count=len(results))
        return results

    def optimize_for_provider(
        self,
        base_prompt: str,
        provider: str = "dalle"
    ) -> str:
        """
        Optimize prompt for specific provider

        Args:
            base_prompt: Base prompt to optimize
            provider: Provider (dalle, midjourney)

        Returns:
            Optimized prompt
        """
        if provider == "dalle":
            # DALL-E 3 prefers natural language descriptions
            return base_prompt

        elif provider == "midjourney":
            # Midjourney prefers comma-separated descriptive phrases
            # Convert natural language to comma-separated format
            optimization_prompt = f"""Convert this natural language prompt to Midjourney format:

Original Prompt:
{base_prompt}

Convert to comma-separated descriptive phrases optimized for Midjourney.
Focus on visual elements, artistic style, and technical quality.

MIDJOURNEY OPTIMIZED:"""

            try:
                optimized = self.llm.invoke(optimization_prompt)
                return optimized.strip()
            except Exception:
                return base_prompt

        return base_prompt


def create_image_prompt_builder(llm) -> ImagePromptBuilderChain:
    """
    Factory function to create Image Prompt Builder Chain

    Args:
        llm: Language model instance

    Returns:
        ImagePromptBuilderChain instance
    """
    return ImagePromptBuilderChain(llm)


# Example usage
if __name__ == "__main__":
    from langchain_community.llms import Ollama

    # Initialize LLM
    llm = Ollama(model="llama3", base_url="http://localhost:11434")

    # Create prompt builder
    builder = create_image_prompt_builder(llm)

    # Build prompt for LinkedIn post
    result = builder.build_prompt(
        content_description="B2B marketing automation platform that helps teams save time and increase efficiency through AI-powered content generation",
        image_purpose="LinkedIn post header",
        platform="linkedin",
        style_preference="modern and professional",
        brand_colors=["#1E3A8A", "#3B82F6", "#FFFFFF"]
    )

    print("\n=== IMAGE PROMPT BUILDING RESULTS ===\n")
    print(f"Visual Concepts:\n{result['visual_concepts']}\n")
    print(f"Composition:\n{result['composition']}\n")
    print(f"Color Palette:\n{result['color_palette']}\n")
    print(f"\n--- DALL-E 3 PROMPT ---\n{result['dalle_prompt']}\n")
    print(f"\n--- MIDJOURNEY PROMPT ---\n{result['midjourney_prompt']}\n")
