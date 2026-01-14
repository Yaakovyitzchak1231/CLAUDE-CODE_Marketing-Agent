"""
Image Generation Agent
Creates marketing images using DALL-E 3 and Midjourney
"""

from typing import Dict, List, Optional, Any
from langchain.tools import Tool
from .base_agent import BaseAgent
from tools.dalle_tool import DallETool, create_dalle_langchain_tool
from tools.midjourney_tool import MidjourneyTool, create_midjourney_langchain_tool
import structlog
from datetime import datetime
import json


logger = structlog.get_logger()


class ImageGenerationAgent(BaseAgent):
    """
    Specialist agent for image generation

    Capabilities:
    - Social media images (LinkedIn, Facebook, Instagram)
    - Blog header images
    - Infographics and diagrams
    - Product visuals
    - Brand imagery
    - Advertisement creatives
    - Thumbnail generation
    """

    def __init__(self):
        """Initialize Image Generation Agent"""

        # Initialize image generation tools
        dalle_tool = create_dalle_langchain_tool()
        midjourney_tool = create_midjourney_langchain_tool()

        # Create prompt builder tool
        def build_image_prompt(content_description: str, requirements: str = "") -> str:
            """Build optimized image prompt from content description"""

            prompt_template = f"""Convert this content description into a detailed image generation prompt:

Content: {content_description}
Requirements: {requirements}

Create a prompt that includes:
1. Main subject/scene
2. Visual style (photorealistic, illustration, digital art, etc.)
3. Composition and framing
4. Lighting (natural, studio, dramatic, etc.)
5. Color palette
6. Mood/atmosphere
7. Technical details (4K, high-resolution, professional, etc.)

Format as a single, detailed prompt suitable for DALL-E 3 or Midjourney."""

            return prompt_template  # In real implementation, this would call LLM

        prompt_builder_tool = Tool(
            name="Image_Prompt_Builder",
            func=build_image_prompt,
            description="Convert content description into optimized image generation prompt. "
                        "Input should be content description and image requirements."
        )

        # Create prompt optimizer tool
        def optimize_for_platform(prompt: str, platform: str, style: str = "professional") -> str:
            """Optimize prompt for specific platform and style"""

            platform_specs = {
                "linkedin": {
                    "dimensions": "1200x628",
                    "style": "professional, corporate, modern",
                    "mood": "trustworthy, authoritative, inspiring"
                },
                "instagram": {
                    "dimensions": "1080x1080",
                    "style": "vibrant, eye-catching, trendy",
                    "mood": "engaging, emotional, authentic"
                },
                "facebook": {
                    "dimensions": "1200x630",
                    "style": "friendly, approachable, clear",
                    "mood": "welcoming, relatable, positive"
                },
                "twitter": {
                    "dimensions": "1200x675",
                    "style": "concise, impactful, contemporary",
                    "mood": "dynamic, relevant, timely"
                },
                "blog_header": {
                    "dimensions": "1920x1080",
                    "style": "professional, clean, thematic",
                    "mood": "informative, engaging, contextual"
                },
                "email_header": {
                    "dimensions": "600x200",
                    "style": "clear, branded, attention-grabbing",
                    "mood": "inviting, relevant, professional"
                }
            }

            spec = platform_specs.get(platform, platform_specs["linkedin"])

            optimized = f"""{prompt}, {spec['style']}, {spec['mood']}, optimized for {platform}, {spec['dimensions']} dimensions, high quality, professional marketing visual"""

            return optimized

        optimizer_tool = Tool(
            name="Platform_Optimizer",
            func=optimize_for_platform,
            description="Optimize image prompt for specific platform (LinkedIn, Instagram, Facebook, blog, email). "
                        "Input should be base prompt and platform name."
        )

        # Create brand application tool
        def apply_brand_guidelines(prompt: str, brand_colors: Optional[List[str]] = None) -> str:
            """Apply brand guidelines to image prompt"""

            brand_elements = []

            if brand_colors:
                colors_str = ", ".join(brand_colors)
                brand_elements.append(f"brand colors: {colors_str}")

            brand_elements.extend([
                "on-brand visual style",
                "consistent with brand identity",
                "professional brand representation"
            ])

            branded_prompt = f"{prompt}, {', '.join(brand_elements)}"

            return branded_prompt

        brand_tool = Tool(
            name="Brand_Applicator",
            func=apply_brand_guidelines,
            description="Apply brand guidelines (colors, style) to image prompt. "
                        "Input should be base prompt and optional brand colors."
        )

        tools = [
            dalle_tool,
            midjourney_tool,
            prompt_builder_tool,
            optimizer_tool,
            brand_tool
        ]

        super().__init__(
            name="Image Generation Agent",
            description="Creates high-quality marketing images using AI image generation (DALL-E 3, Midjourney)",
            tools=tools,
            verbose=True
        )

        # Direct tool access for internal use
        self.dalle = DallETool()
        self.midjourney = MidjourneyTool()

        logger.info("image_agent_initialized")

    def get_specialized_prompt(self) -> str:
        """Get Image Generation Agent system prompt"""
        return """You are an Image Generation Agent specializing in marketing visuals.

Your primary responsibilities:
1. Generate high-quality marketing images
2. Optimize prompts for different platforms
3. Apply brand guidelines consistently
4. Select appropriate image generation service
5. Ensure images meet technical requirements

Image Generation Best Practices:
- Be specific and detailed in prompts
- Include visual style, lighting, composition
- Specify mood and atmosphere
- Add technical quality indicators
- Consider platform requirements
- Apply brand colors and style
- Avoid trademarked content
- Focus on clear subject matter

DALL-E 3 Use Cases:
- Photorealistic images
- Professional marketing visuals
- Corporate imagery
- Product-focused images
- Consistent, reliable results
- Faster generation (30-60 seconds)

Midjourney Use Cases:
- Artistic, stylized images
- Creative concepts
- Illustrations and digital art
- Unique, eye-catching visuals
- Multiple variations
- Slower generation (2-5 minutes)

Platform Optimization:
- LinkedIn: Professional, corporate, 1200x628
- Instagram: Square or vertical, vibrant, 1080x1080
- Facebook: Friendly, approachable, 1200x630
- Blog Headers: Wide, thematic, 1920x1080
- Email Headers: Narrow, attention-grabbing, 600x200

Quality Standards:
- Always specify high-resolution
- Include professional quality indicators
- Ensure proper composition
- Verify brand alignment
- Test multiple variations if needed

Output Format:
Provide:
- Generated image URL(s)
- Prompt used (original and revised)
- Dimensions and format
- Generation cost
- Platform suitability
- Suggested usage
- Alternative variations (if applicable)

Be creative, brand-conscious, and platform-aware."""

    def generate_social_media_image(
        self,
        content: str,
        platform: str,
        brand_colors: Optional[List[str]] = None,
        style: str = "professional",
        provider: str = "dalle"
    ) -> Dict[str, Any]:
        """
        Generate social media image

        Args:
            content: Content description or topic
            platform: Social platform (linkedin, instagram, facebook, twitter)
            brand_colors: List of brand color hex codes
            style: Visual style preference
            provider: Image generator (dalle, midjourney)

        Returns:
            Dict with generated image details
        """
        prompt = f"""Create a {style} social media image for {platform}.

Content: {content}

Requirements:
- Platform: {platform}
- Style: {style}
- Professional marketing quality
- Eye-catching and engaging
- Clear focal point
- Optimized composition

Generate appropriate visual."""

        if brand_colors:
            prompt += f"\nBrand colors: {', '.join(brand_colors)}"

        result = self.run(prompt)

        # Store metadata
        if result.get("output"):
            metadata = {
                "type": "social_media_image",
                "platform": platform,
                "content": content,
                "brand_colors": brand_colors,
                "style": style,
                "provider": provider,
                "created_at": datetime.utcnow().isoformat()
            }

            logger.info(
                "social_image_generated",
                platform=platform,
                provider=provider
            )

            result["metadata"] = metadata

        return result

    def generate_blog_header(
        self,
        blog_title: str,
        blog_topic: str,
        style: str = "modern",
        provider: str = "dalle"
    ) -> Dict[str, Any]:
        """
        Generate blog header image

        Args:
            blog_title: Blog post title
            blog_topic: Blog post topic/theme
            style: Visual style
            provider: Image generator

        Returns:
            Dict with generated image details
        """
        prompt = f"""Create a blog header image.

Blog Title: {blog_title}
Topic: {blog_topic}
Style: {style}

Requirements:
- Wide format (1920x1080)
- Professional and clean
- Thematically relevant to topic
- High-resolution
- Modern design
- Readable with text overlay
- Engaging and informative

Generate appropriate header image."""

        result = self.run(prompt)

        if result.get("output"):
            metadata = {
                "type": "blog_header",
                "title": blog_title,
                "topic": blog_topic,
                "style": style,
                "provider": provider,
                "dimensions": "1920x1080",
                "created_at": datetime.utcnow().isoformat()
            }

            result["metadata"] = metadata

        return result

    def generate_infographic_elements(
        self,
        infographic_topic: str,
        sections: List[str],
        style: str = "modern",
        provider: str = "dalle"
    ) -> Dict[str, Any]:
        """
        Generate infographic visual elements

        Args:
            infographic_topic: Infographic topic
            sections: List of section descriptions
            style: Visual style
            provider: Image generator

        Returns:
            Dict with generated elements
        """
        sections_str = "\n".join([f"- {section}" for section in sections])

        prompt = f"""Create infographic visual elements for: {infographic_topic}

Sections:
{sections_str}

Style: {style}

Requirements:
- Clean, professional design
- Data visualization friendly
- Clear hierarchy
- Consistent visual style
- Modern iconography
- Suitable for vertical layout
- Professional color scheme

Generate appropriate infographic elements."""

        result = self.run(prompt)

        if result.get("output"):
            metadata = {
                "type": "infographic",
                "topic": infographic_topic,
                "sections": sections,
                "style": style,
                "provider": provider,
                "created_at": datetime.utcnow().isoformat()
            }

            result["metadata"] = metadata

        return result

    def generate_product_visual(
        self,
        product_description: str,
        use_case: str,
        style: str = "photorealistic",
        provider: str = "dalle"
    ) -> Dict[str, Any]:
        """
        Generate product marketing visual

        Args:
            product_description: Product description
            use_case: Product use case or scenario
            style: Visual style
            provider: Image generator

        Returns:
            Dict with generated image
        """
        prompt = f"""Create a product marketing visual.

Product: {product_description}
Use Case: {use_case}
Style: {style}

Requirements:
- Professional product photography style
- Clear product visibility
- Contextual environment
- Appropriate lighting
- High-resolution
- Marketing quality
- Compelling composition

Generate product visual."""

        result = self.run(prompt)

        if result.get("output"):
            metadata = {
                "type": "product_visual",
                "product": product_description,
                "use_case": use_case,
                "style": style,
                "provider": provider,
                "created_at": datetime.utcnow().isoformat()
            }

            result["metadata"] = metadata

        return result

    def generate_ad_creative(
        self,
        campaign_message: str,
        target_audience: str,
        platform: str,
        style: str = "compelling",
        provider: str = "dalle"
    ) -> Dict[str, Any]:
        """
        Generate advertisement creative

        Args:
            campaign_message: Ad campaign message
            target_audience: Target audience description
            platform: Advertising platform
            style: Visual style
            provider: Image generator

        Returns:
            Dict with generated ad creative
        """
        prompt = f"""Create an advertisement creative.

Campaign Message: {campaign_message}
Target Audience: {target_audience}
Platform: {platform}
Style: {style}

Requirements:
- Attention-grabbing
- Clear value proposition
- Emotionally resonant
- Platform-optimized
- Professional quality
- Brand-appropriate
- Conversion-focused

Generate ad creative."""

        result = self.run(prompt)

        if result.get("output"):
            metadata = {
                "type": "ad_creative",
                "message": campaign_message,
                "audience": target_audience,
                "platform": platform,
                "style": style,
                "provider": provider,
                "created_at": datetime.utcnow().isoformat()
            }

            result["metadata"] = metadata

        return result

    def generate_batch(
        self,
        prompts: List[Dict[str, Any]],
        provider: str = "dalle"
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple images in batch

        Args:
            prompts: List of prompt dicts with keys: prompt, size, style
            provider: Image generator to use

        Returns:
            List of generation results
        """
        results = []

        for i, prompt_config in enumerate(prompts, 1):
            logger.info(f"generating_batch_image", index=i, total=len(prompts))

            prompt = prompt_config.get("prompt")
            size = prompt_config.get("size", "1024x1024")
            style = prompt_config.get("style", "vivid")

            if provider == "dalle":
                result = self.dalle.generate(
                    prompt=prompt,
                    size=size,
                    style=style
                )
            else:  # midjourney
                result = self.midjourney.generate(
                    prompt=prompt,
                    aspect_ratio=self._convert_size_to_aspect(size)
                )

            results.append(result)

        logger.info("batch_generation_complete", count=len(results))
        return results

    def _convert_size_to_aspect(self, size: str) -> str:
        """Convert DALL-E size to Midjourney aspect ratio"""
        aspect_map = {
            "1024x1024": "1:1",
            "1792x1024": "16:9",
            "1024x1792": "9:16"
        }
        return aspect_map.get(size, "1:1")


def create_image_agent() -> ImageGenerationAgent:
    """Factory function to create Image Generation Agent"""
    return ImageGenerationAgent()
