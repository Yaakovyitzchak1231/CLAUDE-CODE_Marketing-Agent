# Playwright Browser Automation Service

Headless browser automation service built with Playwright and FastAPI. Provides REST API for rendering JavaScript pages, taking screenshots, executing custom scripts, and extracting content.

## Features

- **JavaScript Rendering**: Render Single Page Applications (React, Vue, Angular)
- **Screenshots**: Capture full page or viewport screenshots
- **Content Extraction**: Extract HTML, links, cookies, and custom data
- **Script Execution**: Run custom JavaScript in page context
- **Browser Management**: Efficient context pooling and lifecycle management
- **Headless Mode**: Optimized for server deployment
- **Multiple Browsers**: Support for Chromium, Firefox, and WebKit

## Quick Start

### Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Install Playwright browsers:**
```bash
playwright install chromium
```

3. **Run the service:**
```bash
python app.py
```

The API will be available at `http://localhost:8002`

### Docker Deployment

1. **Build Docker image:**
```bash
docker build -t playwright-service .
```

2. **Run container:**
```bash
docker run -p 8002:8002 playwright-service
```

## API Endpoints

### Health Check

**GET /**
```bash
curl http://localhost:8002/
```

**GET /health**
```bash
curl http://localhost:8002/health
```

### Render Page

**POST /render**

Render a JavaScript page and extract HTML content.

```bash
curl -X POST http://localhost:8002/render \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "wait_for": "networkidle",
    "timeout": 30000,
    "viewport_width": 1920,
    "viewport_height": 1080
  }'
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "final_url": "https://example.com",
  "title": "Example Domain",
  "html": "<!DOCTYPE html><html>...",
  "html_length": 1256,
  "status_code": 200,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Use Cases:**
- Scraping React/Vue/Angular applications
- Extracting dynamically loaded content
- Rendering pages with heavy JavaScript

### Take Screenshot

**POST /screenshot**

Capture PNG screenshot (base64 encoded).

```bash
curl -X POST http://localhost:8002/screenshot \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "full_page": false,
    "wait_for": "networkidle",
    "viewport_width": 1920,
    "viewport_height": 1080
  }'
```

**POST /screenshot/raw**

Capture PNG screenshot (raw bytes).

```bash
curl -X POST http://localhost:8002/screenshot/raw \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "full_page": true
  }' \
  --output screenshot.png
```

**Use Cases:**
- Visual regression testing
- Generating preview images
- Archiving page states

### Execute JavaScript

**POST /execute**

Execute custom JavaScript code on page.

```bash
curl -X POST http://localhost:8002/execute \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "script": "document.querySelectorAll(\"h1\").length"
  }'
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "result": 1,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Use Cases:**
- Extract specific data using custom selectors
- Interact with page elements
- Trigger dynamic content loading

### Extract Links

**POST /links**

Extract all links from page.

```bash
curl -X POST http://localhost:8002/links \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "selector": "a.nav-link"
  }'
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "links": [
    {
      "href": "https://example.com/about",
      "text": "About Us",
      "title": "Learn more about Example"
    }
  ],
  "count": 1,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Use Cases:**
- Web crawling and discovery
- Sitemap generation
- Link validation

### Get Cookies

**POST /cookies**

Retrieve cookies set by page.

```bash
curl -X POST http://localhost:8002/cookies \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com"
  }'
```

**Use Cases:**
- Session management
- Authentication analysis
- Cookie inspection

## Configuration

Environment variables can be set in `.env` file (see `.env.example`):

```bash
# Browser Settings
BROWSER_TYPE=chromium
HEADLESS=true
DEFAULT_TIMEOUT=30000

# Viewport
DEFAULT_VIEWPORT_WIDTH=1920
DEFAULT_VIEWPORT_HEIGHT=1080

# User Agent
USER_AGENT="Mozilla/5.0 ..."

# Performance
MAX_CONCURRENT_CONTEXTS=10
```

## Integration Examples

### Python

```python
import requests

# Render page
response = requests.post(
    "http://localhost:8002/render",
    json={
        "url": "https://example.com",
        "wait_for": "networkidle"
    }
)

data = response.json()
html = data["html"]
```

### n8n Workflow

```json
{
  "nodes": [
    {
      "name": "Render Page",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://playwright-service:8002/render",
        "jsonParameters": true,
        "bodyParametersJson": {
          "url": "={{$json[\"url\"]}}",
          "wait_for": "networkidle"
        }
      }
    }
  ]
}
```

### LangChain Tool

```python
from langchain.tools import Tool

def render_page(url: str) -> str:
    """Render JavaScript page"""
    response = requests.post(
        "http://localhost:8002/render",
        json={"url": url}
    )
    return response.json()["html"]

playwright_tool = Tool(
    name="Browser_Renderer",
    func=render_page,
    description="Render JavaScript pages and extract HTML"
)
```

## Performance Optimization

### Browser Context Pooling

The service uses browser context pooling for better performance:
- Reuses browser instances across requests
- Isolated contexts for concurrent requests
- Automatic cleanup of idle contexts

### Caching

For static pages or repeated scraping:
```python
# Add Redis caching layer
import redis
import hashlib

cache = redis.Redis(host='localhost', port=6379, db=0)

def render_with_cache(url: str) -> str:
    cache_key = f"page:{hashlib.md5(url.encode()).hexdigest()}"

    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return cached.decode()

    # Render and cache
    response = requests.post("http://localhost:8002/render", json={"url": url})
    html = response.json()["html"]

    cache.setex(cache_key, 3600, html)  # Cache for 1 hour
    return html
```

## Troubleshooting

### Browser fails to start

**Error:** `Browser executable not found`

**Solution:**
```bash
playwright install chromium
playwright install-deps chromium
```

### Timeout errors

**Error:** `Navigation timeout of 30000 ms exceeded`

**Solutions:**
1. Increase timeout: `{"timeout": 60000}`
2. Change wait condition: `{"wait_for": "domcontentloaded"}`
3. Check if page loads manually

### Memory issues

If experiencing high memory usage:
1. Reduce `MAX_CONCURRENT_CONTEXTS`
2. Enable browser pooling with smaller pool size
3. Add memory limits to Docker container:
```bash
docker run -m 2g playwright-service
```

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8002/docs`
- ReDoc: `http://localhost:8002/redoc`

## License

Part of the B2B Marketing Automation Platform (Open Source)
