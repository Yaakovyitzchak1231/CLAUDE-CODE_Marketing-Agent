"""
Research Agent
Conducts market research, industry trends, and topic analysis
"""

from typing import List
from langchain.tools import Tool
from .base_agent import BaseAgent
from tools.search_tool import SearXNGTool, create_searxng_langchain_tool
from memory.vector_store import get_vector_store
import structlog


logger = structlog.get_logger()


class ResearchAgent(BaseAgent):
    """
    Specialist agent for research tasks

    Capabilities:
    - Market research
    - Industry trend analysis
    - Topic discovery
    - Data synthesis
    - Insight generation
    """

    def __init__(self):
        """Initialize Research Agent"""

        # Initialize search tool
        search_tool = create_searxng_langchain_tool()

        # Initialize vector store for knowledge retrieval
        vector_store = get_vector_store()

        # Create vector search tool
        def vector_search(query: str) -> str:
            """Search historical content and insights"""
            results = vector_store.search_similar_content(query, n_results=3)

            if not results:
                return "No relevant historical content found."

            formatted = []
            for i, result in enumerate(results, 1):
                formatted.append(
                    f"{i}. {result['document']}\n"
                    f"   (Relevance: {1 - result['distance']:.2f})"
                )

            return "\n\n".join(formatted)

        vector_tool = Tool(
            name="Knowledge_Search",
            func=vector_search,
            description="Search historical content library and past research. "
                        "Useful for finding related insights, past analyses, and building on previous work. "
                        "Input should be a search query."
        )

        # Create data synthesis tool
        def synthesize_data(data: str) -> str:
            """Synthesize research data into insights"""
            # This would call the LLM to analyze and synthesize
            prompt = f"""Analyze the following research data and provide key insights:

{data}

Provide:
1. Key findings (3-5 bullet points)
2. Trends and patterns
3. Actionable recommendations
"""
            return prompt  # In real implementation, this would call LLM

        synthesis_tool = Tool(
            name="Data_Synthesizer",
            func=synthesize_data,
            description="Synthesize raw research data into actionable insights. "
                        "Input should be research data or search results to analyze."
        )

        tools = [search_tool, vector_tool, synthesis_tool]

        super().__init__(
            name="Research Agent",
            description="Conducts comprehensive market research, analyzes industry trends, and generates insights",
            tools=tools,
            verbose=True
        )

        logger.info("research_agent_initialized")

    def get_specialized_prompt(self) -> str:
        """Get Research Agent system prompt"""
        return """You are a Research Agent specializing in B2B market research and analysis.

Your primary responsibilities:
1. Conduct thorough market research using web search
2. Identify industry trends and emerging topics
3. Analyze competitor strategies and positioning
4. Synthesize data into actionable insights
5. Provide data-driven recommendations

Research Best Practices:
- Use multiple search queries to get comprehensive coverage
- Cross-reference information from different sources
- Look for recent data (prefer last 6-12 months)
- Identify both opportunities and challenges
- Support insights with specific examples and data points

Output Format:
Always structure your research with:
- Executive Summary
- Key Findings (bullet points)
- Detailed Analysis
- Recommendations
- Sources

Be thorough but concise. Focus on actionable intelligence."""

    def research_market(self, topic: str, industry: str = None) -> dict:
        """
        Conduct market research on a topic

        Args:
            topic: Research topic
            industry: Optional industry focus

        Returns:
            Dict with research findings
        """
        query = f"{industry} {topic}" if industry else topic

        prompt = f"""Conduct comprehensive market research on: {query}

Research areas:
1. Market size and growth trends
2. Key players and competitors
3. Industry challenges and opportunities
4. Emerging trends and innovations
5. Target audience insights

Provide detailed findings with sources."""

        result = self.run(prompt)
        return result

    def analyze_trends(self, topic: str, timeframe: str = "6 months") -> dict:
        """
        Analyze trends for a topic

        Args:
            topic: Topic to analyze
            timeframe: Timeframe for trend analysis

        Returns:
            Dict with trend analysis
        """
        prompt = f"""Analyze current trends related to: {topic}

Timeframe: Last {timeframe}

Focus on:
1. What's gaining traction?
2. What's declining?
3. What's emerging?
4. What patterns do you see?
5. What's the trajectory?

Provide insights with recent examples."""

        result = self.run(prompt)
        return result

    def competitor_landscape(self, industry: str, competitors: List[str] = None) -> dict:
        """
        Analyze competitive landscape

        Args:
            industry: Industry sector
            competitors: Optional list of specific competitors

        Returns:
            Dict with competitive analysis
        """
        if competitors:
            competitor_list = ", ".join(competitors)
            prompt = f"""Analyze the competitive landscape for these companies: {competitor_list}

Industry: {industry}

Research:
1. Market positioning of each competitor
2. Unique value propositions
3. Strengths and weaknesses
4. Recent news and developments
5. Content and marketing strategies

Provide comparative analysis."""
        else:
            prompt = f"""Identify and analyze top competitors in: {industry}

Research:
1. Who are the market leaders?
2. What are their positioning strategies?
3. What content approaches do they use?
4. What opportunities exist for differentiation?

Provide competitive landscape overview."""

        result = self.run(prompt)
        return result

    def audience_insights(self, target_audience: str, industry: str = None) -> dict:
        """
        Generate audience insights

        Args:
            target_audience: Description of target audience
            industry: Optional industry context

        Returns:
            Dict with audience insights
        """
        context = f" in {industry}" if industry else ""
        prompt = f"""Research insights about this target audience: {target_audience}{context}

Investigate:
1. Demographics and firmographics
2. Pain points and challenges
3. Goals and aspirations
4. Content consumption habits
5. Decision-making process
6. Preferred channels and platforms

Provide detailed audience profile."""

        result = self.run(prompt)
        return result


def create_research_agent() -> ResearchAgent:
    """Factory function to create Research Agent"""
    return ResearchAgent()
