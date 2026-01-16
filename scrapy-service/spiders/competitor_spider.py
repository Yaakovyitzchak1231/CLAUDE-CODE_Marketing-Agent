"""
Competitor Website Spider
Scrapes competitor websites for content monitoring and analysis
"""

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from datetime import datetime
from urllib.parse import urlparse
import trafilatura
import re
from typing import Dict, Any, Optional, List


class CompetitorSpider(CrawlSpider):
    """
    Spider for comprehensive competitor website scraping

    Features:
    - Blog post extraction
    - Product page scraping
    - Press release monitoring
    - Content change detection
    - Pricing information extraction
    """

    name = 'competitor'
    custom_settings = {
        'DEPTH_LIMIT': 3,  # Crawl 3 levels deep
        'CLOSESPIDER_PAGECOUNT': 100,  # Stop after 100 pages
    }

    def __init__(
        self,
        url: str,
        competitor_id: str,
        scrape_type: str = 'full',
        allowed_domains: Optional[List[str]] = None,
        max_depth: Optional[int] = None,
        max_pages: Optional[int] = None,
        *args,
        **kwargs,
    ):
        """
        Initialize Competitor Spider

        Args:
            url: Competitor website URL
            competitor_id: Competitor UUID
            scrape_type: Type of scrape (full, blog, pricing, products)
        """
        super(CompetitorSpider, self).__init__(*args, **kwargs)

        self.start_urls = [url]
        self.competitor_id = competitor_id
        self.scrape_type = scrape_type

        # Parse domain
        parsed = urlparse(url)
        self.allowed_domains = (
            [d.replace('www.', '') for d in allowed_domains]
            if allowed_domains
            else [parsed.netloc.replace('www.', '')]
        )

        # Allow per-request depth/page limits
        self.custom_settings = dict(self.custom_settings)
        if max_depth is not None:
            self.custom_settings['DEPTH_LIMIT'] = max_depth
        if max_pages is not None:
            self.custom_settings['CLOSESPIDER_PAGECOUNT'] = max_pages

        # Define crawling rules based on scrape type
        self.rules = self._get_rules(scrape_type)

        # Compile rules after __init__
        self._compile_rules()

        self.logger.info(f"Initialized CompetitorSpider for {url} (type: {scrape_type})")

    def _get_rules(self, scrape_type: str) -> tuple:
        """Get crawling rules based on scrape type"""

        if scrape_type == 'blog':
            # Blog-focused crawling
            return (
                Rule(
                    LinkExtractor(
                        allow=(r'/blog/', r'/posts/', r'/articles/', r'/news/'),
                        deny=(r'/tag/', r'/category/', r'/author/', r'/page/\d+')
                    ),
                    callback='parse_blog_post',
                    follow=True
                ),
            )

        elif scrape_type == 'pricing':
            # Pricing page crawling
            return (
                Rule(
                    LinkExtractor(
                        allow=(r'/pricing', r'/plans', r'/packages'),
                    ),
                    callback='parse_pricing',
                    follow=False
                ),
            )

        elif scrape_type == 'products':
            # Product page crawling
            return (
                Rule(
                    LinkExtractor(
                        allow=(r'/product', r'/products', r'/solutions', r'/features'),
                        deny=(r'/cart', r'/checkout')
                    ),
                    callback='parse_product',
                    follow=True
                ),
            )

        else:
            # Full site crawl
            return (
                Rule(
                    LinkExtractor(
                        allow=(),  # Allow all
                        deny=(
                            r'/login', r'/signup', r'/cart', r'/checkout',
                            r'/admin', r'/wp-admin', r'/user',
                            r'\.(pdf|zip|jpg|png|gif|svg|mp4|mp3)$'
                        )
                    ),
                    callback='parse_page',
                    follow=True
                ),
            )

    def parse_page(self, response):
        """Parse generic page (full crawl)"""

        # Extract clean content using Trafilatura
        content = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=True,
            no_fallback=False
        )

        if not content or len(content) < 100:
            self.logger.warning(f"Low content on {response.url}")
            return

        yield {
            'competitor_id': self.competitor_id,
            'url': response.url,
            'title': response.css('title::text').get(),
            'content': content,
            'content_type': 'page',
            'word_count': len(content.split()),
            'links_count': len(response.css('a::attr(href)').getall()),
            'images_count': len(response.css('img::attr(src)').getall()),
            'scraped_at': datetime.utcnow().isoformat(),
            'meta_description': response.css('meta[name="description"]::attr(content)').get(),
            'h1_tags': response.css('h1::text').getall(),
            'h2_tags': response.css('h2::text').getall(),
        }

    def parse_blog_post(self, response):
        """Parse blog post with metadata"""

        # Extract content
        content = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=True,
            no_fallback=False
        )

        if not content:
            return

        # Extract metadata
        metadata = trafilatura.extract_metadata(response.text)

        # Extract author
        author = (
            metadata.author if metadata else None or
            response.css('meta[name="author"]::attr(content)').get() or
            response.css('.author::text').get() or
            response.css('[rel="author"]::text').get()
        )

        # Extract publish date
        pub_date = (
            metadata.date if metadata else None or
            response.css('meta[property="article:published_time"]::attr(content)').get() or
            response.css('time::attr(datetime)').get() or
            response.css('.published::text').get()
        )

        # Extract categories/tags
        categories = response.css('.category::text, .tag::text, [rel="category tag"]::text').getall()

        yield {
            'competitor_id': self.competitor_id,
            'url': response.url,
            'title': metadata.title if metadata else response.css('title::text').get(),
            'content': content,
            'content_type': 'blog_post',
            'author': author,
            'published_date': pub_date,
            'categories': categories,
            'word_count': len(content.split()),
            'reading_time': round(len(content.split()) / 200, 1),
            'images_count': len(response.css('article img, .post img').getall()),
            'scraped_at': datetime.utcnow().isoformat(),
            'meta_description': response.css('meta[name="description"]::attr(content)').get(),
            'meta_keywords': response.css('meta[name="keywords"]::attr(content)').get(),
        }

    def parse_pricing(self, response):
        """Parse pricing page"""

        # Extract pricing tiers
        tiers = []

        # Try common pricing selectors
        pricing_containers = response.css(
            '.pricing-tier, .price-box, .pricing-card, .plan, [class*="pricing"]'
        )

        for container in pricing_containers:
            tier_name = container.css('.tier-name::text, .plan-name::text, h3::text').get()
            price = container.css('.price::text, [class*="price"]::text').get()

            # Extract features
            features = container.css('li::text, .feature::text').getall()

            if tier_name or price:
                tiers.append({
                    'name': tier_name.strip() if tier_name else 'Unknown',
                    'price': self._clean_price(price) if price else None,
                    'features': [f.strip() for f in features if f.strip()],
                })

        # Fallback: extract all prices on page
        if not tiers:
            prices = response.css('[class*="price"]::text').getall()
            tiers = [{'price': self._clean_price(p)} for p in prices if p.strip()]

        yield {
            'competitor_id': self.competitor_id,
            'url': response.url,
            'title': response.css('title::text').get(),
            'content_type': 'pricing',
            'pricing_tiers': tiers,
            'scraped_at': datetime.utcnow().isoformat(),
        }

    def parse_product(self, response):
        """Parse product page"""

        # Extract product information
        content = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=True,
            no_fallback=False
        )

        # Extract product title
        product_name = (
            response.css('h1::text').get() or
            response.css('.product-title::text, .product-name::text').get() or
            response.css('title::text').get()
        )

        # Extract price
        price = (
            response.css('.price::text, [itemprop="price"]::text').get() or
            response.css('[class*="price"]::text').re_first(r'[\$€£]\s*[\d,]+\.?\d*')
        )

        # Extract features
        features = response.css(
            '.features li::text, .benefits li::text, [class*="feature"]::text'
        ).getall()

        yield {
            'competitor_id': self.competitor_id,
            'url': response.url,
            'title': product_name,
            'content': content,
            'content_type': 'product',
            'price': self._clean_price(price) if price else None,
            'features': [f.strip() for f in features if f.strip()],
            'images': response.css('.product-image img::attr(src), [itemprop="image"]::attr(src)').getall(),
            'scraped_at': datetime.utcnow().isoformat(),
        }

    def _clean_price(self, price_str: Optional[str]) -> Optional[str]:
        """Clean price string"""
        if not price_str:
            return None

        # Remove extra whitespace
        price_str = price_str.strip()

        # Extract numeric price
        match = re.search(r'[\$€£]?\s*([\d,]+\.?\d*)', price_str)
        if match:
            return match.group(0).strip()

        return price_str


class BlogMonitorSpider(scrapy.Spider):
    """
    Simplified spider for blog monitoring
    Scrapes only the blog feed/archive for new posts
    """

    name = 'blog_monitor'
    custom_settings = {
        'DEPTH_LIMIT': 1,
        'CLOSESPIDER_PAGECOUNT': 20,
    }

    def __init__(
        self,
        url: str,
        competitor_id: str,
        allowed_domains: Optional[List[str]] = None,
        max_posts: int = 20,
        *args,
        **kwargs,
    ):
        super(BlogMonitorSpider, self).__init__(*args, **kwargs)
        self.start_urls = [url]
        self.competitor_id = competitor_id
        self.max_posts = max_posts

        # Parse domain
        parsed = urlparse(url)
        self.allowed_domains = (
            [d.replace('www.', '') for d in allowed_domains]
            if allowed_domains
            else [parsed.netloc.replace('www.', '')]
        )

    def parse(self, response):
        """Parse blog archive/feed page"""

        # Extract blog post links
        blog_links = response.css(
            'article a::attr(href), .post a::attr(href), '
            '[class*="blog"] a::attr(href), h2 a::attr(href)'
        ).getall()

        if self.max_posts:
            blog_links = blog_links[: self.max_posts]

        # Follow links to individual posts
        for link in blog_links:
            yield response.follow(link, callback=self.parse_post)

    def parse_post(self, response):
        """Parse individual blog post"""

        content = trafilatura.extract(response.text)

        if not content or len(content) < 100:
            return

        metadata = trafilatura.extract_metadata(response.text)

        yield {
            'competitor_id': self.competitor_id,
            'url': response.url,
            'title': metadata.title if metadata else response.css('title::text').get(),
            'content': content,
            'content_type': 'blog_post',
            'author': metadata.author if metadata else None,
            'published_date': metadata.date if metadata else None,
            'word_count': len(content.split()),
            'scraped_at': datetime.utcnow().isoformat(),
        }
