# Scrapy Pipelines
from .validation import ValidationPipeline
from .cleaning import CleaningPipeline
from .postgres import PostgreSQLPipeline
from .duplicates import DuplicatesPipeline

__all__ = [
    'ValidationPipeline',
    'CleaningPipeline',
    'PostgreSQLPipeline',
    'DuplicatesPipeline',
]
