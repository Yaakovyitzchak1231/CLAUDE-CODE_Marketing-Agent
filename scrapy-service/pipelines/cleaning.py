"""
Cleaning Pipeline
Cleans and normalizes scraped data
"""

import re
from datetime import datetime
import structlog

logger = structlog.get_logger()


class CleaningPipeline:
    """
    Cleans and normalizes scraped items

    Operations:
    - Remove extra whitespace
    - Normalize URLs
    - Clean HTML entities
    - Trim long text fields
    - Normalize dates
    """

    def process_item(self, item, spider):
        """Clean and normalize item"""

        # Clean title
        if 'title' in item and item['title']:
            item['title'] = self._clean_text(item['title'])

        # Clean content
        if 'content' in item and item['content']:
            item['content'] = self._clean_content(item['content'])

        # Clean meta description
        if 'meta_description' in item and item['meta_description']:
            item['meta_description'] = self._clean_text(item['meta_description'])

        # Clean author
        if 'author' in item and item['author']:
            item['author'] = self._clean_text(item['author'])

        # Normalize URL
        if 'url' in item:
            item['url'] = self._normalize_url(item['url'])

        # Clean lists (categories, features, etc.)
        for field in ['categories', 'features', 'h1_tags', 'h2_tags']:
            if field in item and isinstance(item[field], list):
                item[field] = [self._clean_text(text) for text in item[field] if text]

        # Normalize dates
        if 'published_date' in item and item['published_date']:
            item['published_date'] = self._normalize_date(item['published_date'])

        logger.info("item_cleaned", url=item.get('url'))

        return item

    def _clean_text(self, text: str) -> str:
        """Clean text field"""
        if not text:
            return ''

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Trim
        text = text.strip()

        # Remove control characters
        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)

        return text

    def _clean_content(self, content: str) -> str:
        """Clean content field"""
        # Clean text
        content = self._clean_text(content)

        # Limit length (store first 50,000 characters)
        max_length = 50000
        if len(content) > max_length:
            content = content[:max_length] + '...'
            logger.warning(f"Content truncated to {max_length} characters")

        return content

    def _normalize_url(self, url: str) -> str:
        """Normalize URL"""
        # Remove trailing slash
        url = url.rstrip('/')

        # Remove fragment
        url = url.split('#')[0]

        # Remove utm parameters
        url = re.sub(r'[?&]utm_[^&]*', '', url)

        # Clean up query string
        url = url.replace('?&', '?').rstrip('?&')

        return url

    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string"""
        if not date_str:
            return None

        # If already ISO format, return as-is
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            return date_str[:10]  # Return just date part

        # Try to parse various formats
        from dateutil import parser

        try:
            dt = parser.parse(date_str)
            return dt.date().isoformat()
        except:
            logger.warning(f"Could not parse date: {date_str}")
            return None
