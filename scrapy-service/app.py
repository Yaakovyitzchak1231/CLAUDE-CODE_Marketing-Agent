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

# Job tracking
jobs = {}


# === Pydantic Models ===

class ScrapeRequest(BaseModel):
    """Request to scrape a competitor website"""
    competitor_id: int = Field(..., description="Database ID of the competitor")
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
    competitor_id: int = Field(..., description="Database ID of the competitor")
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
    """
    try:
        # Update job status
        jobs[job_id]["status"] = "running"
        jobs[job_id]["started_at"] = datetime.now()

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
            jobs[job_id]["items_scraped"] = len(items_scraped)

        # Configure crawler
        process.crawl(spider_class, **kwargs)

        # Connect signals
        from scrapy import signals
        for crawler in process.crawlers:
            crawler.signals.connect(item_scraped, signal=signals.item_scraped)

        # Start crawling (blocking)
        process.start()

        # Update job status on completion
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["completed_at"] = datetime.now()
        jobs[job_id]["items_scraped"] = len(items_scraped)

        logger.info(
            "spider_completed",
            job_id=job_id,
            items_count=len(items_scraped)
        )

    except Exception as e:
        # Update job status on error
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["completed_at"] = datetime.now()
        jobs[job_id]["errors"].append(str(e))

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
        "active_jobs": len([j for j in jobs.values() if j["status"] == "running"])
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

    # Initialize job tracking
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "spider": "CompetitorSpider",
        "competitor_id": request.competitor_id,
        "start_url": str(request.start_url),
        "started_at": None,
        "completed_at": None,
        "items_scraped": 0,
        "errors": []
    }

    # Start spider in background
    background_tasks.add_task(
        start_spider_async,
        CompetitorSpider,
        job_id,
        competitor_id=request.competitor_id,
        start_urls=[str(request.start_url)],
        allowed_domains=allowed_domains,
        max_depth=request.max_depth,
        max_pages=request.max_pages,
        content_types=request.content_types or ['page', 'blog_post', 'pricing', 'product']
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

    # Initialize job tracking
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "spider": "BlogMonitorSpider",
        "competitor_id": request.competitor_id,
        "blog_url": str(request.blog_url),
        "started_at": None,
        "completed_at": None,
        "items_scraped": 0,
        "errors": []
    }

    # Start spider in background
    background_tasks.add_task(
        start_spider_async,
        BlogMonitorSpider,
        job_id,
        competitor_id=request.competitor_id,
        start_urls=[str(request.blog_url)],
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
async def get_job_status(job_id: str):
    """
    Get status of scraping job

    Returns current status, progress, and any errors.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        started_at=job["started_at"] or datetime.now(),
        completed_at=job["completed_at"],
        items_scraped=job["items_scraped"],
        errors=job["errors"]
    )


@app.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50
):
    """
    List all scraping jobs

    Optionally filter by status: pending, running, completed, failed
    """
    filtered_jobs = jobs.values()

    # Filter by status if provided
    if status:
        filtered_jobs = [j for j in filtered_jobs if j["status"] == status]

    # Sort by started_at (most recent first)
    sorted_jobs = sorted(
        filtered_jobs,
        key=lambda x: x["started_at"] or datetime.min,
        reverse=True
    )

    # Limit results
    return {
        "total": len(sorted_jobs),
        "limit": limit,
        "jobs": sorted_jobs[:limit]
    }


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete job from tracking

    Note: Does not stop running jobs, only removes from history.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs.pop(job_id)

    logger.info(
        "job_deleted",
        job_id=job_id,
        status=job["status"]
    )

    return {
        "message": f"Job {job_id} deleted",
        "status": job["status"]
    }


@app.get("/stats")
async def get_stats():
    """
    Get scraping service statistics

    Returns counts by job status and overall metrics.
    """
    total_jobs = len(jobs)
    status_counts = {}

    for job in jobs.values():
        status = job["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    total_items = sum(j["items_scraped"] for j in jobs.values())

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
