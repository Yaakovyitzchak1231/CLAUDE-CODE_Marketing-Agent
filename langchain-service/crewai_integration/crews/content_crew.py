"""
Content Generation Crew

A CrewAI crew optimized for marketing content generation.
"""

from typing import Dict, Any, Optional, List
import structlog

logger = structlog.get_logger()

CREWAI_AVAILABLE = False
try:
    from crewai import Crew, Task, Process
    CREWAI_AVAILABLE = True
except ImportError:
    pass


class ContentCrew:
    """
    Content Generation Crew

    Creates marketing content using a team of specialized agents:
    - Research Specialist: Gathers background information
    - Content Creator: Writes engaging content
    - SEO Specialist: Optimizes for search (optional)

    Process: Sequential (Research -> Write -> Optimize)
    """

    def __init__(self, verbose: bool = True, include_seo: bool = True):
        """
        Initialize the content crew.

        Args:
            verbose: Enable verbose logging
            include_seo: Include SEO optimization step
        """
        if not CREWAI_AVAILABLE:
            raise RuntimeError("CrewAI not installed. Run: pip install crewai")

        self.verbose = verbose
        self.include_seo = include_seo
        self._crew = None

        # Import agents
        from ..agents import (
            create_research_specialist,
            create_content_creator,
            create_seo_specialist
        )

        self.research_agent = create_research_specialist(verbose)
        self.content_agent = create_content_creator(verbose)
        self.seo_agent = create_seo_specialist(verbose) if include_seo else None

        logger.info(
            "content_crew_initialized",
            include_seo=include_seo,
            agents=['research', 'content'] + (['seo'] if include_seo else [])
        )

    def generate_blog_post(
        self,
        topic: str,
        target_audience: str,
        keywords: Optional[List[str]] = None,
        word_count: int = 1500
    ) -> Dict[str, Any]:
        """
        Generate a blog post with research and SEO optimization.

        Args:
            topic: Blog topic
            target_audience: Target audience description
            keywords: Target SEO keywords
            word_count: Target word count

        Returns:
            Dict with blog content and metadata
        """
        tasks = self._create_blog_tasks(topic, target_audience, keywords, word_count)
        crew = self._get_crew(tasks)

        result = crew.kickoff()

        return {
            'content_type': 'blog_post',
            'topic': topic,
            'target_audience': target_audience,
            'result': result,
            'process': 'crewai_sequential'
        }

    def generate_linkedin_post(
        self,
        topic: str,
        target_audience: str,
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """
        Generate a LinkedIn post.

        Args:
            topic: Post topic
            target_audience: Target audience
            tone: Tone of voice

        Returns:
            Dict with post content and metadata
        """
        tasks = self._create_linkedin_tasks(topic, target_audience, tone)
        crew = self._get_crew(tasks)

        result = crew.kickoff()

        return {
            'content_type': 'linkedin_post',
            'topic': topic,
            'target_audience': target_audience,
            'tone': tone,
            'result': result,
            'process': 'crewai_sequential'
        }

    def _create_blog_tasks(
        self,
        topic: str,
        audience: str,
        keywords: Optional[List[str]],
        word_count: int
    ) -> List:
        """Create tasks for blog post generation."""
        keyword_str = ', '.join(keywords) if keywords else 'none specified'

        # Task 1: Research
        research_task = Task(
            description=f"""Research the topic: {topic}

            Target audience: {audience}

            Find:
            - Key statistics and data points
            - Recent industry trends
            - Expert opinions and quotes
            - Competitor content angles

            Prioritize authoritative sources (government data, major publications).
            Provide 5-7 key insights with source attribution.""",
            expected_output="A research brief with key statistics, trends, and insights for the blog post.",
            agent=self.research_agent
        )

        # Task 2: Write content
        write_task = Task(
            description=f"""Write a {word_count}-word blog post on: {topic}

            Target audience: {audience}
            Target keywords: {keyword_str}

            Requirements:
            - Engaging, human-sounding prose (avoid AI-like writing)
            - Clear structure with headers (H2, H3)
            - Incorporate research insights naturally
            - Include a compelling hook and strong conclusion
            - Add relevant examples and actionable takeaways

            Use the research provided. Write for a B2B executive audience.""",
            expected_output=f"A complete {word_count}-word blog post with headers, body, and conclusion.",
            agent=self.content_agent,
            context=[research_task]
        )

        tasks = [research_task, write_task]

        # Task 3: SEO optimization (optional)
        if self.include_seo and self.seo_agent:
            seo_task = Task(
                description=f"""Optimize the blog post for SEO.

                Target keywords: {keyword_str}

                Review and optimize:
                - Title tag and meta description
                - Keyword placement (natural, not forced)
                - Header structure (H1, H2, H3)
                - Internal/external linking suggestions
                - Readability for target audience

                Provide the final optimized post plus SEO metadata.""",
                expected_output="SEO-optimized blog post with meta tags and optimization notes.",
                agent=self.seo_agent,
                context=[write_task]
            )
            tasks.append(seo_task)

        return tasks

    def _create_linkedin_tasks(
        self,
        topic: str,
        audience: str,
        tone: str
    ) -> List:
        """Create tasks for LinkedIn post generation."""
        # Task 1: Quick research
        research_task = Task(
            description=f"""Quick research for a LinkedIn post on: {topic}

            Find:
            - 1-2 compelling statistics
            - A timely hook (recent news, trend)
            - Key point for the audience: {audience}

            Keep research brief and focused.""",
            expected_output="2-3 key insights for a LinkedIn post.",
            agent=self.research_agent
        )

        # Task 2: Write LinkedIn post
        write_task = Task(
            description=f"""Write a LinkedIn post on: {topic}

            Target audience: {audience}
            Tone: {tone}

            Requirements:
            - Hook in the first line (stop the scroll)
            - Under 1300 characters (LinkedIn optimal)
            - Use line breaks for readability
            - Include a call-to-action or question
            - Sound like a real person, not AI
            - Avoid hashtag spam (0-3 hashtags max)

            Make it shareable and comment-worthy.""",
            expected_output="A complete LinkedIn post ready to publish.",
            agent=self.content_agent,
            context=[research_task]
        )

        return [research_task, write_task]

    def _get_crew(self, tasks: List) -> 'Crew':
        """Create a crew with the given tasks."""
        agents = [self.research_agent, self.content_agent]
        if self.include_seo and self.seo_agent:
            agents.append(self.seo_agent)

        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=self.verbose
        )
