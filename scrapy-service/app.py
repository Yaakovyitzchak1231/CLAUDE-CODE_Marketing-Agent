"""
Scrapy Service API
FastAPI server exposing Scrapy spiders via REST endpoints
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import structlog
import uuid
import os
import json
import redis

# Scrapy imports
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer
from billiard import Process
import multiprocessing

# Import spiders
from spiders.competitor_spider import CompetitorSpider, BlogMonitorSpider

logger = structlog.get_logger()

app = FastAPI(
    title="Scrapy Service API",
    description="Web scraping service for competitor monitoring and content extraction",
    version="1.0.0"
)

# Redis-based job tracking (persists across processes)
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True
)

JOB_KEY_PREFIX = "scrapy_job:"
JOB_LIST_KEY = "scrapy_jobs"


def update_job_status(job_id: str, job_data: Dict[str, Any]) -> None:
    """Update job status in Redis"""
    # Convert datetime objects to ISO strings for JSON serialization
    serialized = {}
    for key, value in job_data.items():
        if isinstance(value, datetime):
            serialized[key] = value.isoformat()
        elif isinstance(value, list):
            serialized[key] = json.dumps(value)
        else:
            serialized[key] = value

    redis_client.hset(f"{JOB_KEY_PREFIX}{job_id}", mapping=serialized)
    # Add to job list with score as timestamp for ordering
    redis_client.zadd(JOB_LIST_KEY, {job_id: datetime.now().timestamp()})


def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job status from Redis"""
    data = redis_client.hgetall(f"{JOB_KEY_PREFIX}{job_id}")
    if not data:
        return None

    # Deserialize
    result = {}
    for key, value in data.items():
        if key in ('started_at', 'completed_at') and value and value != 'None':
            try:
                result[key] = datetime.fromisoformat(value)
            except (ValueError, TypeError):
                result[key] = None
        elif key == 'errors':
            try:
                result[key] = json.loads(value) if value else []
            except json.JSONDecodeError:
                result[key] = []
        elif key == 'items_scraped':
            result[key] = int(value) if value else 0
        else:
            result[key] = value if value != 'None' else None

    return result


def list_all_jobs(status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """List all jobs from Redis, optionally filtered by status"""
    # Get all job IDs sorted by timestamp (most recent first)
    job_ids = redis_client.zrevrange(JOB_LIST_KEY, 0, -1)

    jobs = []
    for job_id in job_ids:
        job_data = get_job_status(job_id)
        if job_data:
            if status_filter is None or job_data.get("status") == status_filter:
                jobs.append(job_data)
            if len(jobs) >= limit:
                break

    return jobs


def delete_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Delete job from Redis"""
    job_data = get_job_status(job_id)
    if job_data:
        redis_client.delete(f"{JOB_KEY_PREFIX}{job_id}")
        redis_client.zrem(JOB_LIST_KEY, job_id)
    return job_data


def count_active_jobs() -> int:
    """Count currently running jobs"""
    job_ids = redis_client.zrange(JOB_LIST_KEY, 0, -1)
    count = 0
    for job_id in job_ids:
        status = redis_client.hget(f"{JOB_KEY_PREFIX}{job_id}", "status")
        if status == "running":
            count += 1
    return count


# === Pydantic Models ===

class ScrapeRequest(BaseModel):
    """Request to scrape a competitor website"""
    competitor_id: str = Field(..., description="Competitor UUID (competitors.id)")
    start_url: HttpUrl = Field(..., description="Starting URL to scrape")
    allowed_domains: Optional[List[str]] = Field(
        None,
        description="List of allowed domains (default: extracted from start_url)"
    )
    max_depth: int = Field(2, ge=0, le=5, description="Maximum crawl depth")
    max_pages: int = Field(100, ge=1, le=1000, description="Maximum pages to scrape")
    content_types: Optional[List[str]] = Field(
        None,
        description="Content types to extract (blog_post, pricing, product, page)"
    )


class BlogMonitorRequest(BaseModel):
    """Request to monitor competitor blog"""
    competitor_id: str = Field(..., description="Competitor UUID (competitors.id)")
    blog_url: HttpUrl = Field(..., description="Blog feed URL")
    max_posts: int = Field(20, ge=1, le=100, description="Maximum posts to scrape")


class JobResponse(BaseModel):
    """Response for scraping job"""
    job_id: str
    status: str
    message: str
    started_at: datetime


class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    items_scraped: int
    errors: List[str]


# === Helper Functions ===

def run_spider_in_process(spider_class, job_id: str, **kwargs):
    """
    Run spider in separate process to avoid reactor issues

    Scrapy's Twisted reactor can only be started once per process
    Uses Redis for job tracking to persist across process boundaries.
    """
    # Create Redis client for this process
    process_redis = redis.Redis(
        host=os.getenv('REDIS_HOST', 'redis'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        decode_responses=True
    )

    def update_process_job(updates: Dict[str, Any]) -> None:
        """Update job in Redis from within process"""
        serialized = {}
        for key, value in updates.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, list):
                serialized[key] = json.dumps(value)
            else:
                serialized[key] = value
        process_redis.hset(f"{JOB_KEY_PREFIX}{job_id}", mapping=serialized)

    try:
        # Update job status
        update_process_job({
            "status": "running",
            "started_at": datetime.now()
        })

        # Get project settings
        settings = get_project_settings()

        # Override settings if needed
        settings.set('LOG_LEVEL', 'INFO')

        # Create crawler process
        process = CrawlerProcess(settings)

        # Track items
        items_scraped = []

        def item_scraped(item, response, spider):
            items_scraped.append(item)
            update_process_job({"items_scraped": len(items_scraped)})

        # Configure crawler
        process.crawl(spider_class, **kwargs)

        # Connect signals
        from scrapy import signals
        for crawler in process.crawlers:
            crawler.signals.connect(item_scraped, signal=signals.item_scraped)

        # Start crawling (blocking)
        process.start()

        # Update job status on completion
        update_process_job({
            "status": "completed",
            "completed_at": datetime.now(),
            "items_scraped": len(items_scraped)
        })

        logger.info(
            "spider_completed",
            job_id=job_id,
            items_count=len(items_scraped)
        )

    except Exception as e:
        # Get current errors from Redis
        current_errors = process_redis.hget(f"{JOB_KEY_PREFIX}{job_id}", "errors")
        try:
            errors = json.loads(current_errors) if current_errors else []
        except json.JSONDecodeError:
            errors = []
        errors.append(str(e))

        # Update job status on error
        update_process_job({
            "status": "failed",
            "completed_at": datetime.now(),
            "errors": errors
        })

        logger.error(
            "spider_failed",
            job_id=job_id,
            error=str(e)
        )


async def start_spider_async(spider_class, job_id: str, **kwargs):
    """
    Start spider in background process

    Uses multiprocessing to avoid Twisted reactor conflicts
    """
    # Create process
    process = Process(
        target=run_spider_in_process,
        args=(spider_class, job_id),
        kwargs=kwargs
    )

    # Start process
    process.start()

    logger.info(
        "spider_started_async",
        job_id=job_id,
        spider=spider_class.__name__,
        process_id=process.pid
    )


# === API Endpoints ===

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "scrapy-service",
        "status": "running",
        "version": "1.0.0",
        "active_jobs": count_active_jobs()
    }


@app.post("/scrape/competitor", response_model=JobResponse)
async def scrape_competitor(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
    Scrape competitor website

    Crawls website starting from start_url, extracting content
    based on content types and respecting crawl depth limits.
    """
    # Generate job ID
    job_id = str(uuid.uuid4())

    # Extract domain from URL
    from urllib.parse import urlparse
    parsed_url = urlparse(str(request.start_url))
    domain = parsed_url.netloc

    # Set allowed domains
    allowed_domains = request.allowed_domains or [domain]

    # Map requested content types to the spider's scrape_type
    content_types = request.content_types or ['page', 'blog_post', 'pricing', 'product']
    if 'pricing' in content_types:
        scrape_type = 'pricing'
    elif 'product' in content_types:
        scrape_type = 'products'
    elif 'blog_post' in content_types:
        scrape_type = 'blog'
    else:
        scrape_type = 'full'

    # Initialize job tracking in Redis
    update_job_status(job_id, {
        "job_id": job_id,
        "status": "pending",
        "spider": "CompetitorSpider",
        "competitor_id": request.competitor_id,
        "start_url": str(request.start_url),
        "started_at": None,
        "completed_at": None,
        "items_scraped": 0,
        "errors": []
    })

    # Start spider in background
    background_tasks.add_task(
        start_spider_async,
        CompetitorSpider,
        job_id,
        url=str(request.start_url),
        competitor_id=request.competitor_id,
        scrape_type=scrape_type,
        allowed_domains=allowed_domains,
        max_depth=request.max_depth,
        max_pages=request.max_pages
    )

    logger.info(
        "scrape_job_created",
        job_id=job_id,
        competitor_id=request.competitor_id,
        start_url=str(request.start_url)
    )

    return JobResponse(
        job_id=job_id,
        status="pending",
        message=f"Scraping job started for {domain}",
        started_at=datetime.now()
    )


@app.post("/scrape/blog", response_model=JobResponse)
async def scrape_blog(
    request: BlogMonitorRequest,
    background_tasks: BackgroundTasks
):
    """
    Monitor competitor blog

    Lightweight spider for scraping blog posts from feed URLs.
    Optimized for frequent monitoring and updates.
    """
    # Generate job ID
    job_id = str(uuid.uuid4())

    # Extract domain
    from urllib.parse import urlparse
    parsed_url = urlparse(str(request.blog_url))
    domain = parsed_url.netloc

    # Initialize job tracking in Redis
    update_job_status(job_id, {
        "job_id": job_id,
        "status": "pending",
        "spider": "BlogMonitorSpider",
        "competitor_id": request.competitor_id,
        "blog_url": str(request.blog_url),
        "started_at": None,
        "completed_at": None,
        "items_scraped": 0,
        "errors": []
    })

    # Start spider in background
    background_tasks.add_task(
        start_spider_async,
        BlogMonitorSpider,
        job_id,
        url=str(request.blog_url),
        competitor_id=request.competitor_id,
        allowed_domains=[domain],
        max_posts=request.max_posts
    )

    logger.info(
        "blog_monitor_job_created",
        job_id=job_id,
        competitor_id=request.competitor_id,
        blog_url=str(request.blog_url)
    )

    return JobResponse(
        job_id=job_id,
        status="pending",
        message=f"Blog monitoring started for {domain}",
        started_at=datetime.now()
    )


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status_endpoint(job_id: str):
    """
    Get status of scraping job

    Returns current status, progress, and any errors.
    """
    job = get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.get("job_id", job_id),
        status=job.get("status", "unknown"),
        started_at=job.get("started_at") or datetime.now(),
        completed_at=job.get("completed_at"),
        items_scraped=job.get("items_scraped", 0),
        errors=job.get("errors", [])
    )


@app.get("/jobs")
async def list_jobs_endpoint(
    status: Optional[str] = None,
    limit: int = 50
):
    """
    List all scraping jobs

    Optionally filter by status: pending, running, completed, failed
    """
    jobs_list = list_all_jobs(status_filter=status, limit=limit)

    return {
        "total": len(jobs_list),
        "limit": limit,
        "jobs": jobs_list
    }


@app.delete("/jobs/{job_id}")
async def delete_job_endpoint(job_id: str):
    """
    Delete job from tracking

    Note: Does not stop running jobs, only removes from history.
    """
    job = delete_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    logger.info(
        "job_deleted",
        job_id=job_id,
        status=job.get("status")
    )

    return {
        "message": f"Job {job_id} deleted",
        "status": job.get("status")
    }


@app.get("/stats")
async def get_stats():
    """
    Get scraping service statistics

    Returns counts by job status and overall metrics.
    """
    all_jobs = list_all_jobs(limit=1000)  # Get all jobs for stats
    total_jobs = len(all_jobs)
    status_counts = {}

    for job in all_jobs:
        status = job.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    total_items = sum(j.get("items_scraped", 0) for j in all_jobs)

    return {
        "total_jobs": total_jobs,
        "status_counts": status_counts,
        "total_items_scraped": total_items,
        "active_jobs": status_counts.get("running", 0)
    }


if __name__ == "__main__":
    import uvicorn

    # Get port from environment
    port = int(os.getenv("PORT", 8003))

    logger.info(
        "starting_scrapy_service",
        port=port
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
