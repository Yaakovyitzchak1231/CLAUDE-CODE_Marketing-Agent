# n8n Workflow Guide

## Overview

This guide provides detailed documentation for all 10 n8n workflows in the B2B Marketing Automation Platform. Each workflow is designed to handle specific aspects of the marketing automation pipeline.

## Workflow Architecture

All workflows follow consistent design patterns:

1. **Webhook Triggers**: HTTP endpoints for external invocation
2. **Sequential Processing**: Linear node chains for simple flows
3. **Parallel Processing**: Split/merge patterns for concurrent execution
4. **Error Handling**: Retry logic and fallback mechanisms
5. **Data Persistence**: PostgreSQL for state management
6. **Event Emission**: Webhooks to trigger other workflows

## Workflow Inventory

| Workflow | Trigger Type | Purpose | Dependencies |
|----------|-------------|---------|--------------|
| user_onboarding.json | Webhook | User profiling wizard | PostgreSQL, Chroma |
| research_pipeline.json | Webhook | Competitive research | LangChain, SearXNG, PostgreSQL |
| content_generation.json | Webhook | Text content creation | LangChain, Ollama, PostgreSQL, Chroma |
| image_generation.json | Webhook | Image creation | DALL-E 3/Midjourney, PostgreSQL |
| video_generation.json | Webhook | Video creation | Runway/Pika, FFmpeg, PostgreSQL |
| media_post_processing.json | Webhook | Image/video editing | FFmpeg, PostgreSQL |
| content_review_loop.json | Webhook | Human review workflow | LangChain, PostgreSQL, Streamlit |
| publishing_pipeline.json | Webhook | Multi-channel publishing | LinkedIn, WordPress, SMTP, PostgreSQL |
| engagement_tracking.json | Cron + Webhook | Analytics collection | LinkedIn API, Matomo, PostgreSQL |
| trend_monitoring.json | Cron | Trend detection | Reddit, HackerNews, PostgreSQL |

## Workflow Details

### 1. User Onboarding Workflow

**File**: `n8n-workflows/user_onboarding.json`

**Purpose**: Conversational user profiling to collect business information, target audience, and brand guidelines.

**Trigger**: `POST /webhook/onboarding`

**Input Schema**:
```json
{
  "email": "user@example.com",
  "company": "Acme Corp",
  "role": "Marketing Manager",
  "industry": "SaaS",
  "website": "https://acme.com"
}
```

**Workflow Steps**:

1. **Webhook - Start Onboarding**
   - Receives user profile data
   - Validates required fields

2. **Create User Record**
   - SQL: `INSERT INTO users (email, company, created_at) VALUES (...)`
   - Returns user_id

3. **Extract Brand Guidelines**
   - HTTP Request to website scraper
   - Extracts colors, fonts, brand voice from website

4. **Analyze Target Audience**
   - Calls Market Analysis Agent
   - Segments audience based on industry and role

5. **Create Campaign**
   - SQL: `INSERT INTO campaigns (user_id, name, target_audience, branding_json, status)`
   - Sets default campaign as "active"

6. **Store User Profile Embeddings**
   - Calls LangChain `/memory/store` endpoint
   - Stores in Chroma for semantic retrieval

7. **Send Welcome Email**
   - Calls Email Publisher
   - Sends onboarding guide with next steps

8. **Return Response**
   - Returns user_id, campaign_id, onboarding status

**Error Handling**:
- Duplicate email: Returns existing user_id
- Invalid website: Uses default brand colors
- API failures: Retries 3 times with exponential backoff

**Usage Example**:
```bash
curl -X POST http://n8n:5678/webhook/onboarding \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@acme.com",
    "company": "Acme Corp",
    "industry": "SaaS",
    "website": "https://acme.com"
  }'
```

---

### 2. Research Pipeline Workflow

**File**: `n8n-workflows/research_pipeline.json`

**Purpose**: Automated competitive research and market analysis.

**Trigger**: `POST /webhook/research`

**Input Schema**:
```json
{
  "campaign_id": 1,
  "topics": ["AI marketing", "B2B automation"],
  "competitors": ["competitor.com", "rival.io"]
}
```

**Workflow Steps**:

1. **Webhook - Start Research**
   - Receives campaign_id and research topics

2. **Get Campaign Details**
   - SQL: `SELECT * FROM campaigns WHERE id = $campaign_id`
   - Gets target_audience, industry

3. **Search Web (Parallel)**
   - For each topic:
     - Calls SearXNG search tool
     - Extracts top 10 results
   - Executes in parallel using Split In Batches

4. **Scrape Competitor Sites (Parallel)**
   - For each competitor:
     - Calls Playwright scraper service
     - Extracts homepage, blog, pricing page
   - Executes in parallel

5. **Analyze Content Sentiment**
   - Calls Research Agent
   - Sentiment analysis on scraped content
   - Extracts key themes and messaging

6. **Store Competitor Data**
   - SQL: `INSERT INTO competitors (campaign_id, name, url, data_json, last_scraped)`
   - Stores full competitor analysis

7. **Extract Market Insights**
   - Calls Market Analysis Agent
   - Identifies audience pain points, trends

8. **Store Insights**
   - SQL: `INSERT INTO market_insights (campaign_id, segment, insights_json)`

9. **Return Research Summary**
   - Aggregates all findings
   - Returns structured JSON

**Parallel Processing Pattern**:
```
Topics ──→ Split In Batches ──→ [Search 1, Search 2, Search 3] ──→ Merge
Competitors ──→ Split In Batches ──→ [Scrape 1, Scrape 2] ──→ Merge
```

**Output Example**:
```json
{
  "campaign_id": 1,
  "research_summary": {
    "topics_analyzed": 2,
    "competitors_analyzed": 2,
    "key_insights": [
      "AI-powered personalization is trending",
      "Competitors focus on enterprise market"
    ],
    "sentiment": {
      "average_score": 0.65,
      "trend": "positive"
    }
  }
}
```

---

### 3. Content Generation Workflow

**File**: `n8n-workflows/content_generation.json`

**Purpose**: Generate marketing content with SEO optimization and grammar checking.

**Trigger**: `POST /webhook/content-generate`

**Input Schema**:
```json
{
  "campaign_id": 1,
  "topic": "AI in B2B Marketing",
  "content_type": "linkedin_post",
  "target_word_count": 250
}
```

**Workflow Steps**:

1. **Webhook - Generate Content**
   - Receives content generation request

2. **Get Campaign Details**
   - SQL: `SELECT * FROM campaigns WHERE id = $campaign_id`
   - Gets target_audience, branding_json

3. **Get Recent Research**
   - SQL: `SELECT * FROM market_insights WHERE campaign_id = $campaign_id ORDER BY created_at DESC LIMIT 5`
   - Provides research context

4. **Find Similar Content (RAG)**
   - HTTP Request: `POST /memory/search`
   - Searches Chroma for similar successful content
   - Provides examples for LLM

5. **Generate Content**
   - HTTP Request: `POST /agents/content`
   - Payload includes:
     - Topic
     - Target audience
     - Brand voice
     - Research context
     - Similar content examples
   - Returns draft content

6. **Optimize for SEO**
   - HTTP Request: `POST /tools/seo`
   - Adds meta keywords, optimizes headings
   - Returns seo_score (0-100)

7. **Check Grammar**
   - HTTP Request: `POST /tools/grammar`
   - Fixes grammar and style issues
   - Returns corrected content

8. **Save Draft**
   - SQL: `INSERT INTO content_drafts (campaign_id, type, content, seo_score, status) VALUES (...)`
   - Status: "in_review"
   - Returns draft_id

9. **Store Content Embeddings**
   - HTTP Request: `POST /memory/store`
   - Stores in Chroma for future RAG

10. **Trigger Review Webhook**
    - HTTP Request: `POST /webhook/review-notify`
    - Notifies Streamlit dashboard

11. **Return Draft**
    - Returns draft_id, content, seo_score

**Content Type Variations**:

| Type | Word Count | Format | Special Processing |
|------|-----------|--------|-------------------|
| linkedin_post | 150-300 | Plain text + hashtags | 3000 char limit |
| blog_post | 800-1200 | HTML | SEO optimization |
| email_newsletter | 400-600 | HTML template | Personalization |
| twitter_post | 100-200 | Plain text | 280 char limit |

**Error Handling**:
- LLM timeout: Retry with shorter prompt
- Low SEO score (<50): Regenerate with SEO focus
- Grammar check failure: Skip and proceed

---

### 4. Image Generation Workflow

**File**: `n8n-workflows/image_generation.json`

**Purpose**: Generate branded images using DALL-E 3 or Midjourney.

**Trigger**: `POST /webhook/image-generate`

**Input Schema**:
```json
{
  "draft_id": 1,
  "image_type": "social_post",
  "dimensions": "1200x628",
  "provider": "dalle",
  "custom_prompt": "Optional custom prompt"
}
```

**Workflow Steps**:

1. **Webhook - Generate Image**
   - Receives image generation request

2. **Get Content Draft**
   - SQL: `SELECT * FROM content_drafts WHERE id = $draft_id`
   - Gets content text for context

3. **Get Campaign Branding**
   - SQL: `SELECT branding_json FROM campaigns WHERE id = $campaign_id`
   - Gets brand colors, style preferences

4. **Build Image Prompt**
   - HTTP Request: `POST /chains/image-prompt-builder`
   - Converts content text + branding → detailed DALL-E prompt
   - Example output: "Professional team collaboration in modern office, bright natural lighting, corporate colors #1E3A8A and #FFFFFF, minimalist style, 1200x628px"

5. **If DALL-E Provider**
   - HTTP Request: `POST /agents/image` with `provider: dalle`
   - DALL-E 3 generates image
   - Returns image URL

6. **If Midjourney Provider**
   - HTTP Request: `POST /agents/image` with `provider: midjourney`
   - Midjourney generates image
   - Returns image URL

7. **Download Image**
   - HTTP Request: `GET $image_url`
   - Saves to temporary file

8. **Add Watermark**
   - HTTP Request: `POST /tools/ffmpeg`
   - Operation: `add_watermark`
   - Adds logo from branding_json

9. **Resize for Platform**
   - HTTP Request: `POST /tools/ffmpeg`
   - Operation: `resize`
   - Target dimensions from input

10. **Optimize File Size**
    - HTTP Request: `POST /tools/ffmpeg`
    - Operation: `optimize`
    - Compresses without quality loss

11. **Upload to Storage**
    - Saves final image to file system or S3
    - Returns final file path/URL

12. **Save Media Asset**
    - SQL: `INSERT INTO media_assets (draft_id, type, file_path, url, prompt, api_provider, metadata_json)`
    - Stores full generation metadata

13. **Trigger Media Review**
    - HTTP Request: `POST /webhook/media-review-notify`
    - Notifies Streamlit dashboard

14. **Return Asset**
    - Returns asset_id, url, metadata

**Image Types and Dimensions**:

| Type | Dimensions | Use Case |
|------|-----------|----------|
| linkedin_post | 1200x628 | Social media posts |
| blog_header | 1920x1080 | Blog article headers |
| instagram_post | 1080x1080 | Instagram feed |
| email_banner | 600x200 | Email newsletter headers |
| infographic | 800x2000 | Long-form visual content |

**Provider Comparison**:

| Feature | DALL-E 3 | Midjourney |
|---------|----------|------------|
| Quality | Excellent | Artistic |
| Cost | $0.04-0.12/image | $10-60/month |
| Speed | 10-30 seconds | 30-60 seconds |
| Style | Realistic | Stylized |

---

### 5. Video Generation Workflow

**File**: `n8n-workflows/video_generation.json`

**Purpose**: Create videos by generating scenes and stitching with FFmpeg.

**Trigger**: `POST /webhook/video-generate`

**Input Schema**:
```json
{
  "draft_id": 1,
  "video_type": "explainer",
  "duration": 30,
  "provider": "runway"
}
```

**Workflow Steps**:

1. **Webhook - Generate Video**
   - Receives video generation request

2. **Get Content Draft**
   - SQL: `SELECT * FROM content_drafts WHERE id = $draft_id`

3. **Build Video Script**
   - HTTP Request: `POST /chains/video-script-builder`
   - Converts content into scenes with timing
   - Example output:
     ```json
     {
       "scenes": [
         {"text": "Hook: AI is transforming marketing", "duration": 3, "visual": "AI robot"},
         {"text": "Problem: Manual processes slow you down", "duration": 5, "visual": "Stressed marketer"},
         {"text": "Solution: Automate with our platform", "duration": 7, "visual": "Dashboard demo"}
       ]
     }
     ```

4. **Split Scenes**
   - Code Node: Splits scenes into separate items
   - Prepares for parallel processing

5. **Generate Scenes (Parallel)**
   - For each scene:
     - HTTP Request: `POST /agents/video`
     - Provider: Runway ML or Pika
     - Generates 4-8 second clip
     - Returns video URL
   - Uses Split In Batches for parallelization

6. **Download Clips**
   - For each scene URL:
     - HTTP Request: `GET $scene_url`
     - Saves to temporary file

7. **Stitch Clips with FFmpeg**
   - HTTP Request: `POST /tools/ffmpeg`
   - Operation: `stitch`
   - Payload: Array of clip paths + transition effects
   - Returns stitched video path

8. **Add Captions**
   - HTTP Request: `POST /tools/ffmpeg`
   - Operation: `add_captions`
   - Burns in subtitles from scene text

9. **Add Background Music**
   - HTTP Request: `POST /tools/ffmpeg`
   - Operation: `add_audio`
   - Mixes royalty-free background track

10. **Add Intro/Outro**
    - HTTP Request: `POST /tools/ffmpeg`
    - Operation: `add_intro_outro`
    - Prepends/appends brand intro/outro clips

11. **Render Final Video**
    - HTTP Request: `POST /tools/ffmpeg`
    - Operation: `render`
    - Final encoding for target platform

12. **Upload to Storage**
    - Saves to file system or S3

13. **Save Media Asset**
    - SQL: `INSERT INTO media_assets (draft_id, type, file_path, url, prompt, api_provider, metadata_json)`

14. **Trigger Media Review**
    - HTTP Request: `POST /webhook/media-review-notify`

**Video Types**:

| Type | Duration | Scenes | Style |
|------|----------|--------|-------|
| social_short | 15-30s | 3-5 | Fast-paced |
| explainer | 60-90s | 5-8 | Educational |
| product_demo | 90-120s | 6-10 | Detailed |
| testimonial | 30-45s | 2-4 | Emotional |

---

### 6. Media Post-Processing Workflow

**File**: `n8n-workflows/media_post_processing.json`

**Purpose**: Edit images and videos based on user feedback.

**Trigger**: `POST /webhook/media-process`

**Input Schema**:
```json
{
  "asset_id": 1,
  "operation": "crop",
  "params": {
    "x": 100,
    "y": 100,
    "width": 800,
    "height": 600
  }
}
```

**Workflow Steps**:

1. **Webhook - Process Media**
   - Receives edit request

2. **Get Original Asset**
   - SQL: `SELECT * FROM media_assets WHERE id = $asset_id`
   - Gets file_path, type, metadata

3. **Determine Media Type**
   - IF node: Branches based on type (image vs video)

4. **Image Processing Branch**
   - Supported operations:
     - **crop**: Crop to specified dimensions
     - **resize**: Change dimensions
     - **filter**: Apply grayscale, sepia, brightness, contrast
     - **watermark**: Add text or logo overlay
   - HTTP Request: `POST /tools/ffmpeg` (FFmpeg handles images too)

5. **Video Processing Branch**
   - Supported operations:
     - **trim**: Cut to specific time range
     - **captions**: Burn in subtitles
     - **music**: Add/replace background audio
     - **watermark**: Add logo overlay
   - HTTP Request: `POST /tools/ffmpeg`

6. **Save Edited File**
   - Generates new filename with timestamp
   - Saves to file system

7. **Create Edit Record**
   - SQL: `INSERT INTO media_edits (asset_id, edit_type, edit_params, edited_file_path)`
   - Tracks edit history

8. **Update Asset Metadata**
   - SQL: `UPDATE media_assets SET metadata_json = jsonb_set(metadata_json, '{edits_count}', ...)`
   - Increments edit counter

9. **Return Edited Asset**
   - Returns new file_path, edit_id

**Batch Processing**:

The workflow also supports batch operations:

```json
{
  "asset_ids": [1, 2, 3],
  "operation": "watermark",
  "params": {
    "text": "© Acme Corp",
    "position": "bottom-right"
  }
}
```

Uses Split In Batches to process each asset in parallel.

---

### 7. Content Review Loop Workflow

**File**: `n8n-workflows/content_review_loop.json`

**Purpose**: Human-in-the-loop content review with three decision paths.

**Trigger**: `POST /webhook/review-feedback`

**Input Schema**:
```json
{
  "draft_id": 1,
  "action": "revise",
  "feedback_text": "Make tone more professional",
  "rating": 3,
  "suggested_edits": [
    {"section": "intro", "suggestion": "Add stronger hook"}
  ]
}
```

**Workflow Steps**:

1. **Webhook - Review Feedback**
   - Receives review decision

2. **Get Draft Content**
   - SQL: `SELECT * FROM content_drafts WHERE id = $draft_id`
   - Gets original content

3. **Save Feedback**
   - SQL: `INSERT INTO review_feedback (draft_id, reviewer, feedback_text, rating, suggested_edits)`

4. **Switch on Action**
   - IF node with 3 branches: approve, revise, reject

**Branch A: Approve**

5A. **Trigger Publishing**
   - HTTP Request: `POST /webhook/publish`
   - Sends draft_id to publishing workflow

6A. **Update Draft Status**
   - SQL: `UPDATE content_drafts SET status = 'approved' WHERE id = $draft_id`

7A. **Return Success**
   - Returns: `{"status": "approved", "will_publish": true}`

**Branch B: Revise**

5B. **Apply LLM Revisions**
   - HTTP Request: `POST /agents/content`
   - Operation: `revise`
   - Payload:
     - Original content
     - Feedback text
     - Suggested edits
   - LLM applies targeted edits

6B. **Create New Version**
   - SQL: `INSERT INTO content_versions (draft_id, version_number, content, created_by)`
   - Increments version number

7B. **Update Draft**
   - SQL: `UPDATE content_drafts SET content = $revised_content WHERE id = $draft_id`

8B. **Notify Reviewer**
   - HTTP Request: `POST /webhook/review-notify`
   - Sends notification to Streamlit

9B. **Return Revised Content**
   - Returns: `{"status": "revised", "new_version": 2, "content": "..."}`

**Branch C: Reject**

5C. **Update Draft Status**
   - SQL: `UPDATE content_drafts SET status = 'rejected' WHERE id = $draft_id`

6C. **Return Rejection**
   - Returns: `{"status": "rejected"}`

**Iteration Loop**:

The workflow supports multiple revision cycles:
```
Draft Created → In Review → Revise → Revised Draft → In Review → Approve → Publish
```

Each revision creates a new version in content_versions table.

---

### 8. Publishing Pipeline Workflow

**File**: `n8n-workflows/publishing_pipeline.json`

**Purpose**: Publish content to LinkedIn, WordPress, and Email with channel-specific formatting.

**Trigger**: `POST /webhook/publish`

**Input Schema**:
```json
{
  "draft_id": 1,
  "channels": ["linkedin", "wordpress", "email"],
  "scheduled_time": null
}
```

**Workflow Steps**:

1. **Webhook - Publish Content**
   - Receives publishing request

2. **Get Draft and Media**
   - SQL JOIN:
     ```sql
     SELECT d.*, m.url, m.type
     FROM content_drafts d
     LEFT JOIN media_assets m ON m.draft_id = d.id
     WHERE d.id = $draft_id
     ```
   - Gets content + associated media

3. **Get Campaign Branding**
   - SQL: `SELECT branding_json FROM campaigns WHERE id = $campaign_id`

4. **For Each Channel (Parallel)**
   - Split channels into separate items
   - Process each channel in parallel

**Channel A: LinkedIn**

5A. **Format for LinkedIn**
   - Code Node:
     - Truncate to 3000 characters
     - Add hashtags from meta_keywords
     - Format: `{content}\n\n{hashtags}`

6A. **Publish to LinkedIn**
   - HTTP Request: `POST http://langchain-service:8001/publish/linkedin`
   - If media exists: Includes image/video URLs
   - Returns post_id, post_url

**Channel B: WordPress**

5B. **Format for WordPress**
   - Code Node:
     - Convert to HTML
     - Add featured image if exists
     - Format: `<img src="..."/>\n\n{content}`

6B. **Publish to WordPress**
   - HTTP Request: `POST http://langchain-service:8001/publish/wordpress`
   - Sets categories from campaign
   - Returns post_id, post_url

**Channel C: Email**

5C. **Format for Email**
   - Code Node:
     - Use full HTML template
     - Inline images
     - Add header banner

6C. **Send Email Newsletter**
   - HTTP Request: `POST http://langchain-service:8001/publish/email`
   - Sends to campaign subscriber list
   - Returns recipients_count

7. **Merge Channel Results**
   - Aggregates results from all channels

8. **Save Published Records**
   - For each channel:
     - SQL: `INSERT INTO published_content (draft_id, channel, url, published_at)`

9. **Initialize Engagement Tracking**
   - For each published_content:
     - SQL: `INSERT INTO engagement_metrics (content_id, views, clicks, shares, conversions)`
     - Sets all metrics to 0

10. **Update Draft Status**
    - SQL: `UPDATE content_drafts SET status = 'published' WHERE id = $draft_id`

11. **Return Publishing Summary**
    - Returns array of results per channel:
      ```json
      {
        "draft_id": 1,
        "published_channels": [
          {"channel": "linkedin", "url": "https://linkedin.com/...", "success": true},
          {"channel": "wordpress", "url": "https://blog.com/...", "success": true},
          {"channel": "email", "recipients": 500, "success": true}
        ]
      }
      ```

**Scheduled Publishing**:

If `scheduled_time` is provided:
- Saves to `scheduled_publications` table
- Cron workflow checks every 15 minutes
- Triggers publishing at scheduled time

---

### 9. Engagement Tracking Workflow

**File**: `n8n-workflows/engagement_tracking.json`

**Purpose**: Collect engagement metrics from LinkedIn, WordPress, and Matomo.

**Triggers**:
- Cron: Every hour (`0 * * * *`)
- Webhook: `POST /webhook/track-engagement` (manual refresh)

**Workflow Steps**:

1. **Trigger - Start Tracking**
   - Cron runs hourly

2. **Get Recent Published Content**
   - SQL:
     ```sql
     SELECT * FROM published_content
     WHERE published_at > NOW() - INTERVAL '7 days'
     ORDER BY published_at DESC
     ```
   - Gets content published in last 7 days

3. **For Each Published Content**
   - Split into separate items for processing

4. **Switch by Channel**
   - IF node branches by channel type

**Branch A: LinkedIn**

5A. **Fetch LinkedIn Analytics**
   - HTTP Request: `GET https://api.linkedin.com/v2/socialActions/urn:li:ugcPost:${post_id}`
   - Requires OAuth token
   - Returns: impressions, clicks, shares, likes, comments

**Branch B: WordPress**

5B. **Fetch WordPress Stats**
   - HTTP Request: WordPress Stats API (or Matomo)
   - Returns: views, clicks

**Branch C: Email**

5C. **Fetch Email Stats**
   - Query SMTP log or ESP API (Mailgun, SendGrid)
   - Returns: opens, clicks, bounces

6. **Aggregate Metrics**
   - Code Node:
     - Normalizes metrics across channels
     - Calculates engagement_rate = (clicks + shares) / views * 100

7. **Update Engagement Metrics**
   - SQL:
     ```sql
     INSERT INTO engagement_metrics (content_id, views, clicks, shares, conversions, tracked_at)
     VALUES (...)
     ON CONFLICT (content_id, tracked_at)
     DO UPDATE SET views = EXCLUDED.views, clicks = EXCLUDED.clicks
     ```

8. **Check for High Engagement**
   - IF engagement_rate > 5%:
     - Send alert notification
     - Flag content as "high_performer"

9. **Aggregate Campaign Performance**
   - SQL:
     ```sql
     UPDATE campaigns
     SET metadata_json = jsonb_set(
       metadata_json,
       '{total_engagement}',
       (SELECT SUM(clicks + shares) FROM engagement_metrics ...)
     )
     WHERE id = $campaign_id
     ```

10. **Return Tracking Summary**
    - Returns metrics summary per channel

---

### 10. Trend Monitoring Workflow

**File**: `n8n-workflows/trend_monitoring.json`

**Purpose**: Daily analysis of trending topics from Reddit, HackerNews, and web.

**Triggers**:
- Cron: Daily at 8am (`0 8 * * *`)
- Webhook: `POST /webhook/analyze-trends` (manual)

**Workflow Steps**:

1. **Trigger - Start Trend Analysis**
   - Cron runs at 8am daily

2. **Get Active Campaigns**
   - SQL: `SELECT * FROM campaigns WHERE status = 'active'`
   - Gets industries and target audiences

3. **Scrape Reddit (Parallel)**
   - For each industry subreddit:
     - HTTP Request: Reddit API
     - Gets top posts from last 24 hours
     - Extracts title, score, comments

4. **Scrape HackerNews (Parallel)**
   - HTTP Request: HackerNews API
   - Gets front page stories
   - Filters by keywords related to industries

5. **Web Search (Parallel)**
   - For each campaign:
     - HTTP Request: SearXNG
     - Query: "{industry} trends {current_date}"
     - Gets top 10 results

6. **Merge Data Sources**
   - Code Node: Combines all sources into single dataset

7. **Extract Topics**
   - HTTP Request: `POST /tools/topic-extraction`
   - Uses NER to extract entities and topics
   - Groups by topic

8. **Calculate Trend Scores**
   - Code Node:
     ```javascript
     for (const topic in topics) {
       const mentions = topics[topic].length;
       const avgScore = topics[topic].reduce((sum, item) => sum + item.score, 0) / mentions;
       const trendScore = (mentions * avgScore) / 10;
       topicScores[topic] = {
         topic,
         mention_count: mentions,
         avg_engagement_score: avgScore,
         trend_score: trendScore
       };
     }
     ```

9. **Analyze Sentiment**
   - HTTP Request: `POST /tools/sentiment`
   - For each topic, analyzes sentiment
   - Returns: positive, negative, neutral

10. **Store Trends**
    - SQL: `INSERT INTO trends (topic, score, source, sentiment, detected_at)`

11. **Identify Emerging Trends**
    - IF trend_score > 50:
      - Flag as "emerging"
      - Trigger alert

12. **Generate Weekly Report**
    - IF today is Sunday:
      - Aggregates last 7 days of trends
      - Generates report
      - Sends email to campaign owners

13. **Auto-Trigger Content Generation**
    - For top 3 emerging trends:
      - HTTP Request: `POST /webhook/content-generate`
      - Creates content drafts automatically

14. **Return Trend Summary**
    - Returns top 10 trends with scores

**Trend Scoring Algorithm**:
```
trend_score = (mention_count × avg_engagement_score) / 10

Where:
- mention_count: Number of times topic mentioned across sources
- avg_engagement_score: Average upvotes/likes/shares
- Threshold for "emerging": score > 50
```

---

## Common n8n Patterns

### 1. Error Handling

All workflows implement consistent error handling:

```json
{
  "retryOnFail": true,
  "maxTries": 3,
  "waitBetweenTries": 5000,
  "continueOnFail": false
}
```

**Error Node Pattern**:
```
Main Flow ──→ [On Error] ──→ Log Error ──→ Send Alert ──→ Store Failed Job
```

### 2. Conditional Branching

**IF Node**:
```json
{
  "conditions": {
    "conditions": [
      {
        "leftValue": "={{ $json.status }}",
        "rightValue": "approved",
        "operator": {"type": "string", "operation": "equals"}
      }
    ]
  }
}
```

**Switch Node** (multiple conditions):
```json
{
  "mode": "rules",
  "rules": [
    {"conditions": [...], "output": 0},
    {"conditions": [...], "output": 1},
    {"conditions": [...], "output": 2}
  ],
  "fallbackOutput": 3
}
```

### 3. Parallel Processing

**Split In Batches**:
```json
{
  "batchSize": 3,
  "options": {}
}
```

Flow:
```
Input: [item1, item2, item3, item4, item5]
  ↓
Split In Batches (size=3)
  ↓
Batch 1: [item1, item2, item3] ──→ Process ──┐
Batch 2: [item4, item5]        ──→ Process ──┤
                                               ├──→ Merge
```

### 4. Data Transformation

**Code Node** (JavaScript):
```javascript
// Access input data
const items = $input.all();

// Transform
const transformed = items.map(item => ({
  id: item.json.id,
  name: item.json.name.toUpperCase(),
  timestamp: new Date().toISOString()
}));

// Return
return transformed.map(data => ({ json: data }));
```

### 5. Webhook Response

**Immediate Response**:
```json
{
  "respondWith": "firstEntryJson",
  "responseCode": 200,
  "responseHeaders": {
    "Content-Type": "application/json"
  }
}
```

**Async Pattern** (Respond immediately, process in background):
```
Webhook ──→ Respond (202 Accepted) ──→ Continue Processing
```

## Testing Workflows

### Manual Testing

**Test Webhook Endpoints**:
```bash
# Content generation
curl -X POST http://localhost:5678/webhook/content-generate \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": 1,
    "topic": "AI in Marketing",
    "content_type": "linkedin_post"
  }'

# Image generation
curl -X POST http://localhost:5678/webhook/image-generate \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": 1,
    "image_type": "social_post",
    "provider": "dalle"
  }'

# Publishing
curl -X POST http://localhost:5678/webhook/publish \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": 1,
    "channels": ["linkedin"]
  }'
```

### Debugging

**Enable Debug Mode**:
1. Open workflow in n8n UI
2. Click "Execute Workflow"
3. View execution details for each node
4. Check input/output data
5. Review error messages

**Logging**:
- Use "Set" node to log intermediate values
- Add "Stop And Error" node to halt on specific conditions
- Check n8n logs: `docker logs n8n`

### Load Testing

**Simulate Multiple Requests**:
```bash
# Generate 10 concurrent content requests
for i in {1..10}; do
  curl -X POST http://localhost:5678/webhook/content-generate \
    -H "Content-Type: application/json" \
    -d "{\"campaign_id\": 1, \"topic\": \"Topic $i\"}" &
done
wait
```

## Workflow Best Practices

### 1. Naming Conventions

- **Workflows**: Lowercase with underscores (e.g., `content_generation.json`)
- **Nodes**: Title case with action (e.g., "Get Campaign Details")
- **Webhook paths**: Kebab-case (e.g., `/webhook/content-generate`)

### 2. Documentation

- Add notes to complex nodes
- Document expected input/output
- Include examples in webhook descriptions

### 3. Performance

- Use parallel processing for independent tasks
- Cache frequently accessed data in Redis
- Limit database queries with batch operations

### 4. Security

- Never log sensitive data (passwords, API keys)
- Validate all webhook inputs
- Use environment variables for credentials

### 5. Monitoring

- Add logging nodes for critical steps
- Track execution times
- Set up alerts for failures

## Troubleshooting

### Common Issues

**Issue**: Workflow times out
- **Solution**: Increase timeout in settings, optimize slow nodes

**Issue**: Database connection errors
- **Solution**: Check PostgreSQL credentials in `.env`, verify container is running

**Issue**: LLM returns empty response
- **Solution**: Check Ollama service status, verify model is loaded

**Issue**: Webhook not triggering
- **Solution**: Check webhook URL, verify n8n is accessible, check firewall

**Issue**: Parallel processing fails
- **Solution**: Reduce batch size, check for resource limits

### Debug Checklist

1. ✅ Check all services are running (`docker-compose ps`)
2. ✅ Verify environment variables are set
3. ✅ Test database connection
4. ✅ Check n8n logs for errors
5. ✅ Validate webhook payload format
6. ✅ Test individual nodes in isolation
7. ✅ Review execution history in n8n UI

## Conclusion

These 10 workflows form the complete automation pipeline for the B2B Marketing Automation Platform. Each workflow is designed to be:

- **Modular**: Can be tested and deployed independently
- **Scalable**: Parallel processing for performance
- **Resilient**: Error handling and retries
- **Maintainable**: Clear structure and documentation

For additional help, refer to:
- n8n Documentation: https://docs.n8n.io
- API Reference: `docs/api_reference.md`
- Architecture Guide: `docs/architecture.md`
