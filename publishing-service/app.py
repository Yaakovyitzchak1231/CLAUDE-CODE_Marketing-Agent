"""
Publishing Service
Handles content publishing to LinkedIn, WordPress, and Email platforms
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import structlog
from datetime import datetime

from publishers.linkedin import LinkedInPublisher
from publishers.wordpress import WordPressPublisher
from publishers.email import EmailPublisher

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Publishing Service API",
    description="Content publishing service for LinkedIn, WordPress, and Email",
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

# Initialize publishers
linkedin_publisher = LinkedInPublisher()
wordpress_publisher = WordPressPublisher()
email_publisher = EmailPublisher()


# Pydantic models for request validation
class LinkedInPublishRequest(BaseModel):
    access_token: str = Field(..., description="LinkedIn API access token")
    text: str = Field(..., description="Post content text")
    title: Optional[str] = Field(default=None, description="Optional post title")
    media_urls: Optional[List[str]] = Field(default=None, description="Media URLs to attach")
    visibility: str = Field(default="PUBLIC", description="Post visibility: PUBLIC, CONNECTIONS")


class WordPressPublishRequest(BaseModel):
    wp_url: str = Field(..., description="WordPress site URL")
    wp_username: str = Field(..., description="WordPress username")
    wp_password: str = Field(..., description="WordPress password or app password")
    title: str = Field(..., description="Post title")
    content: str = Field(..., description="Post content HTML")
    categories: Optional[List[str]] = Field(default=None, description="Post categories")
    tags: Optional[List[str]] = Field(default=None, description="Post tags")
    featured_image_url: Optional[str] = Field(default=None, description="Featured image URL")
    status: str = Field(default="publish", description="Post status: publish, draft, pending")


class EmailSendRequest(BaseModel):
    smtp_host: str = Field(..., description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: str = Field(..., description="SMTP username")
    smtp_password: str = Field(..., description="SMTP password")
    from_email: str = Field(..., description="Sender email address")
    from_name: Optional[str] = Field(default=None, description="Sender display name")
    to_list: List[str] = Field(..., description="List of recipient email addresses")
    subject: str = Field(..., description="Email subject")
    html_content: str = Field(..., description="Email HTML content")
    inline_images: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="Inline images with url and cid"
    )


# Health check endpoint
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Publishing Service API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "publishers": {
            "linkedin": "available",
            "wordpress": "available",
            "email": "available"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# LinkedIn Publishing endpoint
@app.post("/linkedin/publish")
async def publish_to_linkedin(request: LinkedInPublishRequest):
    """
    Publish content to LinkedIn

    Creates a post on LinkedIn with optional media attachments
    """
    try:
        logger.info(
            "linkedin_publish_request",
            has_media=bool(request.media_urls),
            visibility=request.visibility
        )

        result = await linkedin_publisher.publish(
            access_token=request.access_token,
            text=request.text,
            title=request.title,
            media_urls=request.media_urls,
            visibility=request.visibility
        )

        return JSONResponse(content={
            "success": True,
            "platform": "linkedin",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("linkedin_publish_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# WordPress Publishing endpoint
@app.post("/wordpress/publish")
async def publish_to_wordpress(request: WordPressPublishRequest):
    """
    Publish content to WordPress

    Creates a blog post on a WordPress site
    """
    try:
        logger.info(
            "wordpress_publish_request",
            wp_url=request.wp_url,
            status=request.status
        )

        result = await wordpress_publisher.publish(
            wp_url=request.wp_url,
            wp_username=request.wp_username,
            wp_password=request.wp_password,
            title=request.title,
            content=request.content,
            categories=request.categories,
            tags=request.tags,
            featured_image_url=request.featured_image_url,
            status=request.status
        )

        return JSONResponse(content={
            "success": True,
            "platform": "wordpress",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("wordpress_publish_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Email Newsletter endpoint
@app.post("/email/send")
async def send_email(request: EmailSendRequest):
    """
    Send email newsletter

    Sends HTML email to a list of recipients
    """
    try:
        logger.info(
            "email_send_request",
            recipient_count=len(request.to_list),
            has_images=bool(request.inline_images)
        )

        result = await email_publisher.send(
            smtp_host=request.smtp_host,
            smtp_port=request.smtp_port,
            smtp_username=request.smtp_username,
            smtp_password=request.smtp_password,
            from_email=request.from_email,
            from_name=request.from_name,
            to_list=request.to_list,
            subject=request.subject,
            html_content=request.html_content,
            inline_images=request.inline_images
        )

        return JSONResponse(content={
            "success": True,
            "platform": "email",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error("email_send_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info"
    )
