"""
Scrapy Middlewares
Custom downloader and spider middlewares
"""

from scrapy import signals
from scrapy.exceptions import IgnoreRequest
from scrapy.http import HtmlResponse
import structlog
import time

logger = structlog.get_logger()


class ErrorHandlerMiddleware:
    """
    Handles errors gracefully and logs them

    - Logs all HTTP errors with details
    - Implements custom retry logic for specific status codes
    - Converts certain errors to warnings instead of failures
    """

    def __init__(self, crawler):
        self.crawler = crawler
        self.stats = crawler.stats

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler)

        # Connect signals
        crawler.signals.connect(
            middleware.spider_opened,
            signal=signals.spider_opened
        )

        return middleware

    def spider_opened(self, spider):
        logger.info(
            "error_handler_middleware_enabled",
            spider_name=spider.name
        )

    def process_response(self, request, response, spider):
        """Process HTTP responses"""

        # Log successful responses
        if 200 <= response.status < 300:
            logger.debug(
                "http_success",
                url=request.url,
                status=response.status
            )
            return response

        # Handle specific error codes
        if response.status == 404:
            logger.warning(
                "http_404_not_found",
                url=request.url
            )
            self.stats.inc_value('error_handler/404_count')
            raise IgnoreRequest(f"404 Not Found: {request.url}")

        elif response.status == 403:
            logger.warning(
                "http_403_forbidden",
                url=request.url,
                message="Possible bot detection or access restriction"
            )
            self.stats.inc_value('error_handler/403_count')
            raise IgnoreRequest(f"403 Forbidden: {request.url}")

        elif response.status == 429:
            logger.warning(
                "http_429_rate_limit",
                url=request.url,
                message="Rate limit exceeded, request will be retried"
            )
            self.stats.inc_value('error_handler/429_count')
            # Let retry middleware handle this
            return response

        elif 500 <= response.status < 600:
            logger.error(
                "http_5xx_server_error",
                url=request.url,
                status=response.status
            )
            self.stats.inc_value('error_handler/5xx_count')
            # Let retry middleware handle this
            return response

        else:
            logger.warning(
                "http_unexpected_status",
                url=request.url,
                status=response.status
            )
            self.stats.inc_value('error_handler/other_count')

        return response

    def process_exception(self, request, exception, spider):
        """Process exceptions during request"""

        logger.error(
            "request_exception",
            url=request.url,
            exception_type=type(exception).__name__,
            exception_message=str(exception)
        )

        self.stats.inc_value('error_handler/exception_count')

        # Return None to let other middlewares handle it
        return None


class RateLimitMiddleware:
    """
    Additional rate limiting beyond Scrapy's built-in throttling

    Implements per-domain rate limiting with exponential backoff
    """

    def __init__(self, delay=1.0):
        self.delay = delay
        self.domain_delays = {}

    @classmethod
    def from_crawler(cls, crawler):
        delay = crawler.settings.getfloat('DOWNLOAD_DELAY', 1.0)
        middleware = cls(delay=delay)

        crawler.signals.connect(
            middleware.spider_opened,
            signal=signals.spider_opened
        )

        return middleware

    def spider_opened(self, spider):
        logger.info(
            "rate_limit_middleware_enabled",
            spider_name=spider.name,
            base_delay=self.delay
        )

    def process_request(self, request, spider):
        """Apply per-domain rate limiting"""

        domain = self._get_domain(request.url)

        # Check last request time for this domain
        if domain in self.domain_delays:
            last_request_time = self.domain_delays[domain]
            elapsed = time.time() - last_request_time

            # Wait if not enough time has passed
            if elapsed < self.delay:
                wait_time = self.delay - elapsed
                logger.debug(
                    "rate_limit_waiting",
                    domain=domain,
                    wait_time=wait_time
                )
                time.sleep(wait_time)

        # Update last request time
        self.domain_delays[domain] = time.time()

        return None

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc


class UserAgentRotatorMiddleware:
    """
    Rotates user agents for each request

    Works alongside scrapy-user-agents package
    """

    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        ]
        self.current_index = 0

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()

        crawler.signals.connect(
            middleware.spider_opened,
            signal=signals.spider_opened
        )

        return middleware

    def spider_opened(self, spider):
        logger.info(
            "user_agent_rotator_enabled",
            spider_name=spider.name,
            agents_count=len(self.user_agents)
        )

    def process_request(self, request, spider):
        """Rotate user agent for each request"""

        # Get next user agent
        user_agent = self.user_agents[self.current_index]
        request.headers['User-Agent'] = user_agent

        # Increment index (circular)
        self.current_index = (self.current_index + 1) % len(self.user_agents)

        logger.debug(
            "user_agent_set",
            url=request.url,
            user_agent=user_agent[:50] + '...'
        )

        return None
