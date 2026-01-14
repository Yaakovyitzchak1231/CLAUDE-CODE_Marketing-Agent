"""
Duplicates Pipeline
Filters out duplicate items based on URL fingerprints
"""

from scrapy.exceptions import DropItem
import hashlib
import structlog

logger = structlog.get_logger()


class DuplicatesPipeline:
    """
    Filters duplicate items using URL fingerprints

    Uses in-memory set for session-based deduplication.
    Database-level deduplication handled by PostgreSQL UNIQUE constraints.
    """

    def __init__(self):
        self.seen_urls = set()

    def process_item(self, item, spider):
        """Check if item URL has been seen before"""

        url = item.get('url')

        if not url:
            raise DropItem("Item missing URL")

        # Create fingerprint from URL
        fingerprint = self._get_fingerprint(url)

        # Check if already seen in this session
        if fingerprint in self.seen_urls:
            logger.warning(
                "duplicate_item_dropped",
                url=url,
                fingerprint=fingerprint
            )
            raise DropItem(f"Duplicate item found: {url}")

        # Mark as seen
        self.seen_urls.add(fingerprint)

        logger.debug(
            "item_passed_duplicate_check",
            url=url,
            fingerprint=fingerprint
        )

        return item

    def _get_fingerprint(self, url: str) -> str:
        """Generate URL fingerprint using SHA256"""

        # Normalize URL for fingerprinting
        normalized_url = url.lower().strip()

        # Remove common variations
        normalized_url = normalized_url.rstrip('/')
        normalized_url = normalized_url.replace('www.', '')
        normalized_url = normalized_url.split('#')[0]  # Remove fragment
        normalized_url = normalized_url.split('?')[0]  # Remove query params

        # Generate hash
        fingerprint = hashlib.sha256(normalized_url.encode('utf-8')).hexdigest()

        return fingerprint

    def close_spider(self, spider):
        """Log statistics when spider closes"""

        logger.info(
            "duplicates_pipeline_closed",
            unique_urls_seen=len(self.seen_urls)
        )
