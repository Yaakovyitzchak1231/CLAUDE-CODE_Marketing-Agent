# B2B Marketing Automation Platform - Setup Guide

Complete step-by-step guide to deploy and configure the marketing automation system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Service Configuration](#service-configuration)
4. [LangChain Service Setup](#langchain-service-setup)
5. [n8n Workflow Import](#n8n-workflow-import)
6. [Streamlit Dashboard Setup](#streamlit-dashboard-setup)
7. [Publishing Integration](#publishing-integration)
8. [Testing & Verification](#testing--verification)
9. [Production Deployment](#production-deployment)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware Requirements

**Minimum** (Development/Testing):
- CPU: 4 cores
- RAM: 16GB
- Storage: 50GB SSD
- GPU: Not required (CPU-only Ollama)

**Recommended** (Production):
- CPU: 8+ cores
- RAM: 32GB+
- Storage: 100GB+ SSD
- GPU: NVIDIA GPU with 8GB+ VRAM (for faster LLM inference)

### Software Requirements

- **Operating System**: Linux (Ubuntu 22.04+), macOS, or Windows with WSL2
- **Docker**: Version 24.0+ with Docker Compose V2
- **Git**: Version 2.30+
- **Python**: Version 3.11+ (for local development)
- **Node.js**: Version 18+ (optional, for n8n CLI)

### API Accounts

1. **OpenAI** (for DALL-E 3):
   - Create account at https://platform.openai.com
   - Generate API key
   - Add payment method (pay-as-you-go)

2. **LinkedIn** (for publishing):
   - Create LinkedIn developer app at https://www.linkedin.com/developers
   - Configure OAuth 2.0 with redirect URLs
   - Request permissions: `w_member_social`, `r_liteprofile`

3. **WordPress** (optional):
   - WordPress site with XML-RPC enabled
   - Create application password (Settings → Account Security)

4. **SMTP Email** (optional):
   - Gmail with app password OR
   - Mailgun/SendGrid account

### Download Requirements

- Total download size: ~15GB
- Ollama models: ~4GB (Llama 3 7B)
- Docker images: ~10GB
- Dependencies: ~1GB

---

## Infrastructure Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/Yaakovyitzchak1231/marketing-agent.git
cd marketing-agent
```

### Step 2: Create Environment File

Copy the environment template:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=marketing_db
POSTGRES_USER=marketing_user
POSTGRES_PASSWORD=your_secure_password_here

# Ollama
OLLAMA_HOST=http://ollama:11434

# OpenAI (for DALL-E 3)
OPENAI_API_KEY=sk-your_openai_api_key_here

# Runway ML (for video generation)
RUNWAY_API_KEY=your_runway_api_key_here

# LinkedIn
LINKEDIN_ACCESS_TOKEN=your_linkedin_oauth_token_here

# WordPress
WORDPRESS_URL=https://yourblog.com
WORDPRESS_USERNAME=your_username
WORDPRESS_PASSWORD=your_app_password

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=your_app_password

# n8n
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your_n8n_password

# Security
SESSION_SECRET_KEY=generate_random_secret_key_here
```

### Step 3: Create docker-compose.yml

The main infrastructure file orchestrating all 13 services:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:16-alpine
    container_name: marketing_postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Chroma Vector Database
  chroma:
    image: chromadb/chroma:latest
    container_name: marketing_chroma
    volumes:
      - chroma_data:/chroma/chroma
    ports:
      - "8000:8000"
    environment:
      ALLOW_RESET: true

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: marketing_redis
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes

  # Ollama LLM Service
  ollama:
    image: ollama/ollama:latest
    container_name: marketing_ollama
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
    # Uncomment for GPU support:
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  # SearXNG Meta-Search Engine
  searxng:
    image: searxng/searxng:latest
    container_name: marketing_searxng
    volumes:
      - ./searxng/settings.yml:/etc/searxng/settings.yml
    ports:
      - "8080:8080"
    environment:
      SEARXNG_SECRET: ${SESSION_SECRET_KEY}

  # Scrapy Service
  scrapy:
    build: ./scrapy-service
    container_name: marketing_scrapy
    volumes:
      - ./scrapy-service/spiders:/app/spiders
      - ./scrapy-service/output:/app/output
    ports:
      - "6800:6800"

  # Playwright Service
  playwright:
    build: ./playwright-service
    container_name: marketing_playwright
    ports:
      - "8002:8002"
    shm_size: 2gb

  # LangChain Service (AI Agents)
  langchain-service:
    build: ./langchain-service
    container_name: marketing_langchain
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      CHROMA_HOST: http://chroma:8000
      REDIS_HOST: redis
      REDIS_PORT: 6379
      OLLAMA_HOST: http://ollama:11434
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      RUNWAY_API_KEY: ${RUNWAY_API_KEY}
      SEARXNG_URL: http://searxng:8080
    ports:
      - "8001:8001"
    depends_on:
      - postgres
      - chroma
      - redis
      - ollama
      - searxng

  # n8n Workflow Automation
  n8n:
    image: n8nio/n8n:latest
    container_name: marketing_n8n
    environment:
      N8N_BASIC_AUTH_ACTIVE: ${N8N_BASIC_AUTH_ACTIVE}
      N8N_BASIC_AUTH_USER: ${N8N_BASIC_AUTH_USER}
      N8N_BASIC_AUTH_PASSWORD: ${N8N_BASIC_AUTH_PASSWORD}
      N8N_HOST: n8n
      N8N_PORT: 5678
      N8N_PROTOCOL: http
      WEBHOOK_URL: http://n8n:5678
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
      - ./n8n-workflows:/workflows
    depends_on:
      - postgres
      - langchain-service

  # Streamlit Dashboard
  streamlit:
    build: ./streamlit-dashboard
    container_name: marketing_streamlit
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      N8N_WEBHOOK_URL: http://n8n:5678/webhook
    ports:
      - "8501:8501"
    depends_on:
      - postgres

  # Matomo Analytics
  matomo:
    image: matomo:latest
    container_name: marketing_matomo
    environment:
      MATOMO_DATABASE_HOST: postgres
      MATOMO_DATABASE_ADAPTER: pdo_pgsql
      MATOMO_DATABASE_TABLES_PREFIX: matomo_
      MATOMO_DATABASE_USERNAME: ${POSTGRES_USER}
      MATOMO_DATABASE_PASSWORD: ${POSTGRES_PASSWORD}
      MATOMO_DATABASE_DBNAME: ${POSTGRES_DB}
    ports:
      - "9000:80"
    volumes:
      - matomo_data:/var/www/html
    depends_on:
      - postgres

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: marketing_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - n8n
      - streamlit
      - matomo

volumes:
  postgres_data:
  chroma_data:
  redis_data:
  ollama_data:
  n8n_data:
  matomo_data:
```

### Step 4: Initialize Database Schema

Create `init-scripts/init.sql`:

```sql
-- Database initialization script
-- Run automatically on first PostgreSQL startup

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    company VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    target_audience TEXT,
    branding_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content drafts table
CREATE TABLE IF NOT EXISTS content_drafts (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    seo_score INTEGER,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Content versions table
CREATE TABLE IF NOT EXISTS content_versions (
    id SERIAL PRIMARY KEY,
    draft_id INTEGER REFERENCES content_drafts(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(draft_id, version_number)
);

-- Review feedback table
CREATE TABLE IF NOT EXISTS review_feedback (
    id SERIAL PRIMARY KEY,
    draft_id INTEGER REFERENCES content_drafts(id) ON DELETE CASCADE,
    reviewer VARCHAR(100),
    feedback_text TEXT,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    suggested_edits JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Media assets table
CREATE TABLE IF NOT EXISTS media_assets (
    id SERIAL PRIMARY KEY,
    draft_id INTEGER REFERENCES content_drafts(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500),
    url VARCHAR(500),
    prompt TEXT,
    api_provider VARCHAR(100),
    metadata_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Media edits table
CREATE TABLE IF NOT EXISTS media_edits (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES media_assets(id) ON DELETE CASCADE,
    edit_type VARCHAR(100),
    edit_params JSONB,
    edited_file_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Competitors table
CREATE TABLE IF NOT EXISTS competitors (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    name VARCHAR(255),
    url VARCHAR(500),
    last_scraped TIMESTAMP,
    data_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Market insights table
CREATE TABLE IF NOT EXISTS market_insights (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id) ON DELETE CASCADE,
    segment VARCHAR(255),
    insights_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trends table
CREATE TABLE IF NOT EXISTS trends (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(255) NOT NULL,
    score INTEGER,
    source VARCHAR(100),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Published content table
CREATE TABLE IF NOT EXISTS published_content (
    id SERIAL PRIMARY KEY,
    draft_id INTEGER REFERENCES content_drafts(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,
    url VARCHAR(500),
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Engagement metrics table
CREATE TABLE IF NOT EXISTS engagement_metrics (
    id SERIAL PRIMARY KEY,
    content_id INTEGER REFERENCES published_content(id) ON DELETE CASCADE,
    views INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_content_campaign_id ON content_drafts(campaign_id);
CREATE INDEX IF NOT EXISTS idx_content_status ON content_drafts(status);
CREATE INDEX IF NOT EXISTS idx_media_draft_id ON media_assets(draft_id);
CREATE INDEX IF NOT EXISTS idx_published_draft_id ON published_content(draft_id);
CREATE INDEX IF NOT EXISTS idx_engagement_content_id ON engagement_metrics(content_id);
CREATE INDEX IF NOT EXISTS idx_trends_detected_at ON trends(detected_at DESC);

-- Insert default admin user
INSERT INTO users (email, company) VALUES ('admin@example.com', 'Marketing Automation')
ON CONFLICT (email) DO NOTHING;
```

### Step 5: Start Infrastructure

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

Wait for all services to become healthy (~2-3 minutes).

---

## Service Configuration

### Configure Ollama

Pull the Llama 3 model:

```bash
docker exec -it marketing_ollama ollama pull llama3
```

Verify model is loaded:

```bash
docker exec -it marketing_ollama ollama list
```

Test inference:

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "What is B2B marketing?"
}'
```

### Configure SearXNG

Edit `searxng/settings.yml`:

```yaml
general:
  instance_name: "Marketing Search"

search:
  safe_search: 0
  autocomplete: "google"

engines:
  - name: google
    disabled: false

  - name: bing
    disabled: false

  - name: duckduckgo
    disabled: false

  - name: reddit
    disabled: false

  - name: hackernews
    disabled: false

server:
  secret_key: "${SEARXNG_SECRET}"
  bind_address: "0.0.0.0"
  port: 8080

outgoing:
  request_timeout: 10.0
  max_request_timeout: 30.0
```

Restart SearXNG:

```bash
docker-compose restart searxng
```

---

## LangChain Service Setup

### Install Dependencies

The LangChain service is already containerized. To modify locally:

```bash
cd langchain-service
pip install -r requirements.txt
```

### Test Agent Endpoints

```bash
# Test Research Agent
curl -X POST http://localhost:8001/agents/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "B2B marketing automation trends 2024"
  }'

# Test Content Agent
curl -X POST http://localhost:8001/agents/content \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI in Marketing",
    "target_audience": "Marketing managers at B2B tech companies"
  }'
```

---

## n8n Workflow Import

### Access n8n Dashboard

1. Open browser to http://localhost:5678
2. Login with credentials from `.env`:
   - Username: `admin`
   - Password: `your_n8n_password`

### Import Workflows

1. Click "Workflows" → "Import from File"
2. Import each workflow from `n8n-workflows/`:
   - `user_onboarding.json`
   - `research_pipeline.json`
   - `content_generation.json`
   - `image_generation.json`
   - `video_generation.json`
   - `content_review_loop.json`
   - `media_post_processing.json`
   - `publishing_pipeline.json`
   - `engagement_tracking.json`
   - `trend_monitoring.json`

3. Activate each workflow

### Configure Credentials

For each workflow, configure:

1. **PostgreSQL**:
   - Host: `postgres`
   - Port: `5432`
   - Database: `marketing_db`
   - User/Password: from `.env`

2. **HTTP Request nodes**:
   - LangChain URL: `http://langchain-service:8001`
   - n8n Webhook URL: `http://n8n:5678/webhook`

---

## Streamlit Dashboard Setup

The dashboard is accessible at http://localhost:8501

### First-Time Setup

1. Navigate to "Profile" page
2. Complete onboarding wizard:
   - Enter email and company info
   - Define target audience
   - Set brand guidelines
   - Choose content preferences

3. Create your first campaign:
   - Go to "Campaigns" page
   - Click "Create New Campaign"
   - Fill in campaign details

---

## Publishing Integration

### LinkedIn Setup

1. Create LinkedIn App:
   - Go to https://www.linkedin.com/developers/apps
   - Create new app
   - Add OAuth redirect URL: `http://localhost:5678/oauth/callback`

2. Get Access Token:
   ```bash
   # Use LinkedIn OAuth 2.0 flow
   # Or use Postman to get token manually
   ```

3. Add to `.env`:
   ```bash
   LINKEDIN_ACCESS_TOKEN=your_token_here
   ```

### WordPress Setup

1. Enable XML-RPC on your WordPress site
2. Create application password:
   - WordPress Admin → Users → Profile
   - Scroll to "Application Passwords"
   - Create new password

3. Add to `.env`:
   ```bash
   WORDPRESS_URL=https://yourblog.com
   WORDPRESS_USERNAME=your_username
   WORDPRESS_PASSWORD=application_password
   ```

### Email Setup (Gmail)

1. Enable 2-Factor Authentication
2. Create app password:
   - Google Account → Security → 2-Step Verification → App passwords
   - Select "Mail" and generate

3. Add to `.env`:
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your.email@gmail.com
   SMTP_PASSWORD=app_password
   ```

---

## Testing & Verification

### End-to-End Test

```bash
# Run test script
cd tests
python test_e2e.py
```

This will:
1. Create test campaign
2. Generate content
3. Generate images
4. Submit for review
5. Approve and publish
6. Track engagement

### Manual Testing

1. **Create Campaign**:
   - Dashboard → Campaigns → Create
   - Fill in details, save

2. **Generate Content**:
   - Trigger `content_generation` workflow in n8n
   - Check PostgreSQL for new draft

3. **Review Content**:
   - Dashboard → Content Review
   - Approve draft

4. **Publish**:
   - Trigger `publishing_pipeline` workflow
   - Verify post on LinkedIn/WordPress

---

## Production Deployment

### Security Hardening

1. **Change all default passwords**
2. **Enable HTTPS** (update nginx config)
3. **Set up firewall rules**
4. **Enable database backups**
5. **Rotate API keys regularly**

### Monitoring

Add monitoring stack:

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    # ... configuration

  grafana:
    image: grafana/grafana
    # ... configuration
```

### Backups

```bash
# Database backup script
docker exec marketing_postgres pg_dump -U marketing_user marketing_db > backup.sql

# Restore
cat backup.sql | docker exec -i marketing_postgres psql -U marketing_user marketing_db
```

---

## Troubleshooting

### Common Issues

**Issue: Ollama model not loaded**
```bash
docker exec -it marketing_ollama ollama pull llama3
```

**Issue: PostgreSQL connection refused**
```bash
docker-compose restart postgres
docker-compose logs postgres
```

**Issue: n8n workflows not triggering**
- Check webhook URLs
- Verify credentials
- Check execution logs in n8n

**Issue: Out of memory**
- Increase Docker memory limit
- Reduce Ollama model size (use smaller variant)
- Add swap space

### Getting Help

- GitHub Issues: https://github.com/Yaakovyitzchak1231/marketing-agent/issues
- Documentation: See `/docs` folder
- Logs: `docker-compose logs [service_name]`

---

## Next Steps

1. Create your first campaign
2. Generate content
3. Review and approve
4. Publish to channels
5. Monitor analytics

Congratulations! Your B2B Marketing Automation Platform is now running.
