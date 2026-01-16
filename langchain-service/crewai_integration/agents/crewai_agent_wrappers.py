"""
CrewAI Agent Wrappers

Wraps existing LangChain agents as CrewAI-compatible agents with defined roles,
goals, and backstories.
"""

from typing import Optional, List
import structlog

logger = structlog.get_logger()

# Track if crewai is available
CREWAI_AVAILABLE = False
try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except ImportError:
    logger.warning("crewai_not_installed")


def _get_llm():
    """Get LLM for CrewAI agents."""
    from llm_providers import get_provider
    return get_provider()


def create_research_specialist(
    verbose: bool = True,
    allow_delegation: bool = False
):
    """
    Create a Research Specialist agent.

    Role: Deep research on topics using multiple data sources
    Capabilities:
    - Web search via SearXNG
    - Government data (SEC, BLS, Census)
    - Trend analysis
    - Source verification

    Returns:
        CrewAI Agent
    """
    if not CREWAI_AVAILABLE:
        raise RuntimeError("CrewAI not installed. Run: pip install crewai")

    return Agent(
        role="Research Specialist",
        goal="Conduct thorough, verified research using authoritative sources. "
             "Prioritize government data (SEC, BLS) for regulated industries "
             "and commercial intelligence for niche markets.",
        backstory="""You are a senior market researcher with 15 years of experience
        in B2B industries. You've worked at top consulting firms and specialize in
        finding verified, authoritative data. You never cite unverified sources
        and always indicate confidence levels. Your research has helped companies
        make multi-million dollar decisions.""",
        verbose=verbose,
        allow_delegation=allow_delegation,
        llm=_get_llm()
    )


def create_content_creator(
    verbose: bool = True,
    allow_delegation: bool = False
):
    """
    Create a Content Creator agent.

    Role: Generate marketing content optimized for engagement
    Capabilities:
    - Blog posts with SEO optimization
    - LinkedIn posts for B2B
    - Email campaigns
    - Social media content

    Returns:
        CrewAI Agent
    """
    if not CREWAI_AVAILABLE:
        raise RuntimeError("CrewAI not installed. Run: pip install crewai")

    # Try to use content-specific LLM (LLa-Marketing if available)
    try:
        from llm_providers import get_content_llm
        llm = get_content_llm()
    except Exception:
        llm = _get_llm()

    return Agent(
        role="Content Creator",
        goal="Create compelling, human-sounding marketing content that drives "
             "engagement. Avoid corporate jargon and AI-sounding phrases. "
             "Optimize for B2B executive audiences.",
        backstory="""You are an award-winning B2B marketing copywriter who has
        written for Fortune 500 companies. Your content consistently achieves
        3x industry average engagement rates. You have a gift for making complex
        topics accessible and engaging. You avoid buzzwords and write with
        authenticity that readers trust.""",
        verbose=verbose,
        allow_delegation=allow_delegation,
        llm=llm
    )


def create_trend_analyst(
    verbose: bool = True,
    allow_delegation: bool = False
):
    """
    Create a Trend Analyst agent.

    Role: Identify and analyze emerging trends
    Capabilities:
    - Google Trends analysis
    - Industry publication monitoring
    - Social media sentiment
    - Competitive intelligence

    Returns:
        CrewAI Agent
    """
    if not CREWAI_AVAILABLE:
        raise RuntimeError("CrewAI not installed. Run: pip install crewai")

    return Agent(
        role="Trend Analyst",
        goal="Identify emerging trends before they become mainstream. "
             "Analyze momentum, predict timing windows, and assess market impact.",
        backstory="""You are a strategic foresight analyst who has predicted major
        industry shifts for leading tech companies. You combine data from multiple
        sources - search trends, social signals, and industry publications - to
        identify patterns others miss. Your trend reports have helped companies
        time their market entries perfectly.""",
        verbose=verbose,
        allow_delegation=allow_delegation,
        llm=_get_llm()
    )


def create_market_analyst(
    verbose: bool = True,
    allow_delegation: bool = False
):
    """
    Create a Market Analyst agent.

    Role: Analyze market opportunities and buyer personas
    Capabilities:
    - TAM/SAM/SOM calculations
    - Buyer persona development
    - Competitive positioning
    - Market segmentation

    Returns:
        CrewAI Agent
    """
    if not CREWAI_AVAILABLE:
        raise RuntimeError("CrewAI not installed. Run: pip install crewai")

    return Agent(
        role="Market Analyst",
        goal="Analyze market opportunities with data-driven precision. "
             "Create actionable buyer personas and competitive positioning strategies.",
        backstory="""You are a market strategist who has sized markets and developed
        go-to-market strategies for Series A to IPO companies. You excel at finding
        underserved segments and quantifying opportunities. Your TAM analyses have
        helped companies raise hundreds of millions in funding. You always back
        your insights with verifiable data.""",
        verbose=verbose,
        allow_delegation=allow_delegation,
        llm=_get_llm()
    )


def create_seo_specialist(
    verbose: bool = True,
    allow_delegation: bool = False
):
    """
    Create an SEO Specialist agent.

    Role: Optimize content for search engines
    Capabilities:
    - Keyword optimization
    - Content structure analysis
    - Meta tag generation
    - Readability scoring

    Returns:
        CrewAI Agent
    """
    if not CREWAI_AVAILABLE:
        raise RuntimeError("CrewAI not installed. Run: pip install crewai")

    return Agent(
        role="SEO Specialist",
        goal="Optimize content for search visibility while maintaining natural, "
             "engaging writing. Balance SEO best practices with user experience.",
        backstory="""You are an SEO strategist who has achieved top 3 rankings for
        competitive B2B keywords. You understand both technical SEO and content
        optimization. Unlike many SEO practitioners, you prioritize readability
        and user intent alongside search optimization. Your content ranks well
        AND converts because you never sacrifice quality for keywords.""",
        verbose=verbose,
        allow_delegation=allow_delegation,
        llm=_get_llm()
    )


def create_all_agents(verbose: bool = True) -> dict:
    """
    Create all CrewAI agents.

    Returns:
        Dict of agent name -> agent instance
    """
    return {
        'research_specialist': create_research_specialist(verbose),
        'content_creator': create_content_creator(verbose),
        'trend_analyst': create_trend_analyst(verbose),
        'market_analyst': create_market_analyst(verbose),
        'seo_specialist': create_seo_specialist(verbose)
    }
