"""
Trend Tracking Agent
Monitors industry trends, social media buzz, and emerging topics
"""

from typing import Dict, List, Optional, Any
from langchain.tools import Tool
from .base_agent import BaseAgent
from tools.search_tool import SearXNGTool
import structlog
from datetime import datetime, timedelta
import json
import re
from collections import Counter

logger = structlog.get_logger()


class TrendTrackingAgent(BaseAgent):
    """
    Specialist agent for trend detection and monitoring

    Capabilities:
    - Industry trend monitoring
    - Social media trend detection
    - Emerging topic identification
    - Time-series analysis
    - Trend forecasting
    - Reddit/HackerNews tracking
    - Viral content detection
    """

    def __init__(self):
        """Initialize Trend Tracking Agent"""

        # Initialize tools
        searxng = SearXNGTool()

        # Create trend detection tool
        def detect_trends(query: str, time_range: str = "week") -> str:
            """
            Detect trending topics related to query

            Args:
                query: Topic or industry to monitor
                time_range: Time range (day, week, month)

            Returns:
                JSON string with trending topics
            """
            # Search recent news and social media
            news_results = searxng.search_news(query, time_range=time_range, max_results=20)
            social_results = searxng.search_social(query, max_results=20)
            general_results = searxng.search_general(f"{query} trends {time_range}", max_results=15)

            # Extract keywords from titles
            all_titles = []

            for result in news_results.get("results", []):
                all_titles.append(result.get("title", ""))

            for result in social_results.get("results", []):
                all_titles.append(result.get("title", ""))

            for result in general_results.get("results", []):
                all_titles.append(result.get("title", ""))

            # Extract keywords (simple approach)
            keywords = []
            for title in all_titles:
                # Remove common words and extract potential keywords
                words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', title)
                keywords.extend(words)

            # Count keyword frequency
            keyword_counts = Counter(keywords)
            top_keywords = keyword_counts.most_common(15)

            trends = {
                "query": query,
                "time_range": time_range,
                "trending_topics": [
                    {"keyword": kw, "mentions": count}
                    for kw, count in top_keywords
                ],
                "news_count": len(news_results.get("results", [])),
                "social_count": len(social_results.get("results", [])),
                "sources": {
                    "news": news_results.get("results", [])[:5],
                    "social": social_results.get("results", [])[:5]
                }
            }

            return json.dumps(trends, indent=2)

        trend_detector_tool = Tool(
            name="Trend_Detector",
            func=detect_trends,
            description="Detect trending topics and keywords in a specific industry or topic area. "
                        "Input should be topic and time range (day, week, month)."
        )

        # Create social media monitor tool
        def monitor_social_media(topic: str, platforms: str = "all") -> str:
            """
            Monitor social media for topic mentions

            Args:
                topic: Topic to monitor
                platforms: Platforms to check (reddit, twitter, hackernews, all)

            Returns:
                JSON string with social media insights
            """
            social_results = searxng.search_social(topic, max_results=30)

            # Group by platform (inferred from URL)
            platform_groups = {
                "reddit": [],
                "twitter": [],
                "hackernews": [],
                "other": []
            }

            for result in social_results.get("results", []):
                url = result.get("url", "").lower()

                if "reddit.com" in url:
                    platform_groups["reddit"].append(result)
                elif "twitter.com" in url or "x.com" in url:
                    platform_groups["twitter"].append(result)
                elif "news.ycombinator.com" in url:
                    platform_groups["hackernews"].append(result)
                else:
                    platform_groups["other"].append(result)

            insights = {
                "topic": topic,
                "total_mentions": len(social_results.get("results", [])),
                "by_platform": {
                    platform: {
                        "count": len(results),
                        "top_posts": [
                            {
                                "title": r.get("title", ""),
                                "url": r.get("url", ""),
                                "snippet": r.get("content", "")[:200]
                            }
                            for r in results[:3]
                        ]
                    }
                    for platform, results in platform_groups.items()
                    if len(results) > 0
                }
            }

            return json.dumps(insights, indent=2)

        social_monitor_tool = Tool(
            name="Social_Media_Monitor",
            func=monitor_social_media,
            description="Monitor social media platforms (Reddit, Twitter, HackerNews) for topic mentions. "
                        "Input should be topic name."
        )

        # Create emerging topic detector
        def detect_emerging_topics(industry: str, threshold: int = 5) -> str:
            """
            Detect rapidly growing topics

            Args:
                industry: Industry or vertical to monitor
                threshold: Minimum mention threshold

            Returns:
                JSON string with emerging topics
            """
            # Search recent content (last week)
            recent_results = searxng.search_news(industry, time_range="week", max_results=30)

            # Extract potential emerging topics
            topics = {}

            for result in recent_results.get("results", []):
                title = result.get("title", "")

                # Extract capitalized phrases (potential topics)
                phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b', title)

                for phrase in phrases:
                    if len(phrase) > 3:  # Filter very short phrases
                        topics[phrase] = topics.get(phrase, 0) + 1

            # Filter by threshold
            emerging = [
                {"topic": topic, "mentions": count}
                for topic, count in topics.items()
                if count >= threshold
            ]

            # Sort by mentions
            emerging.sort(key=lambda x: x["mentions"], reverse=True)

            result = {
                "industry": industry,
                "threshold": threshold,
                "emerging_topics": emerging[:10],
                "total_topics_found": len(emerging)
            }

            return json.dumps(result, indent=2)

        emerging_detector_tool = Tool(
            name="Emerging_Topic_Detector",
            func=detect_emerging_topics,
            description="Detect rapidly growing and emerging topics in an industry. "
                        "Input should be industry name and mention threshold."
        )

        # Create time-series analyzer tool
        def analyze_trend_momentum(topic: str) -> str:
            """
            Analyze trend momentum over time

            Args:
                topic: Topic to analyze

            Returns:
                JSON string with momentum analysis
            """
            # Search across different time periods
            today_results = searxng.search_general(topic, max_results=10)
            week_results = searxng.search_news(topic, time_range="week", max_results=10)
            month_results = searxng.search_news(topic, time_range="month", max_results=10)

            # Calculate momentum
            today_count = len(today_results.get("results", []))
            week_count = len(week_results.get("results", []))
            month_count = len(month_results.get("results", []))

            # Simple momentum calculation
            if week_count > 0:
                weekly_momentum = (today_count * 7) / week_count
            else:
                weekly_momentum = 0

            if month_count > 0:
                monthly_momentum = (week_count * 4) / month_count
            else:
                monthly_momentum = 0

            # Determine trend direction
            if weekly_momentum > 1.5:
                trend_direction = "accelerating"
            elif weekly_momentum > 0.8:
                trend_direction = "steady"
            else:
                trend_direction = "declining"

            analysis = {
                "topic": topic,
                "mentions": {
                    "today": today_count,
                    "this_week": week_count,
                    "this_month": month_count
                },
                "momentum": {
                    "weekly": round(weekly_momentum, 2),
                    "monthly": round(monthly_momentum, 2),
                    "direction": trend_direction
                },
                "forecast": f"Based on current momentum, this topic is {trend_direction}."
            }

            return json.dumps(analysis, indent=2)

        momentum_analyzer_tool = Tool(
            name="Trend_Momentum_Analyzer",
            func=analyze_trend_momentum,
            description="Analyze trend momentum and growth trajectory. "
                        "Input should be topic name."
        )

        tools = [
            trend_detector_tool,
            social_monitor_tool,
            emerging_detector_tool,
            momentum_analyzer_tool
        ]

        super().__init__(
            name="Trend Tracking Agent",
            description="Monitors industry trends, detects emerging topics, and analyzes trend momentum",
            tools=tools,
            verbose=True
        )

        # Direct tool access
        self.searxng = searxng

        logger.info("trend_agent_initialized")

    def get_specialized_prompt(self) -> str:
        """Get Trend Tracking Agent system prompt"""
        return """You are a Trend Tracking Agent specializing in industry and social media trends.

Your primary responsibilities:
1. Monitor industry trends and emerging topics
2. Track social media buzz and viral content
3. Analyze trend momentum and growth
4. Forecast trend trajectories
5. Identify early-stage opportunities

Trend Analysis Best Practices:
- Use multiple data sources (news, social media, general web)
- Track trends over time (day, week, month)
- Look for acceleration patterns
- Identify emerging topics before they peak
- Consider both volume and velocity
- Distinguish between fads and lasting trends
- Cross-reference multiple platforms

Data Sources:
- News Articles: Mainstream trend validation
- Reddit: Early community adoption signals
- HackerNews: Tech industry trends
- Twitter/X: Real-time pulse
- Google Trends: Search interest over time

Trend Categories:
- Technology trends (AI, blockchain, cloud, etc.)
- Marketing trends (social media, content formats)
- Industry trends (B2B, SaaS, e-commerce)
- Consumer behavior trends
- Regulatory/policy trends

Momentum Indicators:
- Accelerating: >50% week-over-week growth
- Steady: Stable mention volume
- Declining: <20% week-over-week growth
- Emerging: New topic with rapid growth
- Mature: High volume but stable/declining

Time-Series Analysis:
- Compare current period vs. previous periods
- Calculate growth rates
- Identify inflection points
- Detect seasonality patterns
- Forecast future trajectory

Output Format:
Provide:
- Trending topics with mention counts
- Momentum analysis (accelerating/steady/declining)
- Platform-specific insights
- Emerging opportunities
- Forecast and recommendations
- Data sources and timeframes
- Confidence level in predictions

Be data-driven, forward-looking, and actionable."""

    def monitor_industry_trends(
        self,
        industry: str,
        time_range: str = "week",
        include_social: bool = True
    ) -> Dict[str, Any]:
        """
        Monitor trends in a specific industry

        Args:
            industry: Industry or vertical to monitor
            time_range: Time range (day, week, month)
            include_social: Include social media monitoring

        Returns:
            Dict with trend analysis
        """
        prompt = f"""Monitor trends in the {industry} industry.

Time Range: {time_range}
Include Social Media: {include_social}

Tasks:
1. Detect trending topics in {industry}
2. Identify emerging opportunities
3. Analyze trend momentum
{f"4. Monitor social media buzz" if include_social else ""}

Provide comprehensive trend analysis with actionable insights."""

        result = self.run(prompt)

        if result.get("output"):
            metadata = {
                "type": "industry_trends",
                "industry": industry,
                "time_range": time_range,
                "include_social": include_social,
                "created_at": datetime.utcnow().isoformat()
            }

            logger.info(
                "industry_trends_monitored",
                industry=industry,
                time_range=time_range
            )

            result["metadata"] = metadata

        return result

    def detect_emerging_opportunities(
        self,
        industry: str,
        threshold: int = 5
    ) -> Dict[str, Any]:
        """
        Detect early-stage emerging topics

        Args:
            industry: Industry to monitor
            threshold: Minimum mention threshold

        Returns:
            Dict with emerging topics
        """
        prompt = f"""Detect emerging opportunities in {industry}.

Mention Threshold: {threshold}

Tasks:
1. Identify rapidly growing topics
2. Analyze early-stage adoption signals
3. Assess opportunity potential
4. Provide actionable recommendations

Focus on topics that are emerging but not yet mainstream."""

        result = self.run(prompt)

        if result.get("output"):
            metadata = {
                "type": "emerging_opportunities",
                "industry": industry,
                "threshold": threshold,
                "created_at": datetime.utcnow().isoformat()
            }

            result["metadata"] = metadata

        return result

    def analyze_topic_momentum(
        self,
        topic: str,
        forecast_period: str = "1 month"
    ) -> Dict[str, Any]:
        """
        Analyze momentum and forecast trend

        Args:
            topic: Topic to analyze
            forecast_period: Forecast timeframe

        Returns:
            Dict with momentum analysis
        """
        prompt = f"""Analyze momentum for: {topic}

Forecast Period: {forecast_period}

Tasks:
1. Analyze current trend momentum
2. Compare recent vs. historical mentions
3. Determine trend direction
4. Forecast trend trajectory for {forecast_period}
5. Provide confidence level

Include specific metrics and data sources."""

        result = self.run(prompt)

        if result.get("output"):
            metadata = {
                "type": "momentum_analysis",
                "topic": topic,
                "forecast_period": forecast_period,
                "created_at": datetime.utcnow().isoformat()
            }

            result["metadata"] = metadata

        return result

    def track_social_buzz(
        self,
        topic: str,
        platforms: List[str] = ["reddit", "twitter", "hackernews"]
    ) -> Dict[str, Any]:
        """
        Track social media buzz for topic

        Args:
            topic: Topic to track
            platforms: List of platforms to monitor

        Returns:
            Dict with social media insights
        """
        platforms_str = ", ".join(platforms)

        prompt = f"""Track social media buzz for: {topic}

Platforms: {platforms_str}

Tasks:
1. Monitor mentions across platforms
2. Identify top discussions and threads
3. Analyze sentiment and engagement
4. Detect viral patterns
5. Compare platform-specific trends

Provide platform-by-platform breakdown with key insights."""

        result = self.run(prompt)

        if result.get("output"):
            metadata = {
                "type": "social_buzz",
                "topic": topic,
                "platforms": platforms,
                "created_at": datetime.utcnow().isoformat()
            }

            logger.info(
                "social_buzz_tracked",
                topic=topic,
                platforms=platforms
            )

            result["metadata"] = metadata

        return result

    def identify_content_opportunities(
        self,
        industry: str,
        content_type: str = "blog"
    ) -> Dict[str, Any]:
        """
        Identify trending content opportunities

        Args:
            industry: Industry vertical
            content_type: Content format (blog, video, social, infographic)

        Returns:
            Dict with content ideas based on trends
        """
        prompt = f"""Identify content opportunities in {industry}.

Content Type: {content_type}

Tasks:
1. Find trending topics suitable for {content_type}
2. Identify content gaps and opportunities
3. Analyze what's working (viral content patterns)
4. Provide specific content ideas with rationale
5. Include SEO keyword opportunities

Focus on actionable ideas with trend data support."""

        result = self.run(prompt)

        if result.get("output"):
            metadata = {
                "type": "content_opportunities",
                "industry": industry,
                "content_type": content_type,
                "created_at": datetime.utcnow().isoformat()
            }

            result["metadata"] = metadata

        return result

    def compare_trend_trajectory(
        self,
        topics: List[str],
        time_range: str = "month"
    ) -> Dict[str, Any]:
        """
        Compare multiple topics' trend trajectories

        Args:
            topics: List of topics to compare
            time_range: Time range for comparison

        Returns:
            Dict with comparative analysis
        """
        topics_str = ", ".join(topics)

        prompt = f"""Compare trend trajectories for: {topics_str}

Time Range: {time_range}

Tasks:
1. Analyze momentum for each topic
2. Compare growth rates
3. Identify the fastest-growing topic
4. Determine which topics are declining
5. Provide investment/focus recommendations

Include side-by-side comparison with data."""

        result = self.run(prompt)

        if result.get("output"):
            metadata = {
                "type": "comparative_trends",
                "topics": topics,
                "time_range": time_range,
                "created_at": datetime.utcnow().isoformat()
            }

            result["metadata"] = metadata

        return result


def create_trend_agent() -> TrendTrackingAgent:
    """Factory function to create Trend Tracking Agent"""
    return TrendTrackingAgent()
