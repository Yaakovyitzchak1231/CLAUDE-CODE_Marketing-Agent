"""
Competitor Analysis Agent
Monitors competitors, analyzes their strategies, and identifies opportunities
"""

from typing import List, Dict, Any, Optional
from langchain.tools import Tool
from .base_agent import BaseAgent
from tools.search_tool import SearXNGTool, create_searxng_langchain_tool
from memory.vector_store import get_vector_store
import structlog
from datetime import datetime, timedelta


logger = structlog.get_logger()


class CompetitorAgent(BaseAgent):
    """
    Specialist agent for competitive intelligence

    Capabilities:
    - Competitor discovery and profiling
    - Content strategy analysis
    - Pricing and positioning tracking
    - Market share estimation
    - Competitive advantage identification
    - Alert on competitor changes
    """

    def __init__(self):
        """Initialize Competitor Agent"""

        # Initialize search tool
        search_tool = create_searxng_langchain_tool()

        # Initialize vector store for competitor data
        vector_store = get_vector_store()

        # Create competitor search tool
        def competitor_search(query: str) -> str:
            """Search for competitor information across web sources"""
            searxng = SearXNGTool()

            # Multi-source search
            results = {
                "general": searxng.search_general(query, max_results=5),
                "news": searxng.search_news(query, time_range="month", max_results=5),
                "social": searxng.search_social(query, max_results=3)
            }

            formatted = []

            # Format general results
            if results["general"]:
                formatted.append("=== General Web Results ===")
                for i, result in enumerate(results["general"], 1):
                    formatted.append(
                        f"{i}. {result['title']}\n"
                        f"   URL: {result['url']}\n"
                        f"   {result['content'][:200]}...\n"
                    )

            # Format news results
            if results["news"]:
                formatted.append("\n=== Recent News ===")
                for i, result in enumerate(results["news"], 1):
                    formatted.append(
                        f"{i}. {result['title']}\n"
                        f"   Published: {result.get('publishedDate', 'N/A')}\n"
                        f"   {result['content'][:150]}...\n"
                    )

            # Format social results
            if results["social"]:
                formatted.append("\n=== Social Media ===")
                for i, result in enumerate(results["social"], 1):
                    formatted.append(
                        f"{i}. {result['title']}\n"
                        f"   Source: {result.get('engine', 'Unknown')}\n"
                    )

            return "\n".join(formatted) if formatted else "No competitor data found."

        competitor_search_tool = Tool(
            name="Competitor_Search",
            func=competitor_search,
            description="Search for competitor information across general web, news, and social media. "
                        "Useful for discovering competitors, tracking their activities, and finding recent updates. "
                        "Input should be a competitor name or search query."
        )

        # Create vector search tool for historical competitor data
        def vector_competitor_search(query: str) -> str:
            """Search stored competitor data"""
            results = vector_store.search_competitor_content(query, n_results=5)

            if not results:
                return "No historical competitor data found."

            formatted = []
            for i, result in enumerate(results, 1):
                metadata = result.get('metadata', {})
                formatted.append(
                    f"{i}. {result['document'][:300]}...\n"
                    f"   Competitor: {metadata.get('competitor', 'Unknown')}\n"
                    f"   Source: {metadata.get('source', 'N/A')}\n"
                    f"   Relevance: {1 - result['distance']:.2f}\n"
                )

            return "\n\n".join(formatted)

        vector_tool = Tool(
            name="Historical_Competitor_Data",
            func=vector_competitor_search,
            description="Search historical competitor data stored in vector database. "
                        "Useful for finding past competitor analyses, strategies, and trends. "
                        "Input should be a search query about competitor activities."
        )

        # Create competitor analysis tool
        def analyze_competitor_data(data: str) -> str:
            """Analyze competitor data and extract insights"""
            prompt = f"""Analyze the following competitor data and provide strategic insights:

{data}

Provide:
1. Key Strengths (what they do well)
2. Key Weaknesses (gaps and vulnerabilities)
3. Market Positioning (how they differentiate)
4. Content Strategy (topics, formats, frequency)
5. Target Audience (who they're targeting)
6. Opportunities (what we can do better)

Be specific and actionable."""
            return prompt  # In real implementation, this would call LLM

        analysis_tool = Tool(
            name="Competitor_Analyzer",
            func=analyze_competitor_data,
            description="Analyze competitor data to extract strategic insights. "
                        "Input should be competitor information to analyze."
        )

        tools = [competitor_search_tool, vector_tool, analysis_tool]

        super().__init__(
            name="Competitor Agent",
            description="Conducts competitive intelligence, monitors competitors, and identifies strategic opportunities",
            tools=tools,
            verbose=True
        )

        logger.info("competitor_agent_initialized")

    def get_specialized_prompt(self) -> str:
        """Get Competitor Agent system prompt"""
        return """You are a Competitor Analysis Agent specializing in B2B competitive intelligence.

Your primary responsibilities:
1. Discover and profile key competitors
2. Monitor competitor content and marketing strategies
3. Track pricing, positioning, and messaging changes
4. Identify competitive advantages and weaknesses
5. Provide actionable competitive insights

Analysis Framework:
- Always compare competitors against each other
- Look for patterns in messaging and positioning
- Identify gaps in competitor offerings
- Track changes over time
- Prioritize recent information

Research Best Practices:
- Use multiple sources to validate findings
- Look for primary sources (company websites, press releases)
- Check social media for real-time updates
- Analyze customer reviews and feedback
- Track news and industry publications

Output Format:
Structure your analysis with:
- Competitor Profile (name, website, size, focus)
- Market Position (differentiation, target audience)
- Strengths & Weaknesses (SWOT analysis)
- Content Strategy (topics, channels, frequency)
- Pricing & Packaging (if available)
- Recent Activities (news, launches, changes)
- Strategic Recommendations (opportunities for us)

Be objective, specific, and actionable."""

    def profile_competitor(
        self,
        competitor_name: str,
        store_results: bool = True
    ) -> Dict[str, Any]:
        """
        Create comprehensive competitor profile

        Args:
            competitor_name: Competitor company name
            store_results: Whether to store results in vector DB

        Returns:
            Dict with competitor profile
        """
        prompt = f"""Create a comprehensive profile for this competitor: {competitor_name}

Research and provide:
1. Company Overview (size, location, founded, leadership)
2. Product/Service Offerings
3. Target Market & Audience
4. Market Position & Differentiation
5. Pricing Strategy (if available)
6. Marketing Channels & Presence
7. Recent News & Developments
8. Strengths & Weaknesses
9. Customer Perception (reviews, feedback)

Provide detailed findings with sources."""

        result = self.run(prompt)

        # Store in vector database if requested
        if store_results and result.get("output"):
            vector_store = get_vector_store()
            vector_store.add_competitor_content(
                competitor=competitor_name,
                content=result["output"],
                metadata={
                    "type": "profile",
                    "created_at": datetime.utcnow().isoformat(),
                    "competitor": competitor_name
                }
            )
            logger.info(
                "competitor_profile_stored",
                competitor=competitor_name
            )

        return result

    def analyze_content_strategy(
        self,
        competitor_name: str,
        content_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze competitor's content marketing strategy

        Args:
            competitor_name: Competitor company name
            content_types: Types to analyze (blog, social, video, etc.)

        Returns:
            Dict with content strategy analysis
        """
        content_types_str = ", ".join(content_types) if content_types else "all content types"

        prompt = f"""Analyze the content marketing strategy of {competitor_name}.

Focus on: {content_types_str}

Research and analyze:
1. Content Topics & Themes
2. Content Formats (blog, video, infographic, etc.)
3. Publishing Frequency
4. Content Quality & Depth
5. SEO Strategy (keywords, optimization)
6. Social Media Presence
7. Engagement Metrics (if available)
8. Content Distribution Channels
9. Content Gaps & Opportunities

Provide specific examples and actionable insights."""

        result = self.run(prompt)

        # Store analysis
        if result.get("output"):
            vector_store = get_vector_store()
            vector_store.add_competitor_content(
                competitor=competitor_name,
                content=result["output"],
                metadata={
                    "type": "content_strategy",
                    "created_at": datetime.utcnow().isoformat(),
                    "competitor": competitor_name,
                    "focus": content_types_str
                }
            )

        return result

    def monitor_changes(
        self,
        competitor_name: str,
        since_days: int = 30
    ) -> Dict[str, Any]:
        """
        Monitor recent competitor changes and activities

        Args:
            competitor_name: Competitor company name
            since_days: Look back period in days

        Returns:
            Dict with recent changes
        """
        prompt = f"""Monitor recent changes and activities for {competitor_name} in the last {since_days} days.

Look for:
1. Product/Service Launches
2. Pricing Changes
3. New Content or Campaigns
4. Press Releases & Announcements
5. Leadership Changes
6. Funding or Acquisitions
7. Website Updates
8. Social Media Activity
9. Customer Reviews/Feedback

Prioritize the most recent and significant changes."""

        result = self.run(prompt)

        # Store monitoring results
        if result.get("output"):
            vector_store = get_vector_store()
            vector_store.add_competitor_content(
                competitor=competitor_name,
                content=result["output"],
                metadata={
                    "type": "monitoring",
                    "created_at": datetime.utcnow().isoformat(),
                    "competitor": competitor_name,
                    "period_days": since_days
                }
            )

        return result

    def compare_competitors(
        self,
        competitors: List[str],
        comparison_criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple competitors side-by-side

        Args:
            competitors: List of competitor names
            comparison_criteria: Specific criteria to compare

        Returns:
            Dict with comparative analysis
        """
        competitors_str = ", ".join(competitors)
        criteria_str = ", ".join(comparison_criteria) if comparison_criteria else "all aspects"

        prompt = f"""Conduct a side-by-side comparison of these competitors: {competitors_str}

Compare on: {criteria_str}

Create a comparative analysis including:
1. Market Positioning Comparison
2. Product/Service Comparison
3. Pricing Comparison (if available)
4. Target Audience Comparison
5. Content Strategy Comparison
6. Strengths & Weaknesses Matrix
7. Market Share Estimation
8. Differentiation Analysis

Present in table format where possible. Identify clear winners and gaps."""

        result = self.run(prompt)

        # Store comparison
        if result.get("output"):
            vector_store = get_vector_store()
            for competitor in competitors:
                vector_store.add_competitor_content(
                    competitor=competitor,
                    content=result["output"],
                    metadata={
                        "type": "comparison",
                        "created_at": datetime.utcnow().isoformat(),
                        "competitors": competitors_str,
                        "criteria": criteria_str
                    }
                )

        return result

    def identify_opportunities(
        self,
        competitor_name: str,
        our_strengths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Identify competitive opportunities

        Args:
            competitor_name: Competitor to analyze
            our_strengths: Our company's strengths for comparison

        Returns:
            Dict with opportunity analysis
        """
        strengths_context = f"\n\nOur strengths: {', '.join(our_strengths)}" if our_strengths else ""

        prompt = f"""Analyze {competitor_name} to identify competitive opportunities.{strengths_context}

Identify:
1. Market Gaps (what they're not addressing)
2. Content Gaps (topics they're missing)
3. Audience Segments (underserved customers)
4. Feature Gaps (missing capabilities)
5. Messaging Weaknesses (unclear positioning)
6. Channel Opportunities (unused marketing channels)
7. Pricing Opportunities (market positioning)

For each opportunity, provide:
- Description of the gap
- Why it matters
- How we can capitalize on it
- Estimated impact

Prioritize high-impact, actionable opportunities."""

        result = self.run(prompt)
        return result


def create_competitor_agent() -> CompetitorAgent:
    """Factory function to create Competitor Agent"""
    return CompetitorAgent()
