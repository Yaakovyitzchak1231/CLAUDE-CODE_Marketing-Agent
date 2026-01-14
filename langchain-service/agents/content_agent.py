"""
Content Creation Agent
Generates high-quality marketing content across multiple formats and channels
"""

from typing import List, Dict, Any, Optional
from langchain.tools import Tool
from .base_agent import BaseAgent
from memory.vector_store import get_vector_store
from memory.conversation_memory import get_memory_manager
import structlog
from datetime import datetime
import re


logger = structlog.get_logger()


class ContentAgent(BaseAgent):
    """
    Specialist agent for content creation

    Capabilities:
    - Blog post creation
    - LinkedIn content (posts, articles)
    - Email campaigns (newsletters, sequences)
    - Social media content
    - Website copy
    - Case studies and whitepapers
    - SEO optimization
    - Brand voice consistency
    """

    def __init__(self):
        """Initialize Content Agent"""

        # Initialize vector store for RAG
        vector_store = get_vector_store()

        # Create content research tool
        def research_similar_content(topic: str) -> str:
            """Find similar successful content for inspiration"""
            results = vector_store.search_similar_content(
                query=topic,
                n_results=5
            )

            if not results:
                return "No similar content found in library."

            formatted = []
            for i, result in enumerate(results, 1):
                metadata = result.get('metadata', {})
                formatted.append(
                    f"{i}. {result['document'][:300]}...\n"
                    f"   Type: {metadata.get('type', 'Unknown')}\n"
                    f"   Performance: {metadata.get('engagement_score', 'N/A')}\n"
                    f"   Relevance: {1 - result['distance']:.2f}\n"
                )

            return "\n\n".join(formatted)

        content_research_tool = Tool(
            name="Content_Research",
            func=research_similar_content,
            description="Search historical content library for successful content on similar topics. "
                        "Useful for finding inspiration, proven formats, and effective messaging. "
                        "Input should be content topic or theme."
        )

        # Create SEO analysis tool
        def analyze_seo(content: str) -> str:
            """Analyze content for SEO optimization"""

            # Word count
            word_count = len(content.split())

            # Heading count
            h1_count = len(re.findall(r'^#\s', content, re.MULTILINE))
            h2_count = len(re.findall(r'^##\s', content, re.MULTILINE))
            h3_count = len(re.findall(r'^###\s', content, re.MULTILINE))

            # Link count
            internal_links = len(re.findall(r'\[.*?\]\((?!http)', content))
            external_links = len(re.findall(r'\[.*?\]\(http', content))

            # Reading time (avg 200 words/min)
            reading_time = round(word_count / 200, 1)

            analysis = f"""SEO Analysis:

Content Metrics:
- Word Count: {word_count} words
- Reading Time: {reading_time} minutes
- H1 Count: {h1_count}
- H2 Count: {h2_count}
- H3 Count: {h3_count}
- Internal Links: {internal_links}
- External Links: {external_links}

Recommendations:
"""

            recommendations = []

            if word_count < 300:
                recommendations.append("⚠️ Content is too short. Aim for 800-2000 words for blog posts.")
            elif word_count < 800:
                recommendations.append("⚠️ Consider expanding content to 800-2000 words for better SEO.")
            else:
                recommendations.append("✓ Word count is good for SEO.")

            if h1_count == 0:
                recommendations.append("⚠️ Missing H1 heading (title).")
            elif h1_count > 1:
                recommendations.append("⚠️ Multiple H1 headings. Use only one H1 per page.")
            else:
                recommendations.append("✓ H1 heading structure is correct.")

            if h2_count == 0:
                recommendations.append("⚠️ Add H2 subheadings to improve scannability.")
            else:
                recommendations.append("✓ H2 subheadings present.")

            if internal_links == 0:
                recommendations.append("⚠️ Add internal links to other relevant content.")
            else:
                recommendations.append(f"✓ {internal_links} internal links found.")

            if external_links == 0:
                recommendations.append("⚠️ Consider adding external links to authoritative sources.")
            else:
                recommendations.append(f"✓ {external_links} external links found.")

            analysis += "\n".join(recommendations)
            return analysis

        seo_tool = Tool(
            name="SEO_Analyzer",
            func=analyze_seo,
            description="Analyze content for SEO best practices including word count, headings, and links. "
                        "Input should be the content to analyze."
        )

        # Create brand voice checker
        def check_brand_voice(content: str, brand_guidelines: Optional[str] = None) -> str:
            """Check content against brand voice guidelines"""

            guidelines = brand_guidelines or """Professional yet approachable, authoritative but not arrogant,
data-driven with storytelling, helpful and educational."""

            prompt = f"""Evaluate this content against brand voice guidelines:

Brand Voice: {guidelines}

Content:
{content[:500]}...

Evaluate:
1. Tone consistency (1-10)
2. Professionalism level (1-10)
3. Clarity and readability (1-10)
4. Brand alignment (1-10)
5. Specific suggestions for improvement

Provide scores and actionable feedback."""

            return prompt  # In real implementation, this would call LLM

        brand_voice_tool = Tool(
            name="Brand_Voice_Checker",
            func=check_brand_voice,
            description="Check content for brand voice consistency and alignment. "
                        "Input should be the content to check."
        )

        # Create grammar and style checker
        def check_grammar(content: str) -> str:
            """Basic grammar and style check"""

            issues = []

            # Check for common issues
            if re.search(r'\s\s+', content):
                issues.append("Multiple consecutive spaces found")

            if re.search(r'[.!?]\s*[a-z]', content):
                issues.append("Lowercase letter after sentence ending")

            if len(re.findall(r'!', content)) > 3:
                issues.append("Excessive exclamation marks (avoid overuse)")

            if re.search(r'\bvery\b', content, re.IGNORECASE):
                issues.append("Consider replacing 'very' with stronger adjectives")

            if re.search(r'\breally\b', content, re.IGNORECASE):
                issues.append("Consider replacing 'really' with more specific language")

            # Check paragraph length
            paragraphs = content.split('\n\n')
            long_paragraphs = [i for i, p in enumerate(paragraphs) if len(p.split()) > 150]
            if long_paragraphs:
                issues.append(f"Paragraphs {long_paragraphs} are too long (>150 words)")

            if not issues:
                return "✓ No obvious grammar or style issues detected."

            return "Issues found:\n- " + "\n- ".join(issues)

        grammar_tool = Tool(
            name="Grammar_Checker",
            func=check_grammar,
            description="Check content for basic grammar and style issues. "
                        "Input should be the content to check."
        )

        # Create content optimizer
        def optimize_content(content: str, optimization_type: str = "engagement") -> str:
            """Optimize content for specific goals"""

            prompt = f"""Optimize this content for {optimization_type}:

{content}

Provide optimized version with:
1. Stronger headlines/hooks
2. More engaging language
3. Better flow and structure
4. Clear CTAs
5. Improved readability

Maintain original message and key points."""

            return prompt  # In real implementation, this would call LLM

        optimizer_tool = Tool(
            name="Content_Optimizer",
            func=optimize_content,
            description="Optimize content for engagement, conversions, or SEO. "
                        "Input should be the content to optimize."
        )

        tools = [
            content_research_tool,
            seo_tool,
            brand_voice_tool,
            grammar_tool,
            optimizer_tool
        ]

        super().__init__(
            name="Content Agent",
            description="Creates high-quality marketing content across multiple formats with SEO optimization",
            tools=tools,
            verbose=True
        )

        logger.info("content_agent_initialized")

    def get_specialized_prompt(self) -> str:
        """Get Content Agent system prompt"""
        return """You are a Content Creation Agent specializing in B2B marketing content.

Your primary responsibilities:
1. Create compelling, well-researched content
2. Optimize for SEO and engagement
3. Maintain consistent brand voice
4. Adapt tone for different channels
5. Include clear calls-to-action

Content Best Practices:
- Start with a strong hook
- Use clear, concise language
- Break up text with subheadings
- Include specific examples and data
- End with actionable takeaways
- Optimize for target keywords
- Match audience sophistication level

Writing Guidelines:
- Active voice over passive
- Short sentences (15-20 words avg)
- Short paragraphs (3-4 sentences)
- Use bullet points and lists
- Include relevant statistics
- Cite authoritative sources
- Avoid jargon unless necessary

SEO Requirements:
- Include focus keyword in title
- Use keyword in first paragraph
- Include keyword in at least one H2
- Add meta description (150-160 chars)
- Use descriptive alt text for images
- Include internal and external links

Output Format:
Always provide:
- Headline/Title
- Meta Description
- Content body with proper headings
- Suggested images/visuals
- Call-to-action
- Target keywords
- SEO score estimate

Be creative, data-driven, and audience-focused."""

    def create_blog_post(
        self,
        topic: str,
        keywords: Optional[List[str]] = None,
        word_count: int = 1500,
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """
        Create comprehensive blog post

        Args:
            topic: Blog post topic
            keywords: Target SEO keywords
            word_count: Desired word count
            tone: Content tone (professional, casual, authoritative, etc.)

        Returns:
            Dict with blog post content
        """
        keywords_str = ", ".join(keywords) if keywords else "not specified"

        prompt = f"""Create a comprehensive blog post on: {topic}

Requirements:
- Target word count: {word_count} words
- Tone: {tone}
- Target keywords: {keywords_str}

Structure:
1. Compelling headline (60 chars max, include main keyword)
2. Meta description (155 chars, include keyword, compelling)
3. Introduction (hook, context, what reader will learn)
4. Main body with H2/H3 subheadings
   - Use data and statistics
   - Include specific examples
   - Add actionable insights
5. Conclusion with key takeaways
6. Strong call-to-action

Additional elements:
- Suggested images (describe 3-4 images)
- Internal link opportunities (topics to link to)
- External link opportunities (authoritative sources)
- Social media snippet (280 chars for Twitter/LinkedIn)

Make it engaging, valuable, and optimized for SEO."""

        result = self.run(prompt)

        # Store in content library
        if result.get("output"):
            vector_store = get_vector_store()
            vector_store.add_content_to_library(
                content_id=f"blog_{datetime.utcnow().timestamp()}",
                content=result["output"],
                metadata={
                    "type": "blog_post",
                    "topic": topic,
                    "keywords": keywords or [],
                    "word_count": word_count,
                    "tone": tone,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            logger.info("blog_post_created", topic=topic)

        return result

    def create_linkedin_post(
        self,
        topic: str,
        post_type: str = "thought_leadership",
        length: str = "medium"
    ) -> Dict[str, Any]:
        """
        Create LinkedIn post

        Args:
            topic: Post topic
            post_type: Type (thought_leadership, company_update, industry_news, personal_story)
            length: short (100-300 words), medium (300-600), long (600-1000)

        Returns:
            Dict with LinkedIn post content
        """
        length_guidance = {
            "short": "100-300 words",
            "medium": "300-600 words",
            "long": "600-1000 words"
        }

        prompt = f"""Create a LinkedIn post on: {topic}

Post type: {post_type}
Length: {length} ({length_guidance.get(length, '300-600 words')})

Structure:
1. Strong hook (first 2 lines - appear above "see more")
   - Controversial statement, question, or bold claim
   - Make readers want to click "see more"

2. Main content
   - Personal insight or company perspective
   - Supporting data or examples
   - Storytelling elements
   - Break into short paragraphs (2-3 lines each)

3. Key takeaways
   - 3-5 bullet points or numbered list
   - Actionable insights

4. Call-to-action
   - Encourage comments
   - Ask a question
   - Share resources

Formatting:
- Use emojis strategically (1-3 max)
- Line breaks for readability
- Bold key phrases using **text**
- Include 3-5 relevant hashtags

Tone: Professional yet conversational, authentic, value-driven

Make it scroll-stopping and engagement-focused."""

        result = self.run(prompt)

        # Store in content library
        if result.get("output"):
            vector_store = get_vector_store()
            vector_store.add_content_to_library(
                content_id=f"linkedin_{datetime.utcnow().timestamp()}",
                content=result["output"],
                metadata={
                    "type": "linkedin_post",
                    "topic": topic,
                    "post_type": post_type,
                    "length": length,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            logger.info("linkedin_post_created", topic=topic)

        return result

    def create_email_campaign(
        self,
        campaign_type: str,
        audience: str,
        goal: str,
        sequence_count: int = 1
    ) -> Dict[str, Any]:
        """
        Create email campaign

        Args:
            campaign_type: newsletter, nurture, promotional, onboarding
            audience: Target audience description
            goal: Campaign goal/objective
            sequence_count: Number of emails in sequence

        Returns:
            Dict with email content
        """
        prompt = f"""Create {sequence_count}-email {campaign_type} campaign.

Target audience: {audience}
Goal: {goal}

For each email, provide:

1. Subject Line
   - Compelling (40-50 chars)
   - Personalization token: {{{{first_name}}}}
   - Create urgency or curiosity
   - A/B test variant

2. Preview Text
   - Complements subject line
   - 35-55 characters

3. Email Body
   - Greeting: Hi {{{{first_name}}}},
   - Opening (hook, context)
   - Main content (value, education, or offer)
   - Social proof or credibility
   - Clear CTA button text
   - Footer

4. Design Notes
   - Header image suggestion
   - CTA button color
   - Layout structure

5. Metrics
   - Expected open rate target
   - Expected click rate target

Best practices:
- Mobile-first design
- Single clear CTA
- Scannable content
- Personal tone
- Value-first approach

If sequence, ensure:
- Progressive value delivery
- Logical flow between emails
- Building momentum
- Varied content types"""

        result = self.run(prompt)

        # Store in content library
        if result.get("output"):
            vector_store = get_vector_store()
            vector_store.add_content_to_library(
                content_id=f"email_{datetime.utcnow().timestamp()}",
                content=result["output"],
                metadata={
                    "type": "email_campaign",
                    "campaign_type": campaign_type,
                    "audience": audience,
                    "sequence_count": sequence_count,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            logger.info("email_campaign_created", campaign_type=campaign_type)

        return result

    def create_social_post(
        self,
        platform: str,
        topic: str,
        with_image: bool = True
    ) -> Dict[str, Any]:
        """
        Create social media post

        Args:
            platform: twitter, facebook, instagram
            topic: Post topic
            with_image: Whether to include image suggestion

        Returns:
            Dict with social media post
        """
        platform_specs = {
            "twitter": "280 characters max, hashtags (2-3), mentions",
            "facebook": "40-80 words ideal, questions work well",
            "instagram": "Caption 125-150 words, hashtags (10-15), emojis"
        }

        prompt = f"""Create a {platform} post on: {topic}

Platform requirements: {platform_specs.get(platform, 'General social media')}

Provide:
1. Main post copy
2. Hashtags (relevant, mix of popular and niche)
3. Suggested posting time
4. Engagement tactics
"""

        if with_image:
            prompt += """5. Image description (for image generation)
   - Subject
   - Style
   - Colors
   - Mood
   - Dimensions for {platform}"""

        prompt += f"""

Make it {platform}-native, engaging, and shareable."""

        result = self.run(prompt)

        # Store in content library
        if result.get("output"):
            vector_store = get_vector_store()
            vector_store.add_content_to_library(
                content_id=f"social_{datetime.utcnow().timestamp()}",
                content=result["output"],
                metadata={
                    "type": "social_post",
                    "platform": platform,
                    "topic": topic,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            logger.info("social_post_created", platform=platform)

        return result

    def revise_content(
        self,
        original_content: str,
        feedback: str,
        revision_type: str = "targeted"
    ) -> Dict[str, Any]:
        """
        Revise content based on feedback

        Args:
            original_content: Content to revise
            feedback: Revision feedback
            revision_type: targeted (specific changes) or comprehensive (full rewrite)

        Returns:
            Dict with revised content
        """
        prompt = f"""Revise this content based on feedback.

Original Content:
{original_content}

Feedback:
{feedback}

Revision type: {revision_type}

Provide:
1. Revised content
2. Summary of changes made
3. Explanation of how feedback was addressed

Maintain original structure unless feedback requires change."""

        result = self.run(prompt)

        logger.info(
            "content_revised",
            revision_type=revision_type,
            feedback_length=len(feedback)
        )

        return result


def create_content_agent() -> ContentAgent:
    """Factory function to create Content Agent"""
    return ContentAgent()
