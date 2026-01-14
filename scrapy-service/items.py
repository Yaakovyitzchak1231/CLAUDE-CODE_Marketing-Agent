"""
Scrapy Items - Data Structures for Scraped Content
Defines schemas for different types of scraped data
"""

import scrapy
from scrapy.item import Item, Field
from datetime import datetime


class CompetitorPage(Item):
    """Generic competitor page item"""

    competitor_id = Field()
    url = Field()
    title = Field()
    content = Field()
    content_type = Field()  # page, blog_post, product, pricing
    word_count = Field()
    links_count = Field()
    images_count = Field()
    scraped_at = Field()
    meta_description = Field()
    h1_tags = Field()
    h2_tags = Field()


class BlogPost(Item):
    """Blog post item"""

    competitor_id = Field()
    url = Field()
    title = Field()
    content = Field()
    content_type = Field()
    author = Field()
    published_date = Field()
    categories = Field()
    word_count = Field()
    reading_time = Field()
    images_count = Field()
    scraped_at = Field()
    meta_description = Field()
    meta_keywords = Field()


class PricingPage(Item):
    """Pricing page item"""

    competitor_id = Field()
    url = Field()
    title = Field()
    content_type = Field()
    pricing_tiers = Field()  # List of pricing tiers
    scraped_at = Field()


class ProductPage(Item):
    """Product page item"""

    competitor_id = Field()
    url = Field()
    title = Field()
    content = Field()
    content_type = Field()
    price = Field()
    features = Field()  # List of features
    images = Field()  # List of image URLs
    scraped_at = Field()
