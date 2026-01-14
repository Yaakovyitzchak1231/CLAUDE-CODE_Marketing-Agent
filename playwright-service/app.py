"""
Playwright Service - FastAPI Server
Browser automation service for web scraping and rendering
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List
import structlog
from datetime import datetime
import uvicorn
import base64

from browser_manager import get_browser_manager, BrowserManager

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Playwright Browser Automation API",
    description="Headless browser service for rendering JavaScript pages, screenshots, and content extraction",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models

class RenderRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL to render")
    wait_for: str = Field(default="networkidle", description="Wait condition: load, domcontentloaded, networkidle")
    timeout: int = Field(default=30000, description="Timeout in milliseconds")
    viewport_width: int = Field(default=1920, description="Viewport width")
    viewport_height: int = Field(default=1080, description="Viewport height")


class ScreenshotRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL to screenshot")
    full_page: bool = Field(default=False, description="Capture full scrollable page")
    wait_for: str = Field(default="networkidle", description="Wait condition")
    timeout: int = Field(default=30000, description="Timeout in milliseconds")
    viewport_width: int = Field(default=1920, description="Viewport width")
    viewport_height: int = Field(default=1080, description="Viewport height")


class JavaScriptRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL to load")
    script: str = Field(..., description="JavaScript code to execute")
    wait_for: str = Field(default="networkidle", description="Wait condition")
    timeout: int = Field(default=30000, description="Timeout in milliseconds")


class ExtractLinksRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL to scrape")
    selector: Optional[str] = Field(default=None, description="CSS selector for links (default: all 'a' tags)")
    wait_for: str = Field(default="networkidle", description="Wait condition")
    timeout: int = Field(default=30000, description="Timeout in milliseconds")


class GetCookiesRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL to visit")
    wait_for: str = Field(default="networkidle", description="Wait condition")
    timeout: int = Field(default=30000, description="Timeout in milliseconds")


# Health check endpoint
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Playwright Browser Automation API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    browser_manager = await get_browser_manager()

    return {
        "status": "healthy",
        "browser_running": browser_manager.browser is not None,
        "browser_type": browser_manager.browser_type,
        "headless": browser_manager.headless,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/render")
async def render_page(request: RenderRequest):
    """
    Render JavaScript page and extract HTML content

    This endpoint loads a URL in a headless browser, waits for JavaScript
    to execute, and returns the fully rendered HTML content.

    Use cases:
    - Scraping Single Page Applications (SPAs)
    - Rendering React/Vue/Angular apps
    - Extracting content from JavaScript-heavy sites
    """
    try:
        logger.info("render_request", url=str(request.url))

        browser_manager = await get_browser_manager()

        result = await browser_manager.render_page(
            url=str(request.url),
            wait_for=request.wait_for,
            timeout=request.timeout,
            viewport={
                "width": request.viewport_width,
                "height": request.viewport_height
            }
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to render page")
            )

        return JSONResponse(content={
            "success": True,
            "url": result["url"],
            "final_url": result["final_url"],
            "title": result["title"],
            "html": result["html"],
            "status_code": result.get("status_code"),
            "html_length": len(result["html"]),
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("render_error", url=str(request.url), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/screenshot")
async def take_screenshot(request: ScreenshotRequest):
    """
    Take screenshot of page

    Captures a PNG screenshot of the specified URL. Can capture
    either the visible viewport or the full scrollable page.

    Returns:
    - Base64 encoded PNG image
    - Screenshot metadata
    """
    try:
        logger.info("screenshot_request", url=str(request.url), full_page=request.full_page)

        browser_manager = await get_browser_manager()

        result = await browser_manager.take_screenshot(
            url=str(request.url),
            full_page=request.full_page,
            viewport={
                "width": request.viewport_width,
                "height": request.viewport_height
            },
            wait_for=request.wait_for,
            timeout=request.timeout
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to take screenshot")
            )

        # Encode screenshot as base64
        screenshot_base64 = base64.b64encode(result["screenshot"]).decode("utf-8")

        return JSONResponse(content={
            "success": True,
            "url": result["url"],
            "title": result["title"],
            "screenshot": screenshot_base64,
            "size_bytes": result["size_bytes"],
            "format": "png",
            "encoding": "base64",
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("screenshot_error", url=str(request.url), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/screenshot/raw")
async def take_screenshot_raw(request: ScreenshotRequest):
    """
    Take screenshot and return raw PNG bytes

    Same as /screenshot but returns raw image bytes instead of base64.
    Useful for direct download or display.
    """
    try:
        logger.info("screenshot_raw_request", url=str(request.url))

        browser_manager = await get_browser_manager()

        result = await browser_manager.take_screenshot(
            url=str(request.url),
            full_page=request.full_page,
            viewport={
                "width": request.viewport_width,
                "height": request.viewport_height
            },
            wait_for=request.wait_for,
            timeout=request.timeout
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to take screenshot")
            )

        return Response(
            content=result["screenshot"],
            media_type="image/png",
            headers={
                "Content-Disposition": f'inline; filename="{result["title"][:50]}.png"'
            }
        )

    except Exception as e:
        logger.error("screenshot_raw_error", url=str(request.url), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/execute")
async def execute_javascript(request: JavaScriptRequest):
    """
    Execute JavaScript code on page

    Loads the specified URL and executes custom JavaScript code
    in the page context. Returns the result of the script execution.

    Use cases:
    - Extract specific data using custom selectors
    - Interact with page elements
    - Trigger dynamic content loading
    """
    try:
        logger.info("execute_request", url=str(request.url))

        browser_manager = await get_browser_manager()

        result = await browser_manager.execute_javascript(
            url=str(request.url),
            script=request.script,
            wait_for=request.wait_for,
            timeout=request.timeout
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to execute JavaScript")
            )

        return JSONResponse(content={
            "success": True,
            "url": result["url"],
            "result": result["result"],
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("execute_error", url=str(request.url), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/links")
async def extract_links(request: ExtractLinksRequest):
    """
    Extract all links from page

    Scrapes all links (or links matching a CSS selector) from the page.
    Returns link URLs, text content, and titles.

    Use cases:
    - Discover URLs for crawling
    - Extract navigation structure
    - Find specific link patterns
    """
    try:
        logger.info("extract_links_request", url=str(request.url))

        browser_manager = await get_browser_manager()

        result = await browser_manager.extract_links(
            url=str(request.url),
            selector=request.selector,
            wait_for=request.wait_for,
            timeout=request.timeout
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to extract links")
            )

        return JSONResponse(content={
            "success": True,
            "url": result["url"],
            "links": result["links"],
            "count": result["count"],
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("extract_links_error", url=str(request.url), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cookies")
async def get_cookies(request: GetCookiesRequest):
    """
    Get cookies from page

    Visits the URL and retrieves all cookies set by the page.

    Use cases:
    - Session management
    - Authentication flow inspection
    - Cookie analysis
    """
    try:
        logger.info("get_cookies_request", url=str(request.url))

        browser_manager = await get_browser_manager()

        result = await browser_manager.get_cookies(
            url=str(request.url),
            wait_for=request.wait_for,
            timeout=request.timeout
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get cookies")
            )

        return JSONResponse(content={
            "success": True,
            "url": result["url"],
            "cookies": result["cookies"],
            "count": result["count"],
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("get_cookies_error", url=str(request.url), error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize browser on startup"""
    logger.info("playwright_service_starting")
    browser_manager = await get_browser_manager()
    logger.info("playwright_service_ready")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup browser on shutdown"""
    logger.info("playwright_service_shutting_down")
    browser_manager = await get_browser_manager()
    await browser_manager.stop()
    logger.info("playwright_service_stopped")


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
