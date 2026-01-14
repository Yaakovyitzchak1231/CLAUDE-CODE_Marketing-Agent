"""
PostgreSQL Pipeline
Stores scraped data in PostgreSQL database
"""

import psycopg2
from psycopg2.extras import Json
from psycopg2.pool import ThreadedConnectionPool
from scrapy.exceptions import DropItem
import structlog
import os

logger = structlog.get_logger()


class PostgreSQLPipeline:
    """
    PostgreSQL storage pipeline

    Stores scraped items in database with deduplication
    """

    def __init__(self):
        self.pool = None

    @classmethod
    def from_crawler(cls, crawler):
        """Create pipeline from crawler"""
        return cls()

    def open_spider(self, spider):
        """Initialize database connection pool"""

        database_url = os.getenv(
            'DATABASE_URL',
            'postgresql://n8n:n8npassword@postgres:5432/marketing'
        )

        logger.info("initializing_postgres_connection_pool")

        try:
            self.pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=database_url
            )

            # Create tables if they don't exist
            self._create_tables()

            logger.info("postgres_pool_initialized")

        except Exception as e:
            logger.error("postgres_pool_error", error=str(e))
            raise

    def close_spider(self, spider):
        """Close database connection pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("postgres_pool_closed")

    def process_item(self, item, spider):
        """Store item in database"""

        conn = None
        try:
            # Get connection from pool
            conn = self.pool.getconn()
            cursor = conn.cursor()

            # Determine table and query based on content type
            content_type = item.get('content_type')

            if content_type == 'blog_post':
                self._insert_blog_post(cursor, item)
            elif content_type == 'pricing':
                self._insert_pricing(cursor, item)
            elif content_type == 'product':
                self._insert_product(cursor, item)
            else:
                self._insert_page(cursor, item)

            # Commit transaction
            conn.commit()

            logger.info(
                "item_stored",
                url=item.get('url'),
                content_type=content_type
            )

            return item

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error("postgres_insert_error", error=str(e), url=item.get('url'))
            raise DropItem(f"Database error: {str(e)}")

        finally:
            if conn:
                self.pool.putconn(conn)

    def _create_tables(self):
        """Create database tables if they don't exist"""

        conn = self.pool.getconn()
        cursor = conn.cursor()

        # Competitor pages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitor_pages (
                id SERIAL PRIMARY KEY,
                competitor_id INTEGER NOT NULL,
                url TEXT NOT NULL UNIQUE,
                title TEXT,
                content TEXT,
                content_type VARCHAR(50),
                word_count INTEGER,
                links_count INTEGER,
                images_count INTEGER,
                meta_description TEXT,
                h1_tags JSONB,
                h2_tags JSONB,
                scraped_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT fk_competitor FOREIGN KEY (competitor_id)
                    REFERENCES competitors(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_competitor_pages_competitor_id
                ON competitor_pages(competitor_id);
            CREATE INDEX IF NOT EXISTS idx_competitor_pages_url
                ON competitor_pages(url);
            CREATE INDEX IF NOT EXISTS idx_competitor_pages_scraped_at
                ON competitor_pages(scraped_at);
        """)

        # Blog posts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitor_blog_posts (
                id SERIAL PRIMARY KEY,
                competitor_id INTEGER NOT NULL,
                url TEXT NOT NULL UNIQUE,
                title TEXT,
                content TEXT,
                author TEXT,
                published_date DATE,
                categories JSONB,
                word_count INTEGER,
                reading_time NUMERIC,
                images_count INTEGER,
                meta_description TEXT,
                meta_keywords TEXT,
                scraped_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT fk_competitor FOREIGN KEY (competitor_id)
                    REFERENCES competitors(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_blog_posts_competitor_id
                ON competitor_blog_posts(competitor_id);
            CREATE INDEX IF NOT EXISTS idx_blog_posts_published_date
                ON competitor_blog_posts(published_date);
        """)

        # Pricing table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitor_pricing (
                id SERIAL PRIMARY KEY,
                competitor_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                pricing_tiers JSONB,
                scraped_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT fk_competitor FOREIGN KEY (competitor_id)
                    REFERENCES competitors(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_pricing_competitor_id
                ON competitor_pricing(competitor_id);
        """)

        # Products table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitor_products (
                id SERIAL PRIMARY KEY,
                competitor_id INTEGER NOT NULL,
                url TEXT NOT NULL UNIQUE,
                title TEXT,
                content TEXT,
                price TEXT,
                features JSONB,
                images JSONB,
                scraped_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT fk_competitor FOREIGN KEY (competitor_id)
                    REFERENCES competitors(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_products_competitor_id
                ON competitor_products(competitor_id);
        """)

        conn.commit()
        self.pool.putconn(conn)

        logger.info("database_tables_created")

    def _insert_page(self, cursor, item):
        """Insert generic page"""

        cursor.execute("""
            INSERT INTO competitor_pages (
                competitor_id, url, title, content, content_type,
                word_count, links_count, images_count,
                meta_description, h1_tags, h2_tags, scraped_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                word_count = EXCLUDED.word_count,
                links_count = EXCLUDED.links_count,
                images_count = EXCLUDED.images_count,
                meta_description = EXCLUDED.meta_description,
                h1_tags = EXCLUDED.h1_tags,
                h2_tags = EXCLUDED.h2_tags,
                scraped_at = EXCLUDED.scraped_at
        """, (
            item['competitor_id'],
            item['url'],
            item.get('title'),
            item.get('content'),
            item['content_type'],
            item.get('word_count'),
            item.get('links_count'),
            item.get('images_count'),
            item.get('meta_description'),
            Json(item.get('h1_tags', [])),
            Json(item.get('h2_tags', [])),
            item['scraped_at']
        ))

    def _insert_blog_post(self, cursor, item):
        """Insert blog post"""

        cursor.execute("""
            INSERT INTO competitor_blog_posts (
                competitor_id, url, title, content, author,
                published_date, categories, word_count, reading_time,
                images_count, meta_description, meta_keywords, scraped_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                author = EXCLUDED.author,
                published_date = EXCLUDED.published_date,
                categories = EXCLUDED.categories,
                word_count = EXCLUDED.word_count,
                reading_time = EXCLUDED.reading_time,
                images_count = EXCLUDED.images_count,
                meta_description = EXCLUDED.meta_description,
                meta_keywords = EXCLUDED.meta_keywords,
                scraped_at = EXCLUDED.scraped_at
        """, (
            item['competitor_id'],
            item['url'],
            item.get('title'),
            item.get('content'),
            item.get('author'),
            item.get('published_date'),
            Json(item.get('categories', [])),
            item.get('word_count'),
            item.get('reading_time'),
            item.get('images_count'),
            item.get('meta_description'),
            item.get('meta_keywords'),
            item['scraped_at']
        ))

    def _insert_pricing(self, cursor, item):
        """Insert pricing data"""

        cursor.execute("""
            INSERT INTO competitor_pricing (
                competitor_id, url, title, pricing_tiers, scraped_at
            ) VALUES (%s, %s, %s, %s, %s)
        """, (
            item['competitor_id'],
            item['url'],
            item.get('title'),
            Json(item.get('pricing_tiers', [])),
            item['scraped_at']
        ))

    def _insert_product(self, cursor, item):
        """Insert product data"""

        cursor.execute("""
            INSERT INTO competitor_products (
                competitor_id, url, title, content, price,
                features, images, scraped_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                price = EXCLUDED.price,
                features = EXCLUDED.features,
                images = EXCLUDED.images,
                scraped_at = EXCLUDED.scraped_at
        """, (
            item['competitor_id'],
            item['url'],
            item.get('title'),
            item.get('content'),
            item.get('price'),
            Json(item.get('features', [])),
            Json(item.get('images', [])),
            item['scraped_at']
        ))
