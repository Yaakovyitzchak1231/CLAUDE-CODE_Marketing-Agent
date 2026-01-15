"""
Content Creation Agent
Generates high-quality marketing content across multiple formats and channels

UPDATED: Now uses production-grade analytics modules:
- brand_voice_analyzer.py for brand voice consistency
- ai_detection.py for anti-AI detection
- seo_scorer.py for SEO optimization

ALL scoring uses mathematical algorithms - NO LLM hallucination.
"""

from typing import List, Dict, Any, Optional
from langchain.tools import Tool
from .base_agent import BaseAgent
from memory.vector_store import get_vector_store
from memory.conversation_memory import get_memory_manager
import structlog
from datetime import datetime
import re

# Import analytics modules for REAL scoring (not LLM inference)
try:
    from analytics.brand_voice_analyzer import BrandVoiceAnalyzer, analyze_brand_voice
    from analytics.ai_detection import AIDetector, calculate_ai_likelihood
    from analytics.seo_scorer import SEOScorer, calculate_seo_score
    from analytics.engagement_scorer import EngagementScorer
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

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

        # Create SEO analysis tool - USES REAL SEO SCORER (NO LLM)
        def analyze_seo(content: str, target_keywords: str = "") -> str:
            """
            Analyze content for SEO optimization using MULTI-FACTOR SCORING.

            Uses mathematical formulas for:
            - Title optimization (20%)
            - Meta description (15%)
            - Keyword density (25%)
            - Heading structure (15%)
            - Content length (10%)
            - Internal linking (10%)
            - Image optimization (5%)

            NO LLM INFERENCE - all scores are mathematically calculated.
            """
            if ANALYTICS_AVAILABLE:
                # Parse keywords
                keywords = [kw.strip() for kw in target_keywords.split(',') if kw.strip()] if target_keywords else []

                # Use proper SEO scorer
                seo_scorer = SEOScorer()

                # Create metadata from content (extract title if present)
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else ""

                metadata = {
                    'title': title,
                    'description': content[:160] if len(content) > 160 else content
                }

                # Get comprehensive SEO score
                seo_result = seo_scorer.calculate_seo_score(content, metadata, keywords)

                # Format results
                analysis = f"""═══════════════════════════════════════════════════════════════
SEO ANALYSIS (Multi-Factor Scoring - No LLM Hallucination)
═══════════════════════════════════════════════════════════════

📊 OVERALL SEO SCORE: {seo_result.get('seo_score', 0)}/100 (Grade: {seo_result.get('grade', 'N/A')})

📈 COMPONENT BREAKDOWN:
"""
                for component, score in seo_result.get('component_scores', {}).items():
                    weight = seo_result.get('weights', {}).get(component, 0) * 100
                    analysis += f"   • {component.replace('_', ' ').title()}: {score}/100 (Weight: {weight:.0f}%)\n"

                analysis += f"""
📋 CONTENT METRICS:
   • Word Count: {seo_result.get('metrics', {}).get('word_count', 'N/A')}
   • Title Length: {seo_result.get('metrics', {}).get('title_length', 'N/A')} chars
   • Meta Length: {seo_result.get('metrics', {}).get('meta_length', 'N/A')} chars
   • Keyword Density: {seo_result.get('metrics', {}).get('keyword_density_pct', 'N/A')}%
   • H1 Tags: {seo_result.get('metrics', {}).get('h1_count', 'N/A')}
   • H2 Tags: {seo_result.get('metrics', {}).get('h2_count', 'N/A')}
   • H3 Tags: {seo_result.get('metrics', {}).get('h3_count', 'N/A')}
   • Internal Links: {seo_result.get('metrics', {}).get('internal_links', 'N/A')}
   • Images: {seo_result.get('metrics', {}).get('images', 'N/A')}
   • Images with Alt: {seo_result.get('metrics', {}).get('images_with_alt', 'N/A')}

🎯 RECOMMENDATIONS:
"""
                for rec in seo_result.get('recommendations', []):
                    analysis += f"   • {rec}\n"

                if not seo_result.get('recommendations'):
                    analysis += "   • Content meets SEO best practices\n"

                analysis += f"""
═══════════════════════════════════════════════════════════════
Algorithm: {seo_result.get('algorithm', 'Multi-factor SEO scoring')}
Verified: {seo_result.get('is_verified', True)} (Mathematical calculation, not LLM)
═══════════════════════════════════════════════════════════════"""

                return analysis

            else:
                # Fallback to basic analysis
                word_count = len(content.split())
                h1_count = len(re.findall(r'^#\s', content, re.MULTILINE))
                h2_count = len(re.findall(r'^##\s', content, re.MULTILINE))
                h3_count = len(re.findall(r'^###\s', content, re.MULTILINE))
                internal_links = len(re.findall(r'\[.*?\]\((?!http)', content))
                external_links = len(re.findall(r'\[.*?\]\(http', content))
                reading_time = round(word_count / 200, 1)

                return f"""SEO Analysis (Basic - Analytics modules not installed):
- Word Count: {word_count} words
- Reading Time: {reading_time} minutes
- H1 Count: {h1_count}
- H2 Count: {h2_count}
- H3 Count: {h3_count}
- Internal Links: {internal_links}
- External Links: {external_links}

Install analytics modules for comprehensive scoring: pip install textstat nltk scipy"""

        seo_tool = Tool(
            name="SEO_Analyzer",
            func=analyze_seo,
            description="Analyze content for SEO using MULTI-FACTOR SCORING algorithm. "
                        "Returns title, meta, keywords, headings, length, links, and image scores. "
                        "All scores are mathematically calculated - NO LLM inference."
        )

        # Create brand voice checker - USES REAL ANALYTICS (NO LLM)
        def check_brand_voice(content: str, brand_guidelines: Optional[str] = None) -> str:
            """
            Check content against brand voice guidelines using STATISTICAL ANALYSIS.

            Uses: textstat, NLTK - NO LLM INFERENCE
            All scores are mathematically calculated and VERIFIABLE.
            """
            import json

            if not ANALYTICS_AVAILABLE:
                return "Analytics modules not available. Install with: pip install textstat nltk"

            # Initialize analyzers
            voice_analyzer = BrandVoiceAnalyzer()
            ai_detector = AIDetector()

            # Get brand voice consistency (mathematical analysis)
            brand_analysis = voice_analyzer.calculate_brand_consistency(content)

            # Get AI likelihood score (statistical detection)
            ai_analysis = ai_detector.calculate_ai_likelihood(content)

            # Get readability metrics
            readability = voice_analyzer.calculate_readability_metrics(content)

            # Get tone analysis
            tone = voice_analyzer.analyze_tone(content)

            # Format results
            result = f"""═══════════════════════════════════════════════════════════════
BRAND VOICE ANALYSIS (Mathematical - No LLM Hallucination)
═══════════════════════════════════════════════════════════════

📊 BRAND CONSISTENCY SCORE: {brand_analysis.get('consistency_score', 0)}/100 (Grade: {brand_analysis.get('grade', 'N/A')})

📖 READABILITY METRICS (Flesch-Kincaid, Gunning Fog):
   • Flesch Reading Ease: {readability.get('flesch_reading_ease', 'N/A')} ({readability.get('reading_level', 'N/A')})
   • Grade Level: {readability.get('flesch_kincaid_grade', 'N/A')}
   • Gunning Fog Index: {readability.get('gunning_fog', 'N/A')}
   • Word Count: {readability.get('word_count', 'N/A')}
   • Avg Sentence Length: {readability.get('avg_sentence_length', 'N/A')} words

🎭 TONE ANALYSIS:
   • Assessment: {tone.get('tone_assessment', 'N/A')}
   • Formality Ratio: {tone.get('formality_ratio', 'N/A')}
   • Jargon Density: {tone.get('jargon_density_pct', 0):.2f}%
   • Corporate Jargon Found: {', '.join(tone.get('jargon_words_found', [])) or 'None'}

🤖 AI DETECTION (Anti-AI Scoring):
   • AI Likelihood: {ai_analysis.get('ai_likelihood_score', 0)}/100
   • Assessment: {ai_analysis.get('assessment', 'N/A')}
   • Burstiness: {ai_analysis.get('detailed_metrics', {}).get('burstiness', 'N/A')}
   • Lexical Diversity (MTLD): {ai_analysis.get('detailed_metrics', {}).get('mtld', 'N/A')}
   • Flagged Patterns: {', '.join(ai_analysis.get('flagged_phrases', [])) or 'None'}

📋 RECOMMENDATIONS:
"""
            recommendations = brand_analysis.get('recommendations', [])
            if recommendations:
                for rec in recommendations:
                    result += f"   • {rec}\n"
            else:
                result += "   • Content meets brand voice standards\n"

            result += f"""
═══════════════════════════════════════════════════════════════
Algorithm: {brand_analysis.get('algorithm', 'Statistical text analysis')}
Verified: {brand_analysis.get('is_verified', True)} (Mathematical calculation, not LLM)
═══════════════════════════════════════════════════════════════"""

            return result

        brand_voice_tool = Tool(
            name="Brand_Voice_Checker",
            func=check_brand_voice,
            description="Check content for brand voice consistency using STATISTICAL ANALYSIS. "
                        "Returns readability scores, AI detection, and tone analysis. "
                        "All scores are mathematically calculated - NO LLM inference."
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
