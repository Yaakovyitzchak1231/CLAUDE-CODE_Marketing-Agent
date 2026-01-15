"""
Marketing Agent Tools

This module provides tools for:
- Government data access (BLS, Census, SEC, FDA)
- Commercial intelligence (industry publications, press releases)
- Market trends (Google Trends)
- Media generation (DALL-E, Midjourney, video tools)
- Web scraping and search
"""

from .gov_data_tool import (
    GovDataTool,
    gov_data,
    get_industry_trends,
    get_market_data,
    research_b2b_industry
)

from .commercial_intel_tool import (
    CommercialIntelTool,
    commercial_intel,
    search_commercial_news,
    research_commercial_market
)

from .trends_tool import (
    TrendsTool,
    trends_tool,
    get_keyword_trends,
    find_emerging_trends,
    compare_market_interest
)

from .search_tool import SearchTool
from .scraping_tool import ScrapingTool
from .dalle_tool import DalleTool
from .midjourney_tool import MidjourneyTool
from .runway_tool import RunwayTool
from .pika_tool import PikaTool
from .ffmpeg_tool import FFmpegTool
from .huggingface_models import HuggingFaceModels

__all__ = [
    # Government Data
    'GovDataTool',
    'gov_data',
    'get_industry_trends',
    'get_market_data',
    'research_b2b_industry',

    # Commercial Intelligence
    'CommercialIntelTool',
    'commercial_intel',
    'search_commercial_news',
    'research_commercial_market',

    # Trends
    'TrendsTool',
    'trends_tool',
    'get_keyword_trends',
    'find_emerging_trends',
    'compare_market_interest',

    # Search & Scraping
    'SearchTool',
    'ScrapingTool',

    # Media Generation
    'DalleTool',
    'MidjourneyTool',
    'RunwayTool',
    'PikaTool',
    'FFmpegTool',
    'HuggingFaceModels',
]
