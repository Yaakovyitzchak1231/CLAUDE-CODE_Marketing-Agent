# Scrapy Service

Web scraping service for competitor monitoring and content extraction. Built with Scrapy and FastAPI.

## Features

- **Competitor Website Scraping**: Full website crawling with configurable depth
- **Blog Monitoring**: Lightweight spider for blog feed monitoring
- **Content Type Detection**: Automatic detection of blog posts, pricing pages, products
- **Respectful Crawling**: robots.txt compliance, rate limiting, user agent rotation
- **Data Pipelines**: Validation → Cleaning → Deduplication → PostgreSQL storage
- **REST API**: FastAPI endpoints for triggering scraping jobs
- **Job Tracking**: Monitor scraping progress and status
- **Error Handling**: Comprehensive error handling with retry logic

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FastAPI Server                     │
│  (Job Management & REST API)                        │
└─────────────────┬───────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼────────┐   ┌──────▼──────────┐
│ Competitor     │   │  Blog Monitor   │
│ Spider         │   │  Spider         │
│ (Full Crawl)   │   │  (Feed Only)    │
└───────┬────────┘   └──────┬──────────┘
        │                   │
        └─────────┬─────────┘
                  │
        ┌─────────▼─────────────────────┐
        │      Pipeline Chain           │
        │  1. Validation                │
        │  2. Cleaning                  │
        │  3. PostgreSQL Storage        │
        │  4. Deduplication             │
        └─────────┬─────────────────────┘
                  │
        ┌─────────▼─────────┐
        │   PostgreSQL DB   │
        │ - Pages           │
        │ - Blog Posts      │
        │ - Pricing         │
        │ - Products        │
        └───────────────────┘
```

## API Endpoints

### Competitor Scraping

**POST /scrape/competitor**

Scrape a competitor website with configurable depth and content types.

Request:
```json
{
  "competitor_id": 1,
  "start_url": "https://competitor.com",
  "allowed_domains": ["competitor.com"],
  "max_depth": 2,
  "max_pages": 100,
  "content_types": ["page", "blog_post", "pricing", "product"]
}
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Scraping job started for competitor.com",
  "started_at": "2024-01-15T10:30:00Z"
}
```

### Blog Monitoring

**POST /scrape/blog**

Monitor competitor blog for new posts.

Request:
```json
{
  "competitor_id": 1,
  "blog_url": "https://competitor.com/blog",
  "max_posts": 20
}
```

### Job Status

**GET /jobs/{job_id}**

Get status of a scraping job.

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": null,
  "items_scraped": 45,
  "errors": []
}
```

### List Jobs

**GET /jobs?status=running&limit=50**

List all scraping jobs with optional filtering.

### Service Stats

**GET /stats**

Get scraping service statistics.

Response:
```json
{
  "total_jobs": 150,
  "status_counts": {
    "pending": 2,
    "running": 5,
    "completed": 140,
    "failed": 3
  },
  "total_items_scraped": 12500,
  "active_jobs": 5
}
```

## Spiders

### CompetitorSpider

Full website crawler using CrawlSpider with configurable rules.

**Features:**
- Configurable crawl depth (default: 2 levels)
- Page limit protection (default: 100 pages)
- Content type detection (blog, pricing, product, page)
- Metadata extraction (title, author, date, categories)
- Trafilatura for clean content extraction

**Usage:**
```bash
scrapy crawl competitor -a competitor_id=1 -a start_url=https://competitor.com
```

### BlogMonitorSpider

Lightweight spider for blog feed monitoring.

**Features:**
- Optimized for frequent monitoring
- Low crawl depth (blog feed only)
- Quick execution
- Blog post specific parsing

**Usage:**
```bash
scrapy crawl blog_monitor -a competitor_id=1 -a start_url=https://competitor.com/blog
```

## Pipelines

Scraped items pass through a chain of pipelines:

### 1. ValidationPipeline (Priority: 100)

Validates required fields and data types:
- Required fields: competitor_id, url, content_type, scraped_at
- URL format validation
- Content length validation (min 50 chars)
- Word count validation (min 10 words)

### 2. CleaningPipeline (Priority: 200)

Cleans and normalizes data:
- Remove extra whitespace
- Normalize URLs (remove utm params, fragments)
- Clean HTML entities
- Trim long content (50,000 char limit)
- Normalize dates to ISO format

### 3. PostgreSQLPipeline (Priority: 300)

Stores data in PostgreSQL:
- Connection pooling (1-10 connections)
- Four content type tables (pages, blog_posts, pricing, products)
- UNIQUE constraint on URLs
- ON CONFLICT DO UPDATE for deduplication
- JSONB fields for flexible data

### 4. DuplicatesPipeline (Priority: 400)

Session-based deduplication:
- URL fingerprinting (SHA256)
- In-memory seen URLs tracking
- Drops duplicate items within session

## Middlewares

### ErrorHandlerMiddleware

Handles HTTP errors gracefully:
- Logs all HTTP errors with details
- Custom handling for 404, 403, 429, 5xx
- Stats tracking per error type
- Integration with retry middleware

### RateLimitMiddleware

Per-domain rate limiting:
- Configurable delay per domain
- Prevents overwhelming target servers
- Works with AutoThrottle

### UserAgentRotatorMiddleware

Rotates user agents:
- 5 modern browser user agents
- Circular rotation per request
- Prevents detection

## Database Schema

### competitor_pages
```sql
id SERIAL PRIMARY KEY
competitor_id INTEGER (FK to competitors)
url TEXT UNIQUE
title TEXT
content TEXT
content_type VARCHAR(50)
word_count INTEGER
links_count INTEGER
images_count INTEGER
meta_description TEXT
h1_tags JSONB
h2_tags JSONB
scraped_at TIMESTAMP
created_at TIMESTAMP
```

### competitor_blog_posts
```sql
id SERIAL PRIMARY KEY
competitor_id INTEGER (FK to competitors)
url TEXT UNIQUE
title TEXT
content TEXT
author TEXT
published_date DATE
categories JSONB
word_count INTEGER
reading_time NUMERIC
images_count INTEGER
meta_description TEXT
meta_keywords TEXT
scraped_at TIMESTAMP
created_at TIMESTAMP
```

### competitor_pricing
```sql
id SERIAL PRIMARY KEY
competitor_id INTEGER (FK to competitors)
url TEXT
title TEXT
pricing_tiers JSONB
scraped_at TIMESTAMP
created_at TIMESTAMP
```

### competitor_products
```sql
id SERIAL PRIMARY KEY
competitor_id INTEGER (FK to competitors)
url TEXT UNIQUE
title TEXT
content TEXT
price TEXT
features JSONB
images JSONB
scraped_at TIMESTAMP
created_at TIMESTAMP
```

## Configuration

### Environment Variables

See `.env.example` for all configuration options.

Key settings:
- `PORT`: API server port (default: 8003)
- `DATABASE_URL`: PostgreSQL connection string
- `DOWNLOAD_DELAY`: Delay between requests (default: 1.0s)
- `MAX_DEPTH`: Maximum crawl depth (default: 3)
- `MAX_PAGES_PER_CRAWL`: Page limit per job (default: 100)

### Scrapy Settings

Located in `settings.py`:

**Respectful Crawling:**
- `ROBOTSTXT_OBEY = True`: Respect robots.txt
- `DOWNLOAD_DELAY = 1.0`: 1 second delay
- `CONCURRENT_REQUESTS_PER_DOMAIN = 8`: Limit concurrent requests

**AutoThrottle:**
- `AUTOTHROTTLE_ENABLED = True`: Automatic rate adjustment
- `AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0`: Target concurrency level

**Retry Logic:**
- `RETRY_TIMES = 3`: Retry failed requests 3 times
- `RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]`: Retry these codes

## Running the Service

### Docker (Recommended)

```bash
# Build image
docker build -t scrapy-service .

# Run container
docker run -p 8003:8003 --env-file .env scrapy-service
```

### Docker Compose

Already configured in `docker-compose.yml`:

```bash
docker-compose up scrapy-service
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
python app.py

# Or use Scrapy directly
scrapy crawl competitor -a competitor_id=1 -a start_url=https://example.com
```

## Usage Examples

### 1. Scrape Competitor Website

```bash
curl -X POST http://localhost:8003/scrape/competitor \
  -H "Content-Type: application/json" \
  -d '{
    "competitor_id": 1,
    "start_url": "https://competitor.com",
    "max_depth": 2,
    "max_pages": 50
  }'
```

### 2. Monitor Blog

```bash
curl -X POST http://localhost:8003/scrape/blog \
  -H "Content-Type: application/json" \
  -d '{
    "competitor_id": 1,
    "blog_url": "https://competitor.com/blog",
    "max_posts": 10
  }'
```

### 3. Check Job Status

```bash
curl http://localhost:8003/jobs/550e8400-e29b-41d4-a716-446655440000
```

### 4. List Running Jobs

```bash
curl http://localhost:8003/jobs?status=running
```

## Integration with n8n

The Scrapy service is designed to be triggered by n8n workflows.

**Example n8n Workflow:**

1. **Webhook Trigger**: Receive competitor_id and URL
2. **HTTP Request**: POST to `/scrape/competitor`
3. **Wait for Completion**: Poll `/jobs/{job_id}` until status = "completed"
4. **Process Results**: Query PostgreSQL for scraped data
5. **Trigger Analysis**: Send data to LangChain agents

## Monitoring

### Logs

Structured logging with `structlog`:

```python
logger.info("spider_started", competitor_id=1, start_url="https://example.com")
logger.warning("http_404_not_found", url="https://example.com/missing")
logger.error("spider_failed", job_id="uuid", error="Connection timeout")
```

### Metrics

Track scraping metrics via `/stats` endpoint:
- Total jobs
- Jobs by status
- Total items scraped
- Active jobs

### Health Check

Docker health check via root endpoint:

```bash
curl http://localhost:8003/
```

Response:
```json
{
  "service": "scrapy-service",
  "status": "running",
  "version": "1.0.0",
  "active_jobs": 3
}
```

## Best Practices

### Respectful Scraping

1. **Always respect robots.txt**: Never disable `ROBOTSTXT_OBEY`
2. **Use appropriate delays**: Minimum 1 second between requests
3. **Limit concurrent requests**: Max 8 per domain
4. **Set realistic user agent**: Identify your bot
5. **Handle rate limits**: Auto-throttle and backoff on 429 errors

### Error Handling

1. **Validate inputs**: Check URLs and IDs before scraping
2. **Handle 404s gracefully**: Don't retry missing pages
3. **Respect 403/401**: Stop scraping if blocked
4. **Retry 5xx errors**: Server issues may be temporary
5. **Log all errors**: Track failures for debugging

### Performance

1. **Use connection pooling**: PostgreSQL ThreadedConnectionPool
2. **Enable caching**: Redis HTTP cache for repeated requests
3. **Limit page count**: Prevent runaway crawls
4. **Use background tasks**: Don't block API responses
5. **Monitor memory**: Large crawls can consume significant RAM

### Security

1. **Non-root user**: Container runs as user 'scrapy'
2. **Environment variables**: Never hardcode credentials
3. **Input validation**: Pydantic models validate all requests
4. **SQL injection**: Use parameterized queries only
5. **Rate limiting**: Prevent abuse of API endpoints

## Troubleshooting

### Spider Not Starting

**Issue**: Job status stuck at "pending"

**Solutions:**
- Check logs for Twisted reactor errors
- Verify database connection
- Ensure multiprocessing is working
- Check for port conflicts

### Items Not Being Saved

**Issue**: Spider completes but no data in database

**Solutions:**
- Check pipeline priority order
- Verify DATABASE_URL is correct
- Check PostgreSQL logs for errors
- Ensure tables exist (created automatically)
- Review validation pipeline logs

### Getting Blocked

**Issue**: HTTP 403 or 429 errors

**Solutions:**
- Increase DOWNLOAD_DELAY
- Enable AUTOTHROTTLE
- Rotate user agents
- Check robots.txt compliance
- Consider using proxies

### Memory Issues

**Issue**: Container runs out of memory

**Solutions:**
- Reduce MAX_PAGES_PER_CRAWL
- Limit concurrent requests
- Enable HTTP caching
- Increase Docker memory limit
- Process large crawls in batches

## Dependencies

Core dependencies:
- `scrapy>=2.11.0`: Web scraping framework
- `fastapi>=0.109.0`: REST API framework
- `uvicorn>=0.27.0`: ASGI server
- `psycopg2-binary>=2.9.9`: PostgreSQL adapter
- `trafilatura>=1.6.3`: Content extraction
- `structlog>=24.1.0`: Structured logging
- `python-dateutil>=2.8.2`: Date parsing
- `scrapy-user-agents>=0.1.1`: User agent rotation

See `requirements.txt` for complete list.

## License

This service is part of the B2B Marketing Automation Platform.

## Support

For issues or questions:
1. Check logs: `docker logs scrapy-service`
2. Review API docs: `http://localhost:8003/docs`
3. Check database: Ensure tables exist and have correct schema
4. Test spiders: Run Scrapy directly to isolate issues
