"""
CrewAI Crews

Pre-configured crews for different marketing tasks.
"""

from .content_crew import ContentCrew
from .campaign_crew import CampaignCrew
from .research_crew import ResearchCrew

__all__ = [
    'ContentCrew',
    'CampaignCrew',
    'ResearchCrew'
]
