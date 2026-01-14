"""
Scrapy Settings for Competitor Monitoring
Optimized for respectful, efficient web scraping
"""

import os

# Scrapy Project
BOT_NAME = 'marketing_scraper'
SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'

# Respectful Crawling Settings
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
DOWNLOAD_DELAY = 1.0  # Respect rate limits (1 second between requests)
RANDOMIZE_DOWNLOAD_DELAY = True  # Randomize delay (0.5x to 1.5x)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# Cookies and Sessions
COOKIES_ENABLED = True
COOKIES_DEBUG = False

# User Agent Rotation
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 500,
    'scrapy_rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
    'scrapy_rotating_proxies.middlewares.BanDetectionMiddleware': 620,
    'middlewares.ErrorHandlerMiddleware': 700,
}

# User Agents Pool
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

# Retry Configuration
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]

# Redirect Settings
REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 5

# HTTP Caching (Redis-backed)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600  # 1 hour cache
HTTPCACHE_DIR = '/tmp/scrapy_httpcache'
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
# Alternative: Redis cache
# HTTPCACHE_STORAGE = 'scrapy_redis.cache.RedisCacheStorage'

# Item Pipelines
ITEM_PIPELINES = {
    'pipelines.ValidationPipeline': 100,
    'pipelines.CleaningPipeline': 200,
    'pipelines.PostgreSQLPipeline': 300,
    'pipelines.DuplicatesPipeline': 400,
}

# Database Settings
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://n8n:n8npassword@postgres:5432/marketing'
)

# Redis Settings
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(levelname)s: %(message)s'
LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'

# Telemetry (disable for privacy)
TELNETCONSOLE_ENABLED = False
HTTPERROR_ALLOWED_CODES = [404, 403]  # Don't retry these

# Download Timeout
DOWNLOAD_TIMEOUT = 30

# DNS Cache
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000

# Feed Export (optional JSON output)
FEEDS = {
    '/tmp/scrapy_export.json': {
        'format': 'json',
        'encoding': 'utf8',
        'overwrite': True,
    },
}

# Media Pipeline (for images, if needed)
# IMAGES_STORE = '/tmp/scrapy_images'
# IMAGES_EXPIRES = 90  # days

# Proxy Settings (if using proxy rotation)
ROTATING_PROXY_LIST_PATH = os.getenv('PROXY_LIST_PATH', None)
