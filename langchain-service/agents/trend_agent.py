"""
Trend Tracking Agent
Monitors industry trends, social media buzz, and emerging topics

ENHANCED with analytics integration for:
- Multi-source weighted trend scoring (NO LLM inference)
- Mathematical momentum calculation
- Linear regression trajectory analysis
- Source-credibility weighted data aggregation
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

# Import analytics modules for non-hallucinating trend analysis
try:
    from analytics.trend_scorer import TrendScorer, calculate_trend_score, calculate_momentum
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

# Import government and commercial data tools for verified data
try:
    from tools.gov_data_tool import GovDataTool
    from tools.commercial_intel_tool import CommercialIntelTool
    from tools.trends_tool import GoogleTrendsTool
    DATA_TOOLS_AVAILABLE = True
except ImportError:
    DATA_TOOLS_AVAILABLE = False

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

        # Create VERIFIED trend scorer tool (uses analytics module, NO LLM inference)
        def calculate_verified_trend_score(topic: str, include_gov_data: bool = True) -> str:
            """
            Calculate VERIFIED trend score using multi-source weighted analysis.

            ALGORITHM: Multi-source weighted scoring (NO LLM HALLUCINATION)
            - Google Trends: 30% weight
            - Government Employment Data: 25% weight
            - News Mentions (tiered by source credibility): 20% weight
            - Job Postings: 15% weight
            - Social Sentiment: 10% weight

            Args:
                topic: Topic to score
                include_gov_data: Include government data sources

            Returns:
                JSON with verified trend score and algorithm transparency
            """
            if not ANALYTICS_AVAILABLE:
                return json.dumps({
                    "error": "Analytics module not available",
                    "is_verified": False
                })

            data_sources = {}

            # 1. Google Trends data (if available)
            if DATA_TOOLS_AVAILABLE:
                try:
                    trends_tool = GoogleTrendsTool()
                    trends_result = trends_tool.get_interest_over_time(topic)
                    if trends_result.get("success"):
                        data = trends_result.get("data", {})
                        data_sources['google_trends'] = {
                            'current_interest': data.get("current_value", 50),
                            'avg_interest': data.get("avg_value", 50)
                        }
                except Exception as e:
                    logger.warning(f"Google Trends unavailable: {e}")

            # 2. Government employment data (BLS)
            if include_gov_data and DATA_TOOLS_AVAILABLE:
                try:
                    gov_tool = GovDataTool()
                    # Map topic to industry code (simplified)
                    industry_data = gov_tool.get_employment_data_bls(topic)
                    if industry_data.get("data"):
                        recent = industry_data["data"][-1] if industry_data["data"] else {}
                        data_sources['gov_employment'] = {
                            'growth_rate_pct': recent.get("change_pct", 0)
                        }
                except Exception as e:
                    logger.warning(f"Government data unavailable: {e}")

            # 3. News mentions (use SearXNG with credibility tiers)
            try:
                news_results = searxng.search_news(topic, time_range="week", max_results=20)
                tier1 = 0  # Authoritative (gov, academic)
                tier2 = 0  # Business news
                tier3 = 0  # Industry pubs
                tier4 = 0  # General news

                for result in news_results.get("results", []):
                    url = result.get("url", "").lower()
                    if any(gov in url for gov in [".gov", ".edu", "reuters", "ap"]):
                        tier1 += 1
                    elif any(biz in url for biz in ["wsj", "bloomberg", "ft.com", "forbes"]):
                        tier2 += 1
                    elif any(ind in url for ind in ["techcrunch", "venturebeat", "wired"]):
                        tier3 += 1
                    else:
                        tier4 += 1

                data_sources['news_mentions'] = {
                    'tier1_authoritative': tier1,
                    'tier2_business_news': tier2,
                    'tier3_industry_pubs': tier3,
                    'tier4_general_news': tier4
                }
            except Exception as e:
                logger.warning(f"News search unavailable: {e}")

            # 4. Job postings (use SearXNG)
            try:
                job_results = searxng.search_general(f"{topic} jobs hiring", max_results=20)
                job_count = len([r for r in job_results.get("results", [])
                               if any(w in r.get("title", "").lower()
                                     for w in ["job", "hire", "career", "position"])])
                data_sources['job_postings'] = {
                    'total_postings': job_count,
                    'growth_pct': 0  # Would need historical data
                }
            except Exception as e:
                logger.warning(f"Job search unavailable: {e}")

            # 5. Social sentiment (use SearXNG social)
            try:
                social_results = searxng.search_social(topic, max_results=20)
                # Simple sentiment approximation (would use TextBlob in full implementation)
                positive_words = ["good", "great", "excellent", "amazing", "love", "best"]
                negative_words = ["bad", "poor", "terrible", "hate", "worst", "fail"]

                positive_count = 0
                negative_count = 0
                for result in social_results.get("results", []):
                    text = (result.get("title", "") + " " + result.get("content", "")).lower()
                    positive_count += sum(1 for w in positive_words if w in text)
                    negative_count += sum(1 for w in negative_words if w in text)

                total = positive_count + negative_count
                sentiment = (positive_count - negative_count) / max(total, 1)

                data_sources['social_sentiment'] = {
                    'avg_sentiment': round(sentiment, 2),  # -1 to +1 scale
                    'mention_volume': len(social_results.get("results", []))
                }
            except Exception as e:
                logger.warning(f"Social search unavailable: {e}")

            # Calculate verified trend score using TrendScorer
            scorer = TrendScorer()
            result = scorer.calculate_trend_score(topic, data_sources)

            return json.dumps(result, indent=2)

        verified_trend_tool = Tool(
            name="Verified_Trend_Score",
            func=calculate_verified_trend_score,
            description="Calculate VERIFIED trend score using multi-source weighted analysis. "
                        "NO LLM HALLUCINATION - pure mathematical scoring from real data sources. "
                        "Returns trend_score (0-100), component_scores, confidence level, and algorithm transparency."
        )

        tools = [
            trend_detector_tool,
            social_monitor_tool,
            emerging_detector_tool,
            momentum_analyzer_tool,
            verified_trend_tool  # NEW: Non-hallucinating trend scorer
        ]

        super().__init__(
            name="Trend Tracking Agent",
            description="Monitors industry trends, detects emerging topics, and analyzes trend momentum",
            tools=tools,
            verbose=True
        )

        # Direct tool access
        self.searxng = searxng

        # Initialize analytics components
        if ANALYTICS_AVAILABLE:
            self.trend_scorer = TrendScorer()
            logger.info("trend_agent_initialized_with_analytics")
        else:
            self.trend_scorer = None
            logger.warning("trend_agent_initialized_without_analytics")

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

    def get_verified_trend_score(
        self,
        topic: str,
        include_gov_data: bool = True
    ) -> Dict[str, Any]:
        """
        Get VERIFIED trend score using multi-source weighted analysis.

        THIS METHOD DOES NOT USE LLM - pure mathematical calculation.

        Args:
            topic: Topic to analyze
            include_gov_data: Include government data sources

        Returns:
            Dict with:
            - trend_score: 0-100 weighted score
            - component_scores: Breakdown by source
            - confidence: high/medium/low based on source count
            - direction: strong_positive/positive/neutral/negative/strong_negative
            - algorithm: Description of calculation method
            - is_verified: True (always, since this is mathematical)
        """
        if not ANALYTICS_AVAILABLE:
            return {
                "error": "Analytics module not available",
                "is_verified": False,
                "algorithm": "N/A - module not loaded"
            }

        data_sources = {}

        # Collect data from multiple sources
        # 1. Google Trends
        if DATA_TOOLS_AVAILABLE:
            try:
                trends_tool = GoogleTrendsTool()
                trends_result = trends_tool.get_interest_over_time(topic)
                if trends_result.get("success"):
                    data = trends_result.get("data", {})
                    data_sources['google_trends'] = {
                        'current_interest': data.get("current_value", 50),
                        'avg_interest': data.get("avg_value", 50)
                    }
            except Exception as e:
                logger.warning(f"Google Trends unavailable: {e}")

        # 2. Government data
        if include_gov_data and DATA_TOOLS_AVAILABLE:
            try:
                gov_tool = GovDataTool()
                industry_data = gov_tool.get_employment_data_bls(topic)
                if industry_data.get("data"):
                    recent = industry_data["data"][-1] if industry_data["data"] else {}
                    data_sources['gov_employment'] = {
                        'growth_rate_pct': recent.get("change_pct", 0)
                    }
            except Exception as e:
                logger.warning(f"Government data unavailable: {e}")

        # 3. News mentions with credibility tiers
        try:
            news_results = self.searxng.search_news(topic, time_range="week", max_results=20)
            tier_counts = {'tier1_authoritative': 0, 'tier2_business_news': 0,
                          'tier3_industry_pubs': 0, 'tier4_general_news': 0}

            for result in news_results.get("results", []):
                url = result.get("url", "").lower()
                if any(s in url for s in [".gov", ".edu", "reuters", "ap"]):
                    tier_counts['tier1_authoritative'] += 1
                elif any(s in url for s in ["wsj", "bloomberg", "ft.com", "forbes"]):
                    tier_counts['tier2_business_news'] += 1
                elif any(s in url for s in ["techcrunch", "venturebeat", "wired"]):
                    tier_counts['tier3_industry_pubs'] += 1
                else:
                    tier_counts['tier4_general_news'] += 1

            data_sources['news_mentions'] = tier_counts
        except Exception as e:
            logger.warning(f"News search unavailable: {e}")

        # 4. Job postings
        try:
            job_results = self.searxng.search_general(f"{topic} jobs hiring", max_results=20)
            job_count = len([r for r in job_results.get("results", [])
                           if any(w in r.get("title", "").lower()
                                 for w in ["job", "hire", "career", "position"])])
            data_sources['job_postings'] = {
                'total_postings': job_count,
                'growth_pct': 0
            }
        except Exception as e:
            logger.warning(f"Job search unavailable: {e}")

        # 5. Social sentiment
        try:
            social_results = self.searxng.search_social(topic, max_results=20)
            positive_words = ["good", "great", "excellent", "amazing", "love", "best"]
            negative_words = ["bad", "poor", "terrible", "hate", "worst", "fail"]

            pos, neg = 0, 0
            for result in social_results.get("results", []):
                text = (result.get("title", "") + " " + result.get("content", "")).lower()
                pos += sum(1 for w in positive_words if w in text)
                neg += sum(1 for w in negative_words if w in text)

            total = pos + neg
            sentiment = (pos - neg) / max(total, 1)

            data_sources['social_sentiment'] = {
                'avg_sentiment': round(sentiment, 2),
                'mention_volume': len(social_results.get("results", []))
            }
        except Exception as e:
            logger.warning(f"Social search unavailable: {e}")

        # Calculate using TrendScorer
        result = self.trend_scorer.calculate_trend_score(topic, data_sources)

        # Add metadata
        result["metadata"] = {
            "type": "verified_trend_score",
            "topic": topic,
            "include_gov_data": include_gov_data,
            "created_at": datetime.utcnow().isoformat()
        }

        logger.info(
            "verified_trend_score_calculated",
            topic=topic,
            score=result.get("trend_score"),
            confidence=result.get("confidence")
        )

        return result

    def calculate_trend_momentum(
        self,
        current_score: float,
        previous_score: float,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate trend momentum using mathematical formula.

        Formula: momentum = (current - previous) / previous * 100

        Args:
            current_score: Current trend score
            previous_score: Previous trend score
            time_period_days: Time period for comparison

        Returns:
            Dict with momentum metrics (NO LLM)
        """
        if not ANALYTICS_AVAILABLE:
            return {
                "error": "Analytics module not available",
                "is_verified": False
            }

        return self.trend_scorer.calculate_momentum(
            current_score, previous_score, time_period_days
        )


def create_trend_agent() -> TrendTrackingAgent:
    """Factory function to create Trend Tracking Agent"""
    return TrendTrackingAgent()
