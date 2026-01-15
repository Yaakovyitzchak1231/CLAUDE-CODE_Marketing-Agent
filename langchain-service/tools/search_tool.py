"""
SearXNG Search Tool for LangChain Agents
Provides interface to self-hosted meta-search engine
"""

import requests
from typing import List, Dict, Optional, Any
import json
from urllib.parse import quote_plus


class SearXNGTool:
    """
    Wrapper for SearXNG meta-search engine
    Supports multiple search categories and result filtering
    """

    def __init__(
        self,
        base_url: str = "http://searxng:8080",
        timeout: int = 30,
        max_results: int = 10
    ):
        """
        Initialize SearXNG tool

        Args:
            base_url: SearXNG instance URL
            timeout: Request timeout in seconds
            max_results: Maximum number of results to return
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_results = max_results

    def search(
        self,
        query: str,
        category: str = "general",
        engines: Optional[List[str]] = None,
        language: str = "en",
        time_range: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform search query

        Args:
            query: Search query string
            category: Search category (general, news, images, videos, social media, it, science)
            engines: Specific engines to use (e.g., ['google', 'duckduckgo'])
            language: Language code (default: 'en')
            time_range: Time range filter (day, week, month, year)
            max_results: Maximum number of results to return (overrides instance default)

        Returns:
            List of search results with title, url, content, and metadata
        """
        # Use parameter max_results if provided, else fall back to instance default
        result_limit = max_results if max_results is not None else self.max_results
        # Build search parameters
        params = {
            "q": query,
            "format": "json",
            "categories": category,
            "language": language
        }

        # Add optional parameters
        if engines:
            params["engines"] = ",".join(engines)

        if time_range:
            params["time_range"] = time_range

        try:
            response = requests.get(
                f"{self.base_url}/search",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            # Format and limit results
            formatted_results = []
            for result in results[:result_limit]:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "engine": result.get("engine", ""),
                    "category": result.get("category", ""),
                    "publishedDate": result.get("publishedDate", "")
                })

            return formatted_results

        except requests.exceptions.RequestException as e:
            print(f"SearXNG search error: {e}")
            return []

    def search_general(self, query: str, **kwargs) -> List[Dict]:
        """General web search"""
        return self.search(query, category="general", **kwargs)

    def search_news(self, query: str, time_range: str = "week", **kwargs) -> List[Dict]:
        """News search with recent articles"""
        return self.search(query, category="news", time_range=time_range, **kwargs)

    def search_social(self, query: str, **kwargs) -> List[Dict]:
        """Social media search (Reddit, Lemmy, etc.)"""
        return self.search(query, category="social media", **kwargs)

    def search_images(self, query: str, **kwargs) -> List[Dict]:
        """Image search"""
        return self.search(query, category="images", **kwargs)

    def search_videos(self, query: str, **kwargs) -> List[Dict]:
        """Video search"""
        return self.search(query, category="videos", **kwargs)

    def search_tech(self, query: str, **kwargs) -> List[Dict]:
        """Tech/IT search (GitHub, StackOverflow, etc.)"""
        return self.search(query, category="it", **kwargs)

    def search_academic(self, query: str, **kwargs) -> List[Dict]:
        """Academic/scientific search"""
        return self.search(query, category="science", **kwargs)

    def multi_category_search(
        self,
        query: str,
        categories: List[str]
    ) -> Dict[str, List[Dict]]:
        """
        Search across multiple categories

        Args:
            query: Search query
            categories: List of categories to search

        Returns:
            Dict with category names as keys and result lists as values
        """
        results = {}
        for category in categories:
            results[category] = self.search(query, category=category)

        return results

    def trend_search(
        self,
        topic: str,
        sources: List[str] = ["reddit", "hackernews"]
    ) -> List[Dict]:
        """
        Search for trending topics and discussions

        Args:
            topic: Topic to search for
            sources: Social/tech platforms to search

        Returns:
            Recent discussions and mentions
        """
        # Search across multiple engines
        results = []

        if "reddit" in sources:
            reddit_results = self.search(
                topic,
                category="social media",
                engines=["reddit"],
                time_range="week"
            )
            results.extend(reddit_results)

        if "hackernews" in sources:
            hn_results = self.search(
                topic,
                category="it",
                engines=["hackernews"],
                time_range="week"
            )
            results.extend(hn_results)

        # Sort by recency
        return sorted(
            results,
            key=lambda x: x.get("publishedDate", ""),
            reverse=True
        )

    def competitor_search(
        self,
        company_name: str,
        keywords: List[str]
    ) -> Dict[str, List[Dict]]:
        """
        Search for competitor information

        Args:
            company_name: Competitor company name
            keywords: Additional keywords (e.g., 'pricing', 'features', 'reviews')

        Returns:
            Search results categorized by keyword
        """
        results = {}

        for keyword in keywords:
            query = f"{company_name} {keyword}"
            search_results = self.search_general(query)
            results[keyword] = search_results

        return results

    def market_research(
        self,
        industry: str,
        topics: List[str]
    ) -> Dict[str, List[Dict]]:
        """
        Perform market research across multiple topics

        Args:
            industry: Industry name
            topics: List of topics to research

        Returns:
            Research results by topic
        """
        results = {}

        for topic in topics:
            query = f"{industry} {topic}"

            # Search news and general web
            news_results = self.search_news(query, time_range="month")
            general_results = self.search_general(query)

            results[topic] = {
                "news": news_results[:5],
                "general": general_results[:5]
            }

        return results

    def get_engines(self) -> List[str]:
        """Get list of available search engines"""
        try:
            response = requests.get(
                f"{self.base_url}/config",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            engines = []
            for engine in data.get("engines", []):
                if not engine.get("disabled", False):
                    engines.append(engine.get("name", ""))

            return engines

        except requests.exceptions.RequestException as e:
            print(f"Error fetching engines: {e}")
            return []

    def health_check(self) -> bool:
        """Check if SearXNG is accessible"""
        try:
            response = requests.get(
                f"{self.base_url}/healthz",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


# ==================== LANGCHAIN INTEGRATION ====================

def create_searxng_langchain_tool():
    """Create LangChain-compatible tool"""
    from langchain.tools import Tool

    searxng = SearXNGTool()

    def search_wrapper(query: str) -> str:
        """Search wrapper for LangChain"""
        results = searxng.search_general(query)

        if not results:
            return "No results found."

        # Format results as string
        formatted = []
        for i, result in enumerate(results[:5], 1):
            formatted.append(
                f"{i}. **{result['title']}**\n"
                f"   URL: {result['url']}\n"
                f"   {result['content']}\n"
            )

        return "\n".join(formatted)

    return Tool(
        name="SearXNG_Search",
        func=search_wrapper,
        description="Search the web using self-hosted meta-search engine. "
                    "Useful for finding current information, competitor data, market trends, "
                    "and research topics. Input should be a search query string."
    )


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Initialize tool
    searxng = SearXNGTool(base_url="http://localhost:8080")

    # Test connection
    if searxng.health_check():
        print("✓ SearXNG is running")

        # General search
        print("\n=== General Search ===")
        results = searxng.search_general("B2B marketing automation trends")
        for result in results[:3]:
            print(f"- {result['title']}")
            print(f"  {result['url']}\n")

        # News search
        print("\n=== News Search ===")
        news = searxng.search_news("AI marketing", time_range="week")
        for article in news[:3]:
            print(f"- {article['title']}")
            print(f"  Published: {article.get('publishedDate', 'N/A')}\n")

        # Trend search
        print("\n=== Trend Search ===")
        trends = searxng.trend_search("marketing automation")
        for item in trends[:3]:
            print(f"- {item['title']} ({item.get('engine', 'unknown')})")

        # Available engines
        print("\n=== Available Engines ===")
        engines = searxng.get_engines()
        print(", ".join(engines))

    else:
        print("✗ SearXNG is not accessible")
        print("Make sure the container is running: docker-compose up -d searxng")
