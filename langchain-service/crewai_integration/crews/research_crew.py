"""
Research Crew

A CrewAI crew focused on market research and competitive intelligence.
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


class ResearchCrew:
    """
    Research Crew

    Conducts comprehensive research using:
    - Research Specialist: Deep research from authoritative sources
    - Market Analyst: Market sizing and opportunity analysis
    - Trend Analyst: Emerging trends and timing

    Process: Sequential or parallel depending on task type
    """

    def __init__(self, verbose: bool = True):
        """
        Initialize the research crew.

        Args:
            verbose: Enable verbose logging
        """
        if not CREWAI_AVAILABLE:
            raise RuntimeError("CrewAI not installed. Run: pip install crewai")

        self.verbose = verbose

        # Import agents
        from ..agents import (
            create_research_specialist,
            create_market_analyst,
            create_trend_analyst
        )

        self.research_agent = create_research_specialist(verbose)
        self.market_agent = create_market_analyst(verbose)
        self.trend_agent = create_trend_analyst(verbose)

        logger.info(
            "research_crew_initialized",
            agents=['research', 'market', 'trend']
        )

    def conduct_market_research(
        self,
        product_description: str,
        target_market: str,
        geography: str = "global"
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive market research.

        Args:
            product_description: Product or service description
            target_market: Target market description
            geography: Geographic focus

        Returns:
            Dict with research findings
        """
        tasks = self._create_market_research_tasks(
            product_description, target_market, geography
        )
        crew = self._get_crew(tasks)

        result = crew.kickoff()

        return {
            'research_type': 'market_research',
            'product': product_description,
            'market': target_market,
            'geography': geography,
            'result': result,
            'process': 'crewai_sequential'
        }

    def analyze_competitor(
        self,
        competitor_name: str,
        competitor_url: Optional[str] = None,
        analysis_depth: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Analyze a competitor.

        Args:
            competitor_name: Competitor company name
            competitor_url: Competitor website URL
            analysis_depth: "quick", "standard", or "comprehensive"

        Returns:
            Dict with competitor analysis
        """
        tasks = self._create_competitor_tasks(
            competitor_name, competitor_url, analysis_depth
        )
        crew = self._get_crew(tasks)

        result = crew.kickoff()

        return {
            'research_type': 'competitor_analysis',
            'competitor': competitor_name,
            'url': competitor_url,
            'depth': analysis_depth,
            'result': result,
            'process': 'crewai_sequential'
        }

    def identify_trends(
        self,
        industry: str,
        time_range: str = "month",
        include_predictions: bool = True
    ) -> Dict[str, Any]:
        """
        Identify industry trends.

        Args:
            industry: Industry to analyze
            time_range: "week", "month", or "quarter"
            include_predictions: Include future predictions

        Returns:
            Dict with trend analysis
        """
        tasks = self._create_trend_tasks(industry, time_range, include_predictions)
        crew = self._get_crew(tasks)

        result = crew.kickoff()

        return {
            'research_type': 'trend_analysis',
            'industry': industry,
            'time_range': time_range,
            'include_predictions': include_predictions,
            'result': result,
            'process': 'crewai_sequential'
        }

    def _create_market_research_tasks(
        self,
        product: str,
        market: str,
        geography: str
    ) -> List:
        """Create tasks for market research."""
        # Task 1: Market sizing
        sizing_task = Task(
            description=f"""Calculate market size (TAM/SAM/SOM) for:

            Product: {product}
            Target Market: {market}
            Geography: {geography}

            Provide:
            - Total Addressable Market (TAM) with calculation
            - Serviceable Addressable Market (SAM)
            - Serviceable Obtainable Market (SOM)
            - Growth rate projections
            - Data sources used (cite authoritative sources)

            Use government data (BLS, Census) where available.""",
            expected_output="Market sizing analysis with TAM/SAM/SOM and data sources.",
            agent=self.market_agent
        )

        # Task 2: Buyer research
        buyer_task = Task(
            description=f"""Research the target buyer for:

            Product: {product}
            Target Market: {market}

            Provide:
            - Buyer persona profile
            - Pain points and challenges
            - Buying behavior and journey
            - Decision criteria
            - Budget considerations
            - Information sources they trust

            Be specific and data-driven.""",
            expected_output="Detailed buyer persona with pain points and buying behavior.",
            agent=self.research_agent
        )

        # Task 3: Trend context
        trend_task = Task(
            description=f"""Analyze trends affecting this market:

            Product: {product}
            Target Market: {market}
            Geography: {geography}

            Find:
            - Market tailwinds and headwinds
            - Technology trends impacting the space
            - Regulatory changes to consider
            - Competitive landscape shifts

            Focus on actionable insights.""",
            expected_output="Trend analysis with market drivers and risks.",
            agent=self.trend_agent
        )

        return [sizing_task, buyer_task, trend_task]

    def _create_competitor_tasks(
        self,
        name: str,
        url: Optional[str],
        depth: str
    ) -> List:
        """Create tasks for competitor analysis."""
        url_context = f"Website: {url}" if url else "Website: Not provided"

        # Task 1: Basic research
        research_task = Task(
            description=f"""Research competitor: {name}
            {url_context}

            Find:
            - Company overview (size, funding, history)
            - Product/service offerings
            - Pricing model (if available)
            - Target customers
            - Key differentiators
            - Recent news and announcements

            Use authoritative sources.""",
            expected_output="Comprehensive competitor profile with key details.",
            agent=self.research_agent
        )

        tasks = [research_task]

        if depth in ["standard", "comprehensive"]:
            # Task 2: Market position analysis
            position_task = Task(
                description=f"""Analyze {name}'s market position:

                Based on the research provided, analyze:
                - Market share estimate
                - Competitive advantages
                - Weaknesses and vulnerabilities
                - Customer sentiment (if available)
                - Positioning strategy

                Identify opportunities to differentiate against them.""",
                expected_output="Market position analysis with competitive opportunities.",
                agent=self.market_agent,
                context=[research_task]
            )
            tasks.append(position_task)

        if depth == "comprehensive":
            # Task 3: Content strategy analysis
            content_task = Task(
                description=f"""Analyze {name}'s content strategy:

                Research their:
                - Blog topics and frequency
                - Social media presence
                - SEO keywords they rank for
                - Content themes and messaging
                - Engagement levels

                Identify content gaps we could exploit.""",
                expected_output="Content strategy analysis with actionable gaps.",
                agent=self.trend_agent,
                context=[research_task]
            )
            tasks.append(content_task)

        return tasks

    def _create_trend_tasks(
        self,
        industry: str,
        time_range: str,
        include_predictions: bool
    ) -> List:
        """Create tasks for trend analysis."""
        # Task 1: Current trends
        current_task = Task(
            description=f"""Identify current trends in: {industry}
            Time range: {time_range}

            Find:
            - Top 5 trending topics
            - Search interest trends (Google Trends data)
            - Social media buzz
            - Industry publication focus areas
            - Recent conference themes

            Rank by momentum and relevance.""",
            expected_output="List of current industry trends with momentum indicators.",
            agent=self.trend_agent
        )

        tasks = [current_task]

        if include_predictions:
            # Task 2: Predictions
            prediction_task = Task(
                description=f"""Predict emerging trends in: {industry}

                Based on current trend analysis, identify:
                - 3-5 emerging trends to watch
                - Timing predictions (when will they peak)
                - Early signals to monitor
                - Potential impact on the industry

                Be specific about timing windows.""",
                expected_output="Trend predictions with timing and impact assessment.",
                agent=self.market_agent,
                context=[current_task]
            )
            tasks.append(prediction_task)

        return tasks

    def _get_crew(self, tasks: List) -> 'Crew':
        """Create a crew with the given tasks."""
        agents = [
            self.research_agent,
            self.market_agent,
            self.trend_agent
        ]

        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=self.verbose
        )
