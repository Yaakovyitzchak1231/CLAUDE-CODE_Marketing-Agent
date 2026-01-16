"""
CrewAI Agent Wrappers

Wraps existing LangChain agents for use with CrewAI.
"""

from .crewai_agent_wrappers import (
    create_research_specialist,
    create_content_creator,
    create_trend_analyst,
    create_market_analyst,
    create_seo_specialist
)

__all__ = [
    'create_research_specialist',
    'create_content_creator',
    'create_trend_analyst',
    'create_market_analyst',
    'create_seo_specialist'
]
