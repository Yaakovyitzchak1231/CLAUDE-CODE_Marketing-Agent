"""
Browser Manager for Playwright Service
Handles browser lifecycle, context management, and page automation
"""

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import Optional, Dict, Any, List
import structlog
import asyncio
from contextlib import asynccontextmanager

logger = structlog.get_logger()


class BrowserManager:
    """
    Manages Playwright browser instances and contexts

    Features:
    - Browser pooling for performance
    - Context isolation for concurrent requests
    - Screenshot capture
    - HTML extraction
    - JavaScript rendering
    - Cookie/session management
    """

    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",
        user_agent: Optional[str] = None
    ):
        """
        Initialize Browser Manager

        Args:
            headless: Run browser in headless mode
            browser_type: Browser type (chromium, firefox, webkit)
            user_agent: Custom user agent string
        """
        self.headless = headless
        self.browser_type = browser_type
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        self.playwright = None
        self.browser: Optional[Browser] = None

        logger.info(
            "browser_manager_initialized",
            headless=headless,
            browser_type=browser_type
        )

    async def start(self):
        """Start Playwright and launch browser"""
        if self.browser is not None:
            logger.warning("browser_already_started")
            return

        logger.info("starting_playwright_browser")

        self.playwright = await async_playwright().start()

        # Select browser type
        if self.browser_type == "firefox":
            browser_launcher = self.playwright.firefox
        elif self.browser_type == "webkit":
            browser_launcher = self.playwright.webkit
        else:
            browser_launcher = self.playwright.chromium

        # Launch browser
        self.browser = await browser_launcher.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )

        logger.info("playwright_browser_started", browser_type=self.browser_type)

    async def stop(self):
        """Stop browser and cleanup"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            logger.info("browser_stopped")

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
            logger.info("playwright_stopped")

    @asynccontextmanager
    async def create_context(
        self,
        viewport: Optional[Dict[str, int]] = None,
        user_agent: Optional[str] = None
    ):
        """
        Create isolated browser context

        Args:
            viewport: Viewport dimensions {"width": 1920, "height": 1080}
            user_agent: Custom user agent for this context

        Yields:
            BrowserContext: Isolated browser context
        """
        if not self.browser:
            await self.start()

        viewport = viewport or {"width": 1920, "height": 1080}
        user_agent = user_agent or self.user_agent

        context = await self.browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            java_script_enabled=True,
            accept_downloads=False
        )

        try:
            yield context
        finally:
            await context.close()

    async def render_page(
        self,
        url: str,
        wait_for: str = "networkidle",
        timeout: int = 30000,
        viewport: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Render page and extract content

        Args:
            url: URL to render
            wait_for: Wait condition (load, domcontentloaded, networkidle)
            timeout: Timeout in milliseconds
            viewport: Viewport dimensions

        Returns:
            Dict with HTML content, title, and metadata
        """
        logger.info("rendering_page", url=url, wait_for=wait_for)

        async with self.create_context(viewport=viewport) as context:
            page = await context.new_page()

            try:
                # Navigate to URL
                response = await page.goto(
                    url,
                    wait_until=wait_for,
                    timeout=timeout
                )

                # Extract content
                html = await page.content()
                title = await page.title()
                url_final = page.url

                # Get metadata
                status_code = response.status if response else None

                logger.info(
                    "page_rendered",
                    url=url,
                    final_url=url_final,
                    status=status_code,
                    html_length=len(html)
                )

                return {
                    "success": True,
                    "url": url,
                    "final_url": url_final,
                    "title": title,
                    "html": html,
                    "status_code": status_code
                }

            except Exception as e:
                logger.error("page_render_error", url=url, error=str(e))
                return {
                    "success": False,
                    "url": url,
                    "error": str(e)
                }

            finally:
                await page.close()

    async def take_screenshot(
        self,
        url: str,
        full_page: bool = False,
        viewport: Optional[Dict[str, int]] = None,
        wait_for: str = "networkidle",
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """
        Take screenshot of page

        Args:
            url: URL to screenshot
            full_page: Capture full scrollable page
            viewport: Viewport dimensions
            wait_for: Wait condition
            timeout: Timeout in milliseconds

        Returns:
            Dict with screenshot bytes and metadata
        """
        logger.info("taking_screenshot", url=url, full_page=full_page)

        async with self.create_context(viewport=viewport) as context:
            page = await context.new_page()

            try:
                # Navigate to URL
                await page.goto(url, wait_until=wait_for, timeout=timeout)

                # Take screenshot
                screenshot = await page.screenshot(
                    full_page=full_page,
                    type="png"
                )

                title = await page.title()

                logger.info(
                    "screenshot_captured",
                    url=url,
                    size_bytes=len(screenshot)
                )

                return {
                    "success": True,
                    "url": url,
                    "title": title,
                    "screenshot": screenshot,
                    "size_bytes": len(screenshot)
                }

            except Exception as e:
                logger.error("screenshot_error", url=url, error=str(e))
                return {
                    "success": False,
                    "url": url,
                    "error": str(e)
                }

            finally:
                await page.close()

    async def execute_javascript(
        self,
        url: str,
        script: str,
        wait_for: str = "networkidle",
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """
        Execute JavaScript on page

        Args:
            url: URL to load
            script: JavaScript code to execute
            wait_for: Wait condition
            timeout: Timeout in milliseconds

        Returns:
            Dict with script result
        """
        logger.info("executing_javascript", url=url)

        async with self.create_context() as context:
            page = await context.new_page()

            try:
                # Navigate to URL
                await page.goto(url, wait_until=wait_for, timeout=timeout)

                # Execute script
                result = await page.evaluate(script)

                logger.info("javascript_executed", url=url)

                return {
                    "success": True,
                    "url": url,
                    "result": result
                }

            except Exception as e:
                logger.error("javascript_error", url=url, error=str(e))
                return {
                    "success": False,
                    "url": url,
                    "error": str(e)
                }

            finally:
                await page.close()

    async def extract_links(
        self,
        url: str,
        selector: Optional[str] = None,
        wait_for: str = "networkidle",
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """
        Extract links from page

        Args:
            url: URL to scrape
            selector: CSS selector for links (default: all 'a' tags)
            wait_for: Wait condition
            timeout: Timeout in milliseconds

        Returns:
            Dict with list of links
        """
        logger.info("extracting_links", url=url, selector=selector)

        async with self.create_context() as context:
            page = await context.new_page()

            try:
                # Navigate to URL
                await page.goto(url, wait_until=wait_for, timeout=timeout)

                # Extract links
                selector = selector or "a"
                links = await page.evaluate(f'''
                    () => {{
                        const elements = document.querySelectorAll("{selector}");
                        return Array.from(elements).map(el => ({{
                            href: el.href,
                            text: el.textContent.trim(),
                            title: el.title || null
                        }}));
                    }}
                ''')

                logger.info("links_extracted", url=url, count=len(links))

                return {
                    "success": True,
                    "url": url,
                    "links": links,
                    "count": len(links)
                }

            except Exception as e:
                logger.error("link_extraction_error", url=url, error=str(e))
                return {
                    "success": False,
                    "url": url,
                    "error": str(e)
                }

            finally:
                await page.close()

    async def get_cookies(
        self,
        url: str,
        wait_for: str = "networkidle",
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """
        Get cookies from page

        Args:
            url: URL to visit
            wait_for: Wait condition
            timeout: Timeout in milliseconds

        Returns:
            Dict with cookies
        """
        logger.info("getting_cookies", url=url)

        async with self.create_context() as context:
            page = await context.new_page()

            try:
                # Navigate to URL
                await page.goto(url, wait_until=wait_for, timeout=timeout)

                # Get cookies
                cookies = await context.cookies()

                logger.info("cookies_retrieved", url=url, count=len(cookies))

                return {
                    "success": True,
                    "url": url,
                    "cookies": cookies,
                    "count": len(cookies)
                }

            except Exception as e:
                logger.error("cookie_error", url=url, error=str(e))
                return {
                    "success": False,
                    "url": url,
                    "error": str(e)
                }

            finally:
                await page.close()


# Singleton instance
_browser_manager: Optional[BrowserManager] = None


async def get_browser_manager() -> BrowserManager:
    """Get or create singleton browser manager"""
    global _browser_manager

    if _browser_manager is None:
        _browser_manager = BrowserManager(headless=True, browser_type="chromium")
        await _browser_manager.start()

    return _browser_manager
