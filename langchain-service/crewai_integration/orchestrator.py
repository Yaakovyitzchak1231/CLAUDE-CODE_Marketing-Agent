"""
CrewAI Orchestrator

Main orchestrator that provides a unified interface for CrewAI-based workflows.
"""

from typing import Dict, Any, Optional, List
import structlog

logger = structlog.get_logger()


class CrewAIOrchestrator:
    """
    CrewAI Orchestrator

    Provides a unified interface for running CrewAI crews alongside
    the existing LangGraph supervisor.

    Features:
    - Content generation via ContentCrew
    - Campaign planning via CampaignCrew
    - Research via ResearchCrew
    - Easy switching between orchestration modes
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize the CrewAI orchestrator.

        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self._content_crew = None
        self._campaign_crew = None
        self._research_crew = None

        logger.info("crewai_orchestrator_initialized")

    @property
    def content_crew(self):
        """Lazy load ContentCrew."""
        if self._content_crew is None:
            from .crews import ContentCrew
            self._content_crew = ContentCrew(verbose=self.verbose)
        return self._content_crew

    @property
    def campaign_crew(self):
        """Lazy load CampaignCrew."""
        if self._campaign_crew is None:
            from .crews import CampaignCrew
            self._campaign_crew = CampaignCrew(verbose=self.verbose)
        return self._campaign_crew

    @property
    def research_crew(self):
        """Lazy load ResearchCrew."""
        if self._research_crew is None:
            from .crews import ResearchCrew
            self._research_crew = ResearchCrew(verbose=self.verbose)
        return self._research_crew

    # =========================================================================
    # Content Generation
    # =========================================================================

    def generate_content(
        self,
        content_type: str,
        topic: str,
        target_audience: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate marketing content.

        Args:
            content_type: "blog", "linkedin_post", "email"
            topic: Content topic
            target_audience: Target audience description
            **kwargs: Additional parameters per content type

        Returns:
            Dict with generated content
        """
        logger.info(
            "crewai_generate_content",
            content_type=content_type,
            topic=topic
        )

        if content_type == "blog":
            return self.content_crew.generate_blog_post(
                topic=topic,
                target_audience=target_audience,
                keywords=kwargs.get('keywords'),
                word_count=kwargs.get('word_count', 1500)
            )
        elif content_type == "linkedin_post":
            return self.content_crew.generate_linkedin_post(
                topic=topic,
                target_audience=target_audience,
                tone=kwargs.get('tone', 'professional')
            )
        else:
            raise ValueError(f"Unsupported content type: {content_type}")

    # =========================================================================
    # Campaign Management
    # =========================================================================

    def plan_campaign(
        self,
        campaign_brief: str,
        target_audience: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Plan a marketing campaign.

        Args:
            campaign_brief: Campaign goals and description
            target_audience: Target audience
            **kwargs: Additional parameters

        Returns:
            Dict with campaign plan
        """
        logger.info(
            "crewai_plan_campaign",
            brief=campaign_brief[:50] + "..."
        )

        return self.campaign_crew.plan_campaign(
            campaign_brief=campaign_brief,
            target_audience=target_audience,
            campaign_duration=kwargs.get('duration', '4 weeks'),
            channels=kwargs.get('channels')
        )

    def create_content_calendar(
        self,
        campaign_theme: str,
        target_audience: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a content calendar.

        Args:
            campaign_theme: Campaign theme
            target_audience: Target audience
            **kwargs: Additional parameters

        Returns:
            Dict with content calendar
        """
        logger.info(
            "crewai_create_calendar",
            theme=campaign_theme
        )

        return self.campaign_crew.create_content_calendar(
            campaign_theme=campaign_theme,
            target_audience=target_audience,
            duration_weeks=kwargs.get('duration_weeks', 4),
            posts_per_week=kwargs.get('posts_per_week', 3)
        )

    # =========================================================================
    # Research
    # =========================================================================

    def conduct_research(
        self,
        research_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Conduct research.

        Args:
            research_type: "market", "competitor", "trends"
            **kwargs: Parameters for specific research type

        Returns:
            Dict with research findings
        """
        logger.info(
            "crewai_conduct_research",
            research_type=research_type
        )

        if research_type == "market":
            return self.research_crew.conduct_market_research(
                product_description=kwargs.get('product_description'),
                target_market=kwargs.get('target_market'),
                geography=kwargs.get('geography', 'global')
            )
        elif research_type == "competitor":
            return self.research_crew.analyze_competitor(
                competitor_name=kwargs.get('competitor_name'),
                competitor_url=kwargs.get('competitor_url'),
                analysis_depth=kwargs.get('depth', 'comprehensive')
            )
        elif research_type == "trends":
            return self.research_crew.identify_trends(
                industry=kwargs.get('industry'),
                time_range=kwargs.get('time_range', 'month'),
                include_predictions=kwargs.get('include_predictions', True)
            )
        else:
            raise ValueError(f"Unsupported research type: {research_type}")

    # =========================================================================
    # Unified Interface
    # =========================================================================

    def run(
        self,
        task_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run any CrewAI task through a unified interface.

        Args:
            task_type: Task type to run:
                - "content_blog", "content_linkedin"
                - "campaign_plan", "campaign_calendar"
                - "research_market", "research_competitor", "research_trends"
            **kwargs: Task-specific parameters

        Returns:
            Dict with task results
        """
        task_mapping = {
            # Content tasks
            'content_blog': lambda: self.generate_content(
                content_type='blog', **kwargs
            ),
            'content_linkedin': lambda: self.generate_content(
                content_type='linkedin_post', **kwargs
            ),

            # Campaign tasks
            'campaign_plan': lambda: self.plan_campaign(**kwargs),
            'campaign_calendar': lambda: self.create_content_calendar(**kwargs),

            # Research tasks
            'research_market': lambda: self.conduct_research(
                research_type='market', **kwargs
            ),
            'research_competitor': lambda: self.conduct_research(
                research_type='competitor', **kwargs
            ),
            'research_trends': lambda: self.conduct_research(
                research_type='trends', **kwargs
            )
        }

        if task_type not in task_mapping:
            raise ValueError(
                f"Unknown task type: {task_type}. "
                f"Available: {list(task_mapping.keys())}"
            )

        return task_mapping[task_type]()

    def get_available_tasks(self) -> List[str]:
        """Get list of available task types."""
        return [
            'content_blog',
            'content_linkedin',
            'campaign_plan',
            'campaign_calendar',
            'research_market',
            'research_competitor',
            'research_trends'
        ]


# Singleton instance
_orchestrator: Optional[CrewAIOrchestrator] = None


def get_orchestrator(verbose: bool = True) -> CrewAIOrchestrator:
    """
    Get the CrewAI orchestrator instance.

    Args:
        verbose: Enable verbose logging

    Returns:
        CrewAIOrchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CrewAIOrchestrator(verbose=verbose)
    return _orchestrator
