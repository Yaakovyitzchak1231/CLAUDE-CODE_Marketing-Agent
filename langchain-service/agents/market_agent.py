"""
Market Analysis Agent
Analyzes target markets, audience segments, and provides market intelligence
"""

from typing import List, Dict, Any, Optional
from langchain.tools import Tool
from .base_agent import BaseAgent
from tools.search_tool import SearXNGTool, create_searxng_langchain_tool
from memory.vector_store import get_vector_store
import structlog
from datetime import datetime
import json


logger = structlog.get_logger()


class MarketAnalysisAgent(BaseAgent):
    """
    Specialist agent for market analysis and audience intelligence

    Capabilities:
    - Market sizing and opportunity assessment
    - Audience segmentation and profiling
    - Buyer persona development
    - Market trend identification
    - Industry vertical analysis
    - TAM/SAM/SOM calculation
    """

    def __init__(self):
        """Initialize Market Analysis Agent"""

        # Initialize search tool
        search_tool = create_searxng_langchain_tool()

        # Initialize vector store for market data
        vector_store = get_vector_store()

        # Create market research tool
        def market_research(query: str) -> str:
            """Research market data across multiple categories"""
            searxng = SearXNGTool()

            # Multi-category search for comprehensive market view
            results = searxng.multi_category_search(
                query=query,
                categories=["general", "news", "science"]
            )

            formatted = []

            for category, items in results.items():
                if items:
                    formatted.append(f"=== {category.title()} ===")
                    for i, result in enumerate(items[:3], 1):
                        formatted.append(
                            f"{i}. {result['title']}\n"
                            f"   {result['content'][:200]}...\n"
                            f"   Source: {result['url']}\n"
                        )
                    formatted.append("")

            return "\n".join(formatted) if formatted else "No market data found."

        market_research_tool = Tool(
            name="Market_Research",
            func=market_research,
            description="Research market data, industry reports, and market trends. "
                        "Searches across general web, news, and academic sources. "
                        "Input should be a market or industry to research."
        )

        # Create audience analysis tool
        def analyze_audience(audience_description: str) -> str:
            """Analyze audience characteristics and behaviors"""

            # Search for audience insights
            searxng = SearXNGTool()
            results = searxng.search_general(
                f"{audience_description} demographics behavior preferences",
                max_results=5
            )

            # Also search vector store for similar audience segments
            similar_segments = vector_store.find_relevant_segments(
                audience_description,
                n_results=3
            )

            formatted = ["=== Web Research ==="]
            for i, result in enumerate(results, 1):
                formatted.append(
                    f"{i}. {result['title']}\n"
                    f"   {result['content'][:150]}...\n"
                )

            if similar_segments:
                formatted.append("\n=== Similar Audience Segments (Historical) ===")
                for i, segment in enumerate(similar_segments, 1):
                    metadata = segment.get('metadata', {})
                    formatted.append(
                        f"{i}. {segment['document'][:200]}...\n"
                        f"   Industry: {metadata.get('industry', 'N/A')}\n"
                        f"   Relevance: {1 - segment['distance']:.2f}\n"
                    )

            return "\n".join(formatted)

        audience_tool = Tool(
            name="Audience_Analyzer",
            func=analyze_audience,
            description="Analyze target audience characteristics, demographics, and behaviors. "
                        "Searches web and historical data for audience insights. "
                        "Input should be audience description (e.g., 'B2B SaaS CTOs')."
        )

        # Create market sizing tool
        def estimate_market_size(market_description: str) -> str:
            """Estimate market size using research"""
            prompt = f"""Estimate the market size for: {market_description}

Research and calculate:
1. TAM (Total Addressable Market) - Total market demand
2. SAM (Serviceable Addressable Market) - Segment you can serve
3. SOM (Serviceable Obtainable Market) - Realistic short-term target

For each, provide:
- Size estimate (revenue or units)
- Calculation methodology
- Data sources
- Growth rate (CAGR)
- Key assumptions

Use bottom-up and top-down approaches where possible."""
            return prompt  # In real implementation, this would call LLM

        sizing_tool = Tool(
            name="Market_Sizer",
            func=estimate_market_size,
            description="Estimate market size (TAM/SAM/SOM) for a given market. "
                        "Input should be market or industry description."
        )

        # Create segmentation tool
        def segment_market(criteria: str) -> str:
            """Segment market based on criteria"""
            prompt = f"""Segment the market based on: {criteria}

Create market segments considering:
1. Firmographic Segmentation (size, industry, location)
2. Behavioral Segmentation (usage, needs, pain points)
3. Psychographic Segmentation (values, attitudes)
4. Technographic Segmentation (tech stack, maturity)

For each segment, provide:
- Segment Name & Description
- Size & Growth Potential
- Key Characteristics
- Pain Points & Needs
- Marketing Channels
- Purchase Behavior

Prioritize high-value segments."""
            return prompt  # In real implementation, this would call LLM

        segmentation_tool = Tool(
            name="Market_Segmentation",
            func=segment_market,
            description="Segment market based on specified criteria. "
                        "Input should be segmentation criteria or market description."
        )

        tools = [
            market_research_tool,
            audience_tool,
            sizing_tool,
            segmentation_tool
        ]

        super().__init__(
            name="Market Analysis Agent",
            description="Analyzes target markets, segments audiences, and provides market intelligence",
            tools=tools,
            verbose=True
        )

        logger.info("market_analysis_agent_initialized")

    def get_specialized_prompt(self) -> str:
        """Get Market Analysis Agent system prompt"""
        return """You are a Market Analysis Agent specializing in B2B market research and audience intelligence.

Your primary responsibilities:
1. Analyze market opportunities and size
2. Segment audiences and create buyer personas
3. Identify market trends and dynamics
4. Assess competitive landscape positioning
5. Provide data-driven market insights

Analysis Framework:
- Use both quantitative and qualitative data
- Apply multiple segmentation approaches
- Consider market maturity and growth
- Identify early adopters and laggards
- Assess market entry barriers

Market Research Best Practices:
- Validate data from multiple sources
- Use primary and secondary research
- Consider geographic variations
- Track regulatory and policy changes
- Monitor technology adoption curves
- Analyze economic indicators

Audience Analysis Best Practices:
- Build detailed buyer personas
- Map customer journeys
- Identify decision-making units (DMU)
- Understand buying processes
- Track engagement patterns

Output Format:
Structure your analysis with:
- Executive Summary
- Market Overview (size, growth, trends)
- Segmentation Analysis (key segments, characteristics)
- Buyer Personas (detailed profiles)
- Market Opportunities (gaps, trends, timing)
- Risks & Challenges
- Strategic Recommendations
- Data Sources & Methodology

Be specific, quantitative where possible, and actionable."""

    def analyze_market_opportunity(
        self,
        market_description: str,
        geography: Optional[str] = None,
        store_results: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive market opportunity analysis

        Args:
            market_description: Description of target market
            geography: Geographic focus (optional)
            store_results: Whether to store in vector DB

        Returns:
            Dict with market analysis
        """
        geo_context = f" in {geography}" if geography else ""

        prompt = f"""Conduct a comprehensive market opportunity analysis for: {market_description}{geo_context}

Analyze:
1. Market Overview
   - Current market size (TAM)
   - Market growth rate (CAGR)
   - Market maturity stage
   - Key market drivers

2. Market Dynamics
   - Supply and demand factors
   - Pricing trends
   - Distribution channels
   - Value chain analysis

3. Customer Landscape
   - Total potential customers
   - Customer segments
   - Buying patterns
   - Decision criteria

4. Competitive Intensity
   - Number of players
   - Market concentration
   - Barriers to entry
   - Competitive advantages

5. Market Trends
   - Emerging trends
   - Technology impact
   - Regulatory changes
   - Economic factors

6. Opportunity Assessment
   - Market gaps
   - Unmet needs
   - Growth opportunities
   - Entry strategy

Provide specific data points and sources."""

        result = self.run(prompt)

        # Store in vector database
        if store_results and result.get("output"):
            vector_store = get_vector_store()
            vector_store.add_market_segment(
                segment_id=f"market_{datetime.utcnow().timestamp()}",
                description=result["output"],
                metadata={
                    "type": "market_opportunity",
                    "market": market_description,
                    "geography": geography or "global",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            logger.info(
                "market_opportunity_stored",
                market=market_description
            )

        return result

    def create_buyer_personas(
        self,
        target_audience: str,
        industry: Optional[str] = None,
        count: int = 3
    ) -> Dict[str, Any]:
        """
        Create detailed buyer personas

        Args:
            target_audience: Target audience description
            industry: Industry context
            count: Number of personas to create

        Returns:
            Dict with buyer personas
        """
        industry_context = f" in {industry}" if industry else ""

        prompt = f"""Create {count} detailed buyer personas for: {target_audience}{industry_context}

For each persona, provide:

1. Persona Overview
   - Name & Title
   - Company Size & Type
   - Industry Vertical
   - Reporting Structure

2. Demographics & Firmographics
   - Age range
   - Education level
   - Years of experience
   - Company revenue range
   - Number of employees

3. Goals & Objectives
   - Primary goals (3-5)
   - Success metrics
   - Career aspirations
   - Business objectives

4. Challenges & Pain Points
   - Top challenges (5-7)
   - Daily frustrations
   - Resource constraints
   - Technical limitations

5. Decision-Making
   - Role in buying process
   - Decision criteria
   - Budget authority
   - Approval process
   - Typical buying timeline

6. Information Sources
   - Preferred content types
   - Trusted publications
   - Social media platforms
   - Industry events
   - Peer networks

7. Technology & Tools
   - Current tech stack
   - Tool preferences
   - Technical proficiency
   - Integration requirements

8. Communication Preferences
   - Preferred channels
   - Communication style
   - Meeting preferences
   - Response expectations

9. Objections & Concerns
   - Common objections
   - Risk factors
   - Competitive preferences
   - Price sensitivity

10. Messaging Guidance
    - Key value propositions
    - Messaging dos and don'ts
    - Tone and language
    - Proof points needed

Make personas realistic and distinct."""

        result = self.run(prompt)

        # Store personas
        if result.get("output"):
            vector_store = get_vector_store()
            vector_store.add_market_segment(
                segment_id=f"personas_{datetime.utcnow().timestamp()}",
                description=result["output"],
                metadata={
                    "type": "buyer_personas",
                    "audience": target_audience,
                    "industry": industry or "general",
                    "count": count,
                    "created_at": datetime.utcnow().isoformat()
                }
            )

        return result

    def segment_audience(
        self,
        market: str,
        segmentation_type: str = "firmographic",
        criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Segment audience by specified criteria

        Args:
            market: Market or industry to segment
            segmentation_type: Type of segmentation (firmographic, behavioral, psychographic, technographic)
            criteria: Additional segmentation criteria

        Returns:
            Dict with audience segments
        """
        criteria_str = json.dumps(criteria, indent=2) if criteria else "default criteria"

        prompt = f"""Segment the {market} market using {segmentation_type} segmentation.

Criteria: {criteria_str}

Create 4-6 distinct segments with:

1. Segment Profile
   - Segment name
   - Size estimate
   - Growth potential (High/Medium/Low)
   - Accessibility (Easy/Medium/Hard)

2. Characteristics
   - Defining attributes
   - Common traits
   - Differentiating factors

3. Needs & Preferences
   - Primary needs
   - Secondary needs
   - Purchase preferences
   - Value drivers

4. Behavior Patterns
   - Buying behavior
   - Usage patterns
   - Brand loyalty
   - Price sensitivity

5. Marketing Approach
   - Recommended channels
   - Message positioning
   - Content preferences
   - Engagement tactics

6. Opportunity Assessment
   - Market potential
   - Competitive intensity
   - Barriers to entry
   - Priority ranking (1-5)

Prioritize segments by attractiveness and fit."""

        result = self.run(prompt)

        # Store segmentation
        if result.get("output"):
            vector_store = get_vector_store()
            vector_store.add_market_segment(
                segment_id=f"segmentation_{datetime.utcnow().timestamp()}",
                description=result["output"],
                metadata={
                    "type": "audience_segmentation",
                    "market": market,
                    "segmentation_type": segmentation_type,
                    "criteria": criteria,
                    "created_at": datetime.utcnow().isoformat()
                }
            )

        return result

    def analyze_market_trends(
        self,
        industry: str,
        timeframe: str = "12 months"
    ) -> Dict[str, Any]:
        """
        Analyze market trends and forecast

        Args:
            industry: Industry to analyze
            timeframe: Time horizon for trends

        Returns:
            Dict with trend analysis
        """
        prompt = f"""Analyze market trends in {industry} over the next {timeframe}.

Research and analyze:

1. Current State
   - Market overview
   - Key players
   - Recent developments

2. Emerging Trends
   - Technology trends
   - Business model innovations
   - Consumer behavior shifts
   - Regulatory changes

3. Growth Drivers
   - Positive factors
   - Market catalysts
   - Adoption accelerators

4. Headwinds & Challenges
   - Market obstacles
   - Regulatory risks
   - Economic factors
   - Competitive threats

5. Technology Impact
   - AI/ML adoption
   - Automation trends
   - Platform shifts
   - Integration requirements

6. Market Forecast
   - Growth projections
   - Market size estimates
   - Segment evolution
   - Competitive landscape changes

7. Strategic Implications
   - Opportunities to capitalize
   - Risks to mitigate
   - Timing considerations
   - Investment priorities

Provide specific examples and data points."""

        result = self.run(prompt)

        # Store trend analysis
        if result.get("output"):
            vector_store = get_vector_store()
            vector_store.add_market_segment(
                segment_id=f"trends_{datetime.utcnow().timestamp()}",
                description=result["output"],
                metadata={
                    "type": "market_trends",
                    "industry": industry,
                    "timeframe": timeframe,
                    "created_at": datetime.utcnow().isoformat()
                }
            )

        return result

    def calculate_tam_sam_som(
        self,
        product_description: str,
        geography: str = "global"
    ) -> Dict[str, Any]:
        """
        Calculate TAM, SAM, and SOM

        Args:
            product_description: Product/service description
            geography: Geographic market

        Returns:
            Dict with market size calculations
        """
        prompt = f"""Calculate TAM, SAM, and SOM for: {product_description} in {geography}

Provide detailed calculations:

1. TAM (Total Addressable Market)
   - Definition: Total market demand
   - Calculation method: [Top-down or Bottom-up]
   - Market size: $XXX [Million/Billion]
   - Data sources
   - Key assumptions
   - Growth rate (CAGR): XX%

2. SAM (Serviceable Addressable Market)
   - Definition: Segment you can serve
   - Target segment criteria
   - Calculation method
   - Market size: $XXX [Million/Billion]
   - % of TAM: XX%
   - Constraints considered
   - Growth rate: XX%

3. SOM (Serviceable Obtainable Market)
   - Definition: Realistic market share (1-3 years)
   - Market penetration estimate: XX%
   - Calculation method
   - Market size: $XXX [Million/Billion]
   - % of SAM: XX%
   - Competitive factors
   - Time to achieve: XX months

4. Methodology
   - Data sources used
   - Assumptions made
   - Confidence level
   - Alternative scenarios

5. Market Dynamics
   - Growth drivers
   - Market maturity
   - Competitive intensity
   - Regulatory factors

Show all calculations with formulas."""

        result = self.run(prompt)
        return result


def create_market_agent() -> MarketAnalysisAgent:
    """Factory function to create Market Analysis Agent"""
    return MarketAnalysisAgent()
