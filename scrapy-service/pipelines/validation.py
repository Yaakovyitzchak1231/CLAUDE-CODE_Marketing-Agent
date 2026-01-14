"""
Validation Pipeline
Validates scraped items before processing
"""

from scrapy.exceptions import DropItem
import structlog

logger = structlog.get_logger()


class ValidationPipeline:
    """
    Validates scraped items

    Checks:
    - Required fields present
    - Data types correct
    - Content length sufficient
    - URL format valid
    """

    def process_item(self, item, spider):
        """Validate item"""

        # Check required fields
        required_fields = ['competitor_id', 'url', 'content_type', 'scraped_at']

        for field in required_fields:
            if field not in item:
                raise DropItem(f"Missing required field: {field} in {item.get('url', 'unknown')}")

        # Validate competitor_id
        if not isinstance(item.get('competitor_id'), int):
            raise DropItem(f"Invalid competitor_id type: {type(item['competitor_id'])}")

        # Validate URL
        url = item.get('url', '')
        if not url.startswith('http'):
            raise DropItem(f"Invalid URL format: {url}")

        # Validate content (if present)
        if 'content' in item:
            content = item['content']

            if not content or not isinstance(content, str):
                raise DropItem(f"Invalid content in {url}")

            if len(content) < 50:
                raise DropItem(f"Content too short ({len(content)} chars) in {url}")

        # Validate word count
        if 'word_count' in item and item['word_count'] < 10:
            raise DropItem(f"Word count too low ({item['word_count']}) in {url}")

        logger.info(
            "item_validated",
            url=url,
            content_type=item['content_type']
        )

        return item
