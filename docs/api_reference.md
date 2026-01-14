# API Reference

Complete API documentation for the B2B Marketing Automation Platform.

## Table of Contents

1. [LangChain Service API](#langchain-service-api)
2. [n8n Webhook API](#n8n-webhook-api)
3. [Publishing API](#publishing-api)
4. [Database Schema](#database-schema)

---

## LangChain Service API

Base URL: `http://localhost:8001`

All endpoints accept JSON payloads and return JSON responses.

### Agent Endpoints

#### POST /agents/research

Execute research agent to gather information from web sources.

**Request:**
```json
{
  "query": "B2B marketing automation trends 2024",
  "sources": ["google", "reddit", "hackernews"],
  "max_results": 10
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "title": "AI-Powered Marketing Automation",
      "url": "https://example.com/article",
      "content": "Summary of the article...",
      "sentiment": "positive",
      "score": 0.89
    }
  ],
  "metadata": {
    "total_results": 10,
    "processing_time": 5.2,
    "sources_used": ["google", "reddit"]
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid query parameter",
  "code": "INVALID_INPUT"
}
```

---

#### POST /agents/content

Generate marketing content using LLM.

**Request:**
```json
{
  "topic": "AI in B2B Marketing",
  "target_audience": "Marketing managers at tech companies",
  "content_type": "linkedin_post",
  "brand_voice": "professional",
  "tone": "informative",
  "research_context": [
    {"title": "Article 1", "content": "Summary..."}
  ],
  "seo_keywords": ["AI", "marketing", "automation"]
}
```

**Response:**
```json
{
  "success": true,
  "content": "AI is transforming B2B marketing in unprecedented ways...",
  "seo_score": 85,
  "word_count": 250,
  "reading_time": 1.5,
  "hashtags": ["#AI", "#Marketing", "#B2B"],
  "metadata": {
    "model": "llama3",
    "temperature": 0.7,
    "tokens_used": 450
  }
}
```

---

#### POST /agents/image

Generate images using DALL-E 3 or Midjourney.

**Request:**
```json
{
  "prompt": "Professional team collaboration in modern office, bright natural lighting, blue corporate colors",
  "provider": "dalle3",
  "dimensions": "1200x628",
  "style": "corporate",
  "brand_colors": ["#1E3A8A", "#FFFFFF"]
}
```

**Response:**
```json
{
  "success": true,
  "image_url": "https://cdn.openai.com/...",
  "asset_id": 123,
  "metadata": {
    "provider": "dalle3",
    "dimensions": {"width": 1200, "height": 628},
    "format": "png",
    "size_bytes": 245678,
    "generation_time": 8.5
  }
}
```

---

#### POST /agents/video

Generate videos using Runway ML or Pika.

**Request:**
```json
{
  "script": {
    "scenes": [
      {
        "prompt": "Camera slowly zooms into laptop screen showing dashboard",
        "duration": 4
      },
      {
        "prompt": "Smooth pan from left to right across modern office",
        "duration": 5
      }
    ]
  },
  "provider": "runway",
  "resolution": "1920x1080",
  "transitions": ["fade", "cut"],
  "audio_url": "https://example.com/background-music.mp3"
}
```

**Response:**
```json
{
  "success": true,
  "video_url": "https://storage.example.com/video_123.mp4",
  "asset_id": 456,
  "metadata": {
    "provider": "runway",
    "duration": 9,
    "resolution": "1920x1080",
    "format": "mp4",
    "size_bytes": 12345678,
    "scenes_count": 2
  }
}
```

---

#### POST /agents/trend

Analyze trending topics from multiple sources.

**Request:**
```json
{
  "sources": ["reddit", "hackernews", "web"],
  "timeframe": "24h",
  "industry": "technology",
  "min_score": 50
}
```

**Response:**
```json
{
  "success": true,
  "trends": [
    {
      "topic": "AI Agent Frameworks",
      "score": 87,
      "mention_count": 45,
      "sentiment": "positive",
      "sources": {
        "reddit": 20,
        "hackernews": 15,
        "web": 10
      },
      "top_keywords": ["agents", "LangChain", "autonomous"]
    }
  ],
  "metadata": {
    "total_trends": 10,
    "analysis_time": 12.3
  }
}
```

---

### Tool Endpoints

#### POST /tools/seo

Optimize content for search engines.

**Request:**
```json
{
  "content": "Your content here...",
  "target_keywords": ["B2B marketing", "automation"],
  "meta_description": "Optional meta description"
}
```

**Response:**
```json
{
  "success": true,
  "optimized_content": "Optimized content...",
  "seo_score": 92,
  "improvements": [
    "Added target keyword to first paragraph",
    "Optimized heading structure",
    "Added internal links"
  ],
  "keyword_density": {
    "B2B marketing": 0.02,
    "automation": 0.015
  }
}
```

---

#### POST /tools/ffmpeg

Edit videos using FFmpeg.

**Request:**
```json
{
  "operation": "stitch",
  "clips": [
    "https://example.com/scene1.mp4",
    "https://example.com/scene2.mp4"
  ],
  "transitions": ["fade", "cut"],
  "output_format": "mp4",
  "captions": {
    "text": "Welcome to our product demo",
    "position": "bottom",
    "font_size": 24
  },
  "audio_url": "https://example.com/music.mp3",
  "audio_volume": 0.3
}
```

**Response:**
```json
{
  "success": true,
  "output_url": "https://storage.example.com/final_video.mp4",
  "metadata": {
    "duration": 30,
    "resolution": "1920x1080",
    "format": "mp4",
    "size_bytes": 45678900
  }
}
```

---

### Memory Endpoints

#### POST /memory/store

Store embeddings in vector database.

**Request:**
```json
{
  "collection": "content_library",
  "documents": [
    {
      "id": "content_123",
      "text": "Your content here...",
      "metadata": {
        "type": "linkedin_post",
        "campaign_id": 1,
        "performance_score": 0.85
      }
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "stored_count": 1,
  "collection": "content_library"
}
```

---

#### POST /memory/search

Search vector database for similar content.

**Request:**
```json
{
  "collection": "content_library",
  "query": "B2B marketing automation",
  "top_k": 5,
  "filter": {
    "type": "linkedin_post",
    "performance_score": {"$gte": 0.7}
  }
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "id": "content_456",
      "text": "Similar content...",
      "score": 0.92,
      "metadata": {
        "type": "linkedin_post",
        "campaign_id": 1,
        "performance_score": 0.85
      }
    }
  ]
}
```

---

## n8n Webhook API

Base URL: `http://localhost:5678/webhook`

### Content Review Webhook

#### POST /review-feedback

Submit content review feedback.

**Request:**
```json
{
  "draft_id": 123,
  "action": "approve",
  "reviewer_id": 1,
  "feedback_text": "Great content, ready to publish",
  "rating": 5,
  "suggested_edits": []
}
```

**Actions:** `approve`, `revise`, `reject`

**Response:**
```json
{
  "success": true,
  "draft_id": 123,
  "new_status": "approved",
  "message": "Content approved and queued for publishing"
}
```

---

### Media Processing Webhook

#### POST /media-process

Request media editing operations.

**Request:**
```json
{
  "asset_id": 456,
  "operation": "composite",
  "crop_width": 1200,
  "crop_height": 628,
  "resize_mode": "cover",
  "watermark_text": "© 2024 Company",
  "watermark_position": "bottom-right",
  "filters": {
    "type": "brightness",
    "value": 1.1
  }
}
```

**Response:**
```json
{
  "success": true,
  "asset_id": 456,
  "edited_url": "https://storage.example.com/edited_image.png",
  "edit_id": 789
}
```

---

### Onboarding Webhook

#### POST /onboarding

Trigger user onboarding workflow.

**Request:**
```json
{
  "user_id": 1,
  "email": "user@example.com",
  "company": "Tech Corp",
  "industry": "Technology",
  "target_audience": "Marketing managers at B2B tech companies",
  "brand_voice": "professional",
  "tone": "informative"
}
```

**Response:**
```json
{
  "success": true,
  "user_id": 1,
  "workflow_id": "onboarding_abc123",
  "message": "Onboarding initiated"
}
```

---

### Content Generation Webhook

#### POST /generate-content

Trigger content generation workflow.

**Request:**
```json
{
  "campaign_id": 1,
  "topic": "AI in Marketing",
  "content_type": "linkedin_post"
}
```

**Response:**
```json
{
  "success": true,
  "workflow_id": "gen_xyz789",
  "message": "Content generation started",
  "estimated_completion": "2-3 minutes"
}
```

---

### Image Generation Webhook

#### POST /generate-image

Trigger image generation workflow.

**Request:**
```json
{
  "content_id": 123,
  "prompt": "Professional team collaboration",
  "provider": "dalle3",
  "dimensions": "1200x628"
}
```

**Response:**
```json
{
  "success": true,
  "workflow_id": "img_abc123",
  "message": "Image generation started"
}
```

---

### Publishing Webhook

#### POST /publish

Trigger multi-channel publishing.

**Request:**
```json
{
  "draft_id": 123,
  "channels": ["linkedin", "wordpress", "email"],
  "schedule": "immediate",
  "linkedin_visibility": "PUBLIC",
  "wordpress_status": "publish",
  "email_recipients": ["list@example.com"]
}
```

**Response:**
```json
{
  "success": true,
  "draft_id": 123,
  "published_channels": {
    "linkedin": {
      "url": "https://www.linkedin.com/feed/update/...",
      "post_id": "urn:li:ugcPost:..."
    },
    "wordpress": {
      "url": "https://yourblog.com/post-slug",
      "post_id": 456
    },
    "email": {
      "recipients": 100,
      "sent_at": "2024-01-15T10:30:00Z"
    }
  }
}
```

---

## Publishing API

### LinkedIn Publisher

Python module: `publishing.linkedin_publisher`

#### publish_to_linkedin()

```python
from publishing import publish_to_linkedin

result = publish_to_linkedin(
    content="Your post content here",
    media_urls=["https://example.com/image.png"],
    media_type="image",
    hashtags=["Marketing", "AI"],
    access_token="your_token"
)

# Returns:
{
    "success": True,
    "post_id": "urn:li:ugcPost:...",
    "url": "https://www.linkedin.com/feed/update/...",
    "media_count": 1,
    "created_at": "2024-01-15T10:30:00"
}
```

---

### WordPress Publisher

Python module: `publishing.wordpress_publisher`

#### publish_to_wordpress()

```python
from publishing import publish_to_wordpress

result = publish_to_wordpress(
    title="How to Automate B2B Marketing",
    content="<p>Your content here...</p>",
    featured_image_url="https://example.com/header.png",
    categories=["Marketing"],
    tags=["B2B", "Automation"],
    status="publish",
    url="https://yourblog.com",
    username="your_username",
    password="app_password"
)

# Returns:
{
    "success": True,
    "post_id": 123,
    "url": "https://yourblog.com/post-slug",
    "status": "publish",
    "created_at": "2024-01-15T10:30:00"
}
```

---

### Email Publisher

Python module: `publishing.email_publisher`

#### send_email_newsletter()

```python
from publishing import send_email_newsletter

result = send_email_newsletter(
    to_emails=["subscriber@example.com"],
    subject="Weekly Marketing Insights",
    content="<h1>Newsletter content...</h1>",
    header_image_url="https://example.com/banner.png",
    footer_text="© 2024 Company",
    unsubscribe_link="https://example.com/unsubscribe",
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_username="your@email.com",
    smtp_password="app_password"
)

# Returns:
{
    "success": True,
    "recipients": 1,
    "sent_at": "2024-01-15T10:30:00",
    "subject": "Weekly Marketing Insights"
}
```

---

## Database Schema

### Tables

#### users
```sql
id              SERIAL PRIMARY KEY
email           VARCHAR(255) UNIQUE NOT NULL
company         VARCHAR(255)
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### campaigns
```sql
id              SERIAL PRIMARY KEY
user_id         INTEGER REFERENCES users(id)
name            VARCHAR(255) NOT NULL
status          VARCHAR(50) DEFAULT 'active'
target_audience TEXT
branding_json   JSONB
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**branding_json structure:**
```json
{
  "brand_voice": "professional",
  "tone": "informative",
  "primary_color": "#1E3A8A",
  "secondary_color": "#FFFFFF",
  "keywords": ["innovation", "technology"],
  "logo_url": "https://example.com/logo.png",
  "website_url": "https://example.com",
  "tagline": "Your tagline here"
}
```

#### content_drafts
```sql
id              SERIAL PRIMARY KEY
campaign_id     INTEGER REFERENCES campaigns(id)
type            VARCHAR(50) NOT NULL
content         TEXT NOT NULL
seo_score       INTEGER
status          VARCHAR(50) DEFAULT 'draft'
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Status values:** `draft`, `in_review`, `approved`, `rejected`, `published`

**Type values:** `linkedin_post`, `blog_post`, `email`, `social_media`

#### media_assets
```sql
id              SERIAL PRIMARY KEY
draft_id        INTEGER REFERENCES content_drafts(id)
type            VARCHAR(50) NOT NULL
file_path       VARCHAR(500)
url             VARCHAR(500)
prompt          TEXT
api_provider    VARCHAR(100)
metadata_json   JSONB
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Type values:** `image`, `video`

**Provider values:** `dalle3`, `midjourney`, `runway`, `pika`, `stable_diffusion`

**metadata_json structure:**
```json
{
  "dimensions": {"width": 1200, "height": 628},
  "duration": 30,
  "format": "png",
  "size_bytes": 245678,
  "prompt_params": {
    "temperature": 0.7,
    "style": "corporate"
  }
}
```

#### published_content
```sql
id              SERIAL PRIMARY KEY
draft_id        INTEGER REFERENCES content_drafts(id)
channel         VARCHAR(50) NOT NULL
url             VARCHAR(500)
published_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Channel values:** `linkedin`, `wordpress`, `email`, `twitter`, `facebook`

#### engagement_metrics
```sql
id              SERIAL PRIMARY KEY
content_id      INTEGER REFERENCES published_content(id)
views           INTEGER DEFAULT 0
clicks          INTEGER DEFAULT 0
shares          INTEGER DEFAULT 0
conversions     INTEGER DEFAULT 0
tracked_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

---

## Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INVALID_INPUT` | Invalid request parameters | 400 |
| `UNAUTHORIZED` | Missing or invalid authentication | 401 |
| `FORBIDDEN` | Insufficient permissions | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `RATE_LIMIT` | API rate limit exceeded | 429 |
| `SERVER_ERROR` | Internal server error | 500 |
| `SERVICE_UNAVAILABLE` | External service unavailable | 503 |
| `LLM_ERROR` | LLM generation failed | 500 |
| `MEDIA_ERROR` | Media generation/processing failed | 500 |
| `DATABASE_ERROR` | Database operation failed | 500 |

---

## Rate Limits

### LangChain Service
- **Research Agent**: 100 requests/hour
- **Content Agent**: 200 requests/hour
- **Image Agent**: 50 requests/hour (DALL-E API limit)
- **Video Agent**: 20 requests/hour (Runway API limit)

### Publishing APIs
- **LinkedIn**: 100 posts/day (free tier)
- **WordPress**: No limit (self-hosted)
- **Email**: 500 emails/day (Gmail free), 2000/day (Google Workspace)

---

## Authentication

### API Keys

Set in environment variables:

```bash
# LangChain Service
LANGCHAIN_API_KEY=your_internal_api_key

# LinkedIn
LINKEDIN_ACCESS_TOKEN=your_oauth_token

# WordPress
WORDPRESS_USERNAME=your_username
WORDPRESS_PASSWORD=app_password

# Email
SMTP_USERNAME=your_email
SMTP_PASSWORD=app_password
```

### n8n Basic Auth

Configure in `.env`:

```bash
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_password
```

Access n8n with credentials at: `http://localhost:5678`

---

## SDK Examples

### Python SDK

```python
import requests

# LangChain Service Client
class MarketingAPI:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url

    def generate_content(self, topic, audience):
        response = requests.post(
            f"{self.base_url}/agents/content",
            json={
                "topic": topic,
                "target_audience": audience
            }
        )
        return response.json()

    def generate_image(self, prompt):
        response = requests.post(
            f"{self.base_url}/agents/image",
            json={"prompt": prompt}
        )
        return response.json()

# Usage
api = MarketingAPI()
content = api.generate_content(
    topic="AI Marketing Tools",
    audience="B2B marketers"
)
print(content["content"])
```

### Node.js SDK

```javascript
const axios = require('axios');

class MarketingAPI {
    constructor(baseURL = 'http://localhost:8001') {
        this.client = axios.create({ baseURL });
    }

    async generateContent(topic, audience) {
        const response = await this.client.post('/agents/content', {
            topic,
            target_audience: audience
        });
        return response.data;
    }

    async generateImage(prompt) {
        const response = await this.client.post('/agents/image', {
            prompt
        });
        return response.data;
    }
}

// Usage
const api = new MarketingAPI();
const content = await api.generateContent(
    'AI Marketing Tools',
    'B2B marketers'
);
console.log(content.content);
```

---

## Webhooks

### Event Types

The platform can send webhooks for various events:

| Event | Trigger | Payload |
|-------|---------|---------|
| `content.created` | New content draft created | `{draft_id, content, status}` |
| `content.approved` | Content approved for publishing | `{draft_id, approved_by, timestamp}` |
| `content.published` | Content published to channel | `{draft_id, channel, url}` |
| `media.generated` | Media asset generated | `{asset_id, type, url}` |
| `engagement.updated` | New engagement metrics | `{content_id, views, clicks, shares}` |
| `trend.detected` | New trend detected | `{topic, score, sources}` |

### Webhook Configuration

Configure webhook endpoints in n8n workflow settings or via API:

```json
{
  "event": "content.published",
  "url": "https://your-app.com/webhooks/content-published",
  "secret": "your_webhook_secret",
  "enabled": true
}
```

---

## Support

- **API Issues**: Open issue on GitHub
- **Documentation**: See `/docs` folder
- **Examples**: See `/examples` folder (coming soon)
