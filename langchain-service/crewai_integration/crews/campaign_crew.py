"""
Campaign Management Crew

A CrewAI crew for full marketing campaign planning and execution.
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


class CampaignCrew:
    """
    Campaign Management Crew

    Plans and executes comprehensive marketing campaigns using:
    - Market Analyst: Audience analysis and positioning
    - Trend Analyst: Timing and trending topics
    - Content Creator: Campaign messaging and content
    - SEO Specialist: Content optimization

    Process: Hierarchical (parallel research, sequential execution)
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize the campaign crew.

        Args:
            verbose: Enable verbose logging
        """
        if not CREWAI_AVAILABLE:
            raise RuntimeError("CrewAI not installed. Run: pip install crewai")

        self.verbose = verbose

        # Import agents
        from ..agents import (
            create_market_analyst,
            create_trend_analyst,
            create_content_creator,
            create_seo_specialist
        )

        self.market_agent = create_market_analyst(verbose)
        self.trend_agent = create_trend_analyst(verbose)
        self.content_agent = create_content_creator(verbose)
        self.seo_agent = create_seo_specialist(verbose)

        logger.info(
            "campaign_crew_initialized",
            agents=['market', 'trend', 'content', 'seo']
        )

    def plan_campaign(
        self,
        campaign_brief: str,
        target_audience: str,
        campaign_duration: str = "4 weeks",
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Plan a comprehensive marketing campaign.

        Args:
            campaign_brief: Campaign goals and product/service
            target_audience: Target audience description
            campaign_duration: Campaign duration
            channels: Marketing channels (default: LinkedIn, blog, email)

        Returns:
            Dict with campaign plan and content recommendations
        """
        channels = channels or ['linkedin', 'blog', 'email']
        channel_str = ', '.join(channels)

        tasks = self._create_campaign_tasks(
            campaign_brief, target_audience, campaign_duration, channel_str
        )
        crew = self._get_crew(tasks)

        result = crew.kickoff()

        return {
            'campaign_type': 'full_campaign',
            'brief': campaign_brief,
            'target_audience': target_audience,
            'duration': campaign_duration,
            'channels': channels,
            'result': result,
            'process': 'crewai_sequential'
        }

    def create_content_calendar(
        self,
        campaign_theme: str,
        target_audience: str,
        duration_weeks: int = 4,
        posts_per_week: int = 3
    ) -> Dict[str, Any]:
        """
        Create a content calendar for a campaign.

        Args:
            campaign_theme: Overall campaign theme
            target_audience: Target audience
            duration_weeks: Number of weeks
            posts_per_week: Posts per week

        Returns:
            Dict with content calendar
        """
        tasks = self._create_calendar_tasks(
            campaign_theme, target_audience, duration_weeks, posts_per_week
        )
        crew = self._get_crew(tasks)

        result = crew.kickoff()

        return {
            'calendar_type': 'content_calendar',
            'theme': campaign_theme,
            'duration_weeks': duration_weeks,
            'posts_per_week': posts_per_week,
            'total_posts': duration_weeks * posts_per_week,
            'result': result,
            'process': 'crewai_sequential'
        }

    def _create_campaign_tasks(
        self,
        brief: str,
        audience: str,
        duration: str,
        channels: str
    ) -> List:
        """Create tasks for campaign planning."""
        # Task 1: Market analysis
        market_task = Task(
            description=f"""Analyze the market opportunity for this campaign:

            Campaign Brief: {brief}
            Target Audience: {audience}

            Provide:
            - Buyer persona profile (pain points, goals, objections)
            - Competitive positioning opportunities
            - Key messages that will resonate
            - Content preferences of the audience

            Be specific and actionable.""",
            expected_output="A detailed market analysis with buyer persona and positioning strategy.",
            agent=self.market_agent
        )

        # Task 2: Trend analysis
        trend_task = Task(
            description=f"""Identify trending topics and timing opportunities:

            Campaign Brief: {brief}
            Target Audience: {audience}
            Duration: {duration}

            Find:
            - Trending topics in the industry
            - Seasonal or timely hooks
            - Content angles that are gaining momentum
            - Hashtags and keywords with rising interest

            Focus on actionable timing recommendations.""",
            expected_output="Trend analysis with specific topic recommendations and timing windows.",
            agent=self.trend_agent
        )

        # Task 3: Campaign strategy and content plan
        strategy_task = Task(
            description=f"""Create a comprehensive campaign strategy:

            Campaign Brief: {brief}
            Target Audience: {audience}
            Duration: {duration}
            Channels: {channels}

            Use the market analysis and trend insights to create:
            - Campaign narrative and key themes
            - Content mix per channel
            - Messaging framework
            - Content calendar outline
            - Success metrics

            Make it specific and executable.""",
            expected_output="Complete campaign strategy with content plan and calendar outline.",
            agent=self.content_agent,
            context=[market_task, trend_task]
        )

        # Task 4: SEO and content optimization strategy
        seo_task = Task(
            description=f"""Create an SEO and content optimization strategy:

            Review the campaign strategy and provide:
            - Target keywords for each content piece
            - SEO best practices for each channel
            - Content optimization checklist
            - Suggested meta tags and descriptions

            Focus on practical, actionable guidance.""",
            expected_output="SEO strategy with keywords and optimization guidelines for the campaign.",
            agent=self.seo_agent,
            context=[strategy_task]
        )

        return [market_task, trend_task, strategy_task, seo_task]

    def _create_calendar_tasks(
        self,
        theme: str,
        audience: str,
        weeks: int,
        posts_per_week: int
    ) -> List:
        """Create tasks for content calendar generation."""
        total_posts = weeks * posts_per_week

        # Task 1: Topic research
        research_task = Task(
            description=f"""Research {total_posts} content topics for:

            Theme: {theme}
            Audience: {audience}

            For each topic, provide:
            - Topic title
            - Content angle
            - Target keyword
            - Why it will resonate

            Mix evergreen and timely content.""",
            expected_output=f"List of {total_posts} content topics with angles and keywords.",
            agent=self.trend_agent
        )

        # Task 2: Content calendar
        calendar_task = Task(
            description=f"""Create a {weeks}-week content calendar:

            Theme: {theme}
            Audience: {audience}
            Posts per week: {posts_per_week}

            For each week, specify:
            - Posting days and times
            - Content type (blog, LinkedIn, etc.)
            - Topic and headline
            - Key message
            - CTA

            Use the research provided. Balance content types.""",
            expected_output=f"Complete {weeks}-week content calendar with {total_posts} posts.",
            agent=self.content_agent,
            context=[research_task]
        )

        return [research_task, calendar_task]

    def _get_crew(self, tasks: List) -> 'Crew':
        """Create a crew with the given tasks."""
        agents = [
            self.market_agent,
            self.trend_agent,
            self.content_agent,
            self.seo_agent
        ]

        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=self.verbose
        )
