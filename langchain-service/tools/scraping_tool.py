"""
Web Scraping Tool
LangChain tool for extracting content from web pages using Trafilatura and Playwright
"""

from langchain.tools import Tool, StructuredTool
from langchain.pydantic_v1 import BaseModel, Field
from typing import Optional, Dict, Any, List
import trafilatura
import requests
import structlog
from datetime import datetime
import json

logger = structlog.get_logger()


class WebScrapingInput(BaseModel):
    """Input for web scraping tool"""
    url: str = Field(description="URL of the webpage to scrape")
    include_links: bool = Field(
        default=False,
        description="Whether to include extracted links"
    )
    include_images: bool = Field(
        default=False,
        description="Whether to include image URLs"
    )
    include_metadata: bool = Field(
        default=True,
        description="Whether to include page metadata (title, author, date)"
    )
    use_playwright: bool = Field(
        default=False,
        description="Use Playwright for JavaScript-rendered pages"
    )


class WebScrapingTool:
    """
    Web scraping tool using Trafilatura for content extraction

    Features:
    - Clean content extraction without ads/boilerplate
    - Metadata extraction (title, author, date, description)
    - Link and image extraction
    - Optional Playwright for JavaScript rendering
    - Automatic encoding detection
    """

    def __init__(self, playwright_url: Optional[str] = None):
        """
        Initialize scraping tool

        Args:
            playwright_url: URL of Playwright service (e.g., http://playwright-service:8002)
        """
        self.playwright_url = playwright_url or "http://playwright-service:8002"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scrape_page(
        self,
        url: str,
        include_links: bool = False,
        include_images: bool = False,
        include_metadata: bool = True,
        use_playwright: bool = False
    ) -> str:
        """
        Scrape webpage and extract clean content

        Args:
            url: URL to scrape
            include_links: Include extracted links
            include_images: Include image URLs
            include_metadata: Include page metadata
            use_playwright: Use Playwright for JS rendering

        Returns:
            JSON string with extracted content
        """
        try:
            logger.info("scraping_page", url=url, use_playwright=use_playwright)

            # Fetch HTML
            if use_playwright:
                html = self._fetch_with_playwright(url)
            else:
                html = self._fetch_with_requests(url)

            # Extract content
            content = trafilatura.extract(
                html,
                include_links=include_links,
                include_images=include_images,
                include_comments=False,
                output_format='txt'
            )

            if not content:
                logger.warning("no_content_extracted", url=url)
                return json.dumps({
                    "success": False,
                    "error": "No content could be extracted from the page"
                })

            # Build result
            result = {
                "success": True,
                "url": url,
                "content": content,
                "word_count": len(content.split()),
                "scraped_at": datetime.now().isoformat()
            }

            # Add metadata if requested
            if include_metadata:
                metadata = self._extract_metadata(html)
                result["metadata"] = metadata

            # Add links if requested
            if include_links:
                links = self._extract_links(html)
                result["links"] = links

            # Add images if requested
            if include_images:
                images = self._extract_images(html)
                result["images"] = images

            logger.info(
                "scraping_completed",
                url=url,
                word_count=result["word_count"],
                has_metadata=include_metadata
            )

            return json.dumps(result, indent=2)

        except Exception as e:
            logger.error("scraping_error", url=url, error=str(e))
            return json.dumps({
                "success": False,
                "url": url,
                "error": str(e)
            })

    def _fetch_with_requests(self, url: str) -> str:
        """Fetch HTML using requests library"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text

        except requests.RequestException as e:
            logger.error("requests_fetch_error", url=url, error=str(e))
            raise

    def _fetch_with_playwright(self, url: str) -> str:
        """Fetch HTML using Playwright service for JavaScript rendering"""
        try:
            response = requests.post(
                f"{self.playwright_url}/render",
                json={"url": url, "wait_for": "networkidle"},
                timeout=60
            )
            response.raise_for_status()

            data = response.json()

            if not data.get("success"):
                raise Exception(f"Playwright rendering failed: {data.get('error')}")

            return data.get("html", "")

        except requests.RequestException as e:
            logger.error("playwright_fetch_error", url=url, error=str(e))
            raise

    def _extract_metadata(self, html: str) -> Dict[str, Optional[str]]:
        """Extract page metadata using Trafilatura"""
        metadata = trafilatura.extract_metadata(html)

        if not metadata:
            return {}

        return {
            "title": metadata.title,
            "author": metadata.author,
            "date": metadata.date,
            "description": metadata.description,
            "sitename": metadata.sitename,
            "categories": metadata.categories,
            "tags": metadata.tags,
            "language": metadata.language
        }

    def _extract_links(self, html: str) -> List[str]:
        """Extract all links from HTML"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'lxml')
        links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('http'):
                links.append(href)

        return list(set(links))  # Deduplicate

    def _extract_images(self, html: str) -> List[Dict[str, str]]:
        """Extract image URLs with alt text"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'lxml')
        images = []

        for img_tag in soup.find_all('img', src=True):
            images.append({
                "src": img_tag['src'],
                "alt": img_tag.get('alt', '')
            })

        return images


# === LangChain Tool Creation ===

def create_web_scraping_tool(playwright_url: Optional[str] = None) -> StructuredTool:
    """
    Create LangChain web scraping tool

    Args:
        playwright_url: URL of Playwright service

    Returns:
        StructuredTool for web scraping
    """
    scraper = WebScrapingTool(playwright_url=playwright_url)

    return StructuredTool(
        name="web_scraper",
        description=(
            "Extract clean content from web pages. "
            "Returns page text, metadata (title, author, date), and optionally links/images. "
            "Use this tool to scrape competitor websites, blog posts, or any web content. "
            "Set use_playwright=true for JavaScript-heavy pages."
        ),
        func=scraper.scrape_page,
        args_schema=WebScrapingInput
    )


# === Simplified Tools ===

def create_simple_scraping_tool(playwright_url: Optional[str] = None) -> Tool:
    """
    Create simplified web scraping tool (URL input only)

    Returns:
        Tool for basic web scraping
    """
    scraper = WebScrapingTool(playwright_url=playwright_url)

    def scrape_url(url: str) -> str:
        """Scrape URL and return content"""
        return scraper.scrape_page(
            url=url,
            include_metadata=True,
            include_links=False,
            include_images=False,
            use_playwright=False
        )

    return Tool(
        name="scrape_url",
        description=(
            "Scrape a URL and extract clean text content with metadata. "
            "Input: URL string. "
            "Output: JSON with content, title, author, date, word count."
        ),
        func=scrape_url
    )


def create_js_scraping_tool(playwright_url: Optional[str] = None) -> Tool:
    """
    Create JavaScript scraping tool (uses Playwright)

    Returns:
        Tool for scraping JavaScript-rendered pages
    """
    scraper = WebScrapingTool(playwright_url=playwright_url)

    def scrape_js_page(url: str) -> str:
        """Scrape JavaScript-rendered page"""
        return scraper.scrape_page(
            url=url,
            include_metadata=True,
            include_links=True,
            include_images=True,
            use_playwright=True
        )

    return Tool(
        name="scrape_js_page",
        description=(
            "Scrape JavaScript-rendered web pages using headless browser. "
            "Use this for single-page applications (React, Vue, Angular) "
            "or pages that load content dynamically. "
            "Input: URL string. "
            "Output: JSON with content, metadata, links, images."
        ),
        func=scrape_js_page
    )


# === Batch Scraping ===

class BatchScrapingTool:
    """
    Batch web scraping tool for scraping multiple URLs

    Useful for processing lists of competitor pages or blog posts
    """

    def __init__(self, playwright_url: Optional[str] = None):
        self.scraper = WebScrapingTool(playwright_url=playwright_url)

    def scrape_multiple(
        self,
        urls: List[str],
        use_playwright: bool = False,
        max_concurrent: int = 5
    ) -> str:
        """
        Scrape multiple URLs

        Args:
            urls: List of URLs to scrape
            use_playwright: Use Playwright for all URLs
            max_concurrent: Maximum concurrent requests

        Returns:
            JSON string with results for all URLs
        """
        import concurrent.futures

        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit scraping tasks
            future_to_url = {
                executor.submit(
                    self.scraper.scrape_page,
                    url,
                    include_metadata=True,
                    use_playwright=use_playwright
                ): url
                for url in urls
            }

            # Collect results
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results.append(json.loads(result))
                except Exception as e:
                    logger.error("batch_scraping_error", url=url, error=str(e))
                    results.append({
                        "success": False,
                        "url": url,
                        "error": str(e)
                    })

        return json.dumps({
            "total_urls": len(urls),
            "successful": len([r for r in results if r.get("success")]),
            "failed": len([r for r in results if not r.get("success")]),
            "results": results
        }, indent=2)


def create_batch_scraping_tool(playwright_url: Optional[str] = None) -> Tool:
    """
    Create batch scraping tool

    Returns:
        Tool for scraping multiple URLs
    """
    batch_scraper = BatchScrapingTool(playwright_url=playwright_url)

    def scrape_urls(urls_json: str) -> str:
        """
        Scrape multiple URLs from JSON list

        Args:
            urls_json: JSON string with "urls" array

        Returns:
            JSON with results
        """
        try:
            data = json.loads(urls_json)
            urls = data.get("urls", [])

            if not urls:
                return json.dumps({"error": "No URLs provided"})

            return batch_scraper.scrape_multiple(urls)

        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {str(e)}"})

    return Tool(
        name="batch_scrape",
        description=(
            "Scrape multiple URLs in parallel. "
            "Input: JSON with 'urls' array like {\"urls\": [\"url1\", \"url2\"]}. "
            "Output: JSON with results for all URLs including success/failure counts."
        ),
        func=scrape_urls
    )
