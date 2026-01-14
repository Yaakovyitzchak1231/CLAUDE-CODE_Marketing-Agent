# B2B Marketing Automation Platform - Project Structure

## Repository Overview

This document provides a complete guide to the project structure, explaining what each directory and file does.

---

## Root Directory

```
marketing-system/
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
├── docker-compose.yml              # Multi-container orchestration
├── README.md                       # Project overview and quick start
├── SETUP_GUIDE.md                  # Detailed setup instructions
├── TESTING_CHECKLIST.md            # Comprehensive testing guide
├── PROJECT_STRUCTURE.md            # This file - repository documentation
├── test-services.sh                # Service health check script (Linux/Mac)
├── test-services.ps1               # Service health check script (Windows)
└── Agent Architecture - Supervisor Pattern.png  # Architecture diagram
```

### Key Files

**`.env.example`**
- Template for environment variables
- Copy to `.env` and fill in your credentials
- Never commit `.env` to git (contains secrets)

**`docker-compose.yml`**
- Defines all 13 services (PostgreSQL, n8n, Ollama, etc.)
- Service configuration and networking
- Volume mappings for persistence
- Port exposures

**`README.md`**
- Quick start guide
- System overview
- Feature highlights
- Basic installation steps

**`SETUP_GUIDE.md`**
- 40-step detailed deployment guide
- Service-by-service configuration
- Troubleshooting common issues

**`TESTING_CHECKLIST.md`**
- Phase-by-phase testing guide
- Service health checks
- E2E workflow testing
- Performance benchmarks

---

## Directory Structure

### `/docs` - Documentation

```
docs/
├── setup_guide.md          # Comprehensive setup documentation
├── api_reference.md        # API endpoints and schemas
├── architecture.md         # System architecture deep dive
├── workflow_guide.md       # n8n workflow documentation
├── testing_summary.md      # Test coverage and results
└── video_tutorials.md      # Video tutorial scripts
```

**Purpose**: Complete system documentation for deployment, development, and maintenance.

**When to use**:
- Setting up the system for the first time
- Understanding API endpoints
- Learning about system architecture
- Creating video tutorials
- Reviewing test coverage

---

### `/init-scripts` - Database Initialization

```
init-scripts/
└── init.sql                # PostgreSQL schema and seed data
```

**Purpose**: Initializes PostgreSQL database with required schema.

**Tables Created**:
- `users` - User accounts and profiles
- `campaigns` - Marketing campaigns
- `content_drafts` - Generated content with versions
- `content_versions` - Content revision history
- `review_feedback` - Human review comments
- `media_assets` - Images and videos
- `media_edits` - Media editing history
- `published_content` - Published content tracking
- `engagement_metrics` - Analytics data
- `competitors` - Competitor profiles
- `market_insights` - Research findings
- `trends` - Trending topics

**Auto-executed**: Runs automatically when PostgreSQL container first starts.

---

### `/langchain-service` - AI Agent Framework

```
langchain-service/
├── agents/                 # Specialist agents
│   ├── __init__.py
│   ├── base_agent.py       # Base agent class (ReAct pattern)
│   ├── supervisor.py       # LangGraph supervisor orchestrator
│   ├── research_agent.py   # Market research and analysis
│   ├── competitor_agent.py # Competitor monitoring
│   ├── market_agent.py     # Audience segmentation
│   ├── content_agent.py    # Content generation
│   ├── image_agent.py      # Image generation (DALL-E/Midjourney)
│   ├── video_agent.py      # Video generation (Runway/Pika)
│   ├── trend_agent.py      # Trend detection
│   └── review_coordinator.py  # Human-in-the-loop coordination
│
├── chains/                 # LangChain sequential processing
│   ├── __init__.py
│   ├── seo_optimizer.py    # SEO optimization chain
│   ├── image_prompt_builder.py  # Content → Image prompts
│   ├── video_script_builder.py  # Content → Video scripts
│   └── content_synthesizer.py   # Research aggregation
│
├── tools/                  # Agent capabilities
│   ├── __init__.py
│   ├── searxng_tool.py     # SearXNG search integration
│   ├── scraping_tool.py    # Playwright/Scrapy wrapper
│   ├── dalle_tool.py       # DALL-E 3 API wrapper
│   ├── midjourney_tool.py  # Midjourney API wrapper
│   ├── runway_tool.py      # Runway ML API wrapper
│   ├── pika_tool.py        # Pika API wrapper
│   ├── ffmpeg_tool.py      # Video editing (stitching, captions)
│   └── vector_search.py    # Chroma semantic search
│
├── memory/                 # State management
│   ├── __init__.py
│   ├── vector_store.py     # Chroma vector DB manager
│   ├── conversation_buffer.py  # Conversation history
│   └── shared_context.py   # Cross-agent shared memory
│
├── state/                  # LangGraph state
│   ├── __init__.py
│   └── workflow_state.py   # State management for workflows
│
├── routes/                 # FastAPI endpoints
│   ├── __init__.py
│   ├── supervisor.py       # Supervisor agent endpoint
│   └── agents.py           # Individual agent endpoints
│
├── app.py                  # FastAPI server
├── requirements.txt        # Python dependencies
└── README.md              # Service documentation
```

**Purpose**: Core AI agent framework using LangChain and LangGraph.

**Key Patterns**:
- **Supervisor Pattern**: Central coordinator routes tasks to specialist agents
- **ReAct Pattern**: Agents reason and act in loops with tool usage
- **Shared Memory**: Cross-agent context sharing via vector store
- **Tool Registry**: Centralized access to search, scraping, APIs, models

**Endpoints**:
- `POST /supervisor` - Main entry point for task delegation
- `POST /agents/research` - Direct research agent invocation
- `POST /agents/content` - Direct content generation
- `POST /agents/image` - Direct image generation
- `POST /agents/video` - Direct video generation
- `GET /health` - Service health check

---

### `/n8n-workflows` - Workflow Orchestration

```
n8n-workflows/
├── user_onboarding.json         # Conversational signup wizard
├── research_pipeline.json       # Research agent orchestration
├── content_generation.json      # Text content creation
├── image_generation.json        # Image creation (DALL-E/Midjourney)
├── video_generation.json        # Video creation (Runway/Pika)
├── content_review_loop.json     # Human-in-the-loop review
├── media_post_processing.json   # Image/video optimization
├── publishing_pipeline.json     # Multi-channel publishing
├── engagement_tracking.json     # Real-time analytics
└── trend_monitoring.json        # Scheduled trend analysis
```

**Purpose**: n8n workflow definitions for automating marketing processes.

**Import Instructions**:
1. Open n8n UI: http://localhost:5678
2. Settings → Import Workflow
3. Upload each JSON file
4. Activate workflows

**Common Patterns**:
- **Webhook Triggers**: Async processing via HTTP webhooks
- **Scheduled Triggers**: Cron-based recurring tasks
- **Database Nodes**: PostgreSQL read/write operations
- **HTTP Request Nodes**: Call LangChain service APIs
- **Code Nodes**: JavaScript transformations
- **Conditional Branching**: IF/Switch nodes for routing

---

### `/streamlit-dashboard` - User Interface

```
streamlit-dashboard/
├── pages/                  # Multi-page app structure
│   ├── content_review.py   # Text content review interface
│   ├── media_review.py     # Image/video review interface
│   ├── asset_library.py    # Browse and reuse media assets
│   ├── analytics.py        # Campaign performance dashboards
│   ├── campaigns.py        # Campaign management CRUD
│   └── onboarding.py       # User profiling wizard
│
├── components/             # Reusable UI components
│   ├── content_editor.py   # Rich text editor with annotations
│   ├── image_editor.py     # Image crop/resize/filter tools
│   └── video_player.py     # Video preview with timeline
│
├── utils/                  # Helper functions
│   ├── database.py         # Database connection utilities
│   └── api_client.py       # n8n webhook client
│
├── app.py                  # Main dashboard entry point
├── requirements.txt        # Python dependencies
└── README.md              # Dashboard documentation
```

**Purpose**: Interactive web dashboard for content review and campaign management.

**Key Features**:
- **Content Review**: Side-by-side diff editor, inline feedback, version history
- **Media Review**: Image editor (crop, resize, filters), video player (trim, captions)
- **Asset Library**: Search/filter previous media, reuse in campaigns
- **Analytics**: Time series charts, channel comparison, engagement metrics
- **Campaigns**: Create/edit/delete campaigns, view content pipeline

**Access**: http://localhost:8501

**Tech Stack**:
- Streamlit (Python web framework)
- PostgreSQL (psycopg2)
- Plotly (interactive charts)
- Pillow (image processing)

---

### `/publishing` - Publishing Adapters

```
publishing/
├── linkedin_publisher.py   # LinkedIn v2 API client
├── wordpress_publisher.py  # WordPress XML-RPC client
├── email_publisher.py      # SMTP email client
├── __init__.py            # Package exports
├── requirements.txt       # Python dependencies
└── README.md             # Publishing documentation
```

**Purpose**: Multi-channel publishing with unified interface.

**Supported Channels**:
- **LinkedIn**: OAuth 2.0, ugcPosts API, image/video attachments
- **WordPress**: XML-RPC, create/update posts, media upload
- **Email**: SMTP with TLS, HTML templates, inline images

**Usage Pattern**:
```python
from publishing import LinkedInPublisher

publisher = LinkedInPublisher(access_token)
publisher.create_text_post("Hello LinkedIn!")
publisher.create_image_post("Check this out", image_url)
```

---

### `/tests` - Testing Infrastructure

```
tests/
├── __init__.py
├── conftest.py                      # Pytest fixtures and config
├── requirements.txt                 # Test dependencies
├── README.md                        # Testing documentation
│
├── test_e2e_content_generation.py   # Content workflow tests
├── test_e2e_media_generation.py     # Image/video workflow tests
├── test_e2e_review_workflow.py      # Review loop tests
├── test_e2e_publishing.py           # Publishing pipeline tests
│
├── load_test_workflows.py           # Locust load testing
└── run_tests.py                     # Test runner script
```

**Purpose**: Comprehensive testing suite for validation.

**Test Categories**:
- **Integration Tests**: Require running services (marked `@pytest.mark.integration`)
- **E2E Tests**: Complete workflows (marked `@pytest.mark.e2e`)
- **Load Tests**: Performance testing with Locust

**Running Tests**:
```bash
# Service health check
python tests/run_tests.py --services

# Quick tests (< 1 min)
python tests/run_tests.py --quick

# Full E2E suite (~5 min)
python tests/run_tests.py --e2e

# With coverage report
python tests/run_tests.py --coverage

# Load testing
python tests/run_tests.py --load
```

**Coverage**: 91% average across 29 tests

---

### Service-Specific Directories

#### `/chroma-init` - Vector Database Setup
```
chroma-init/
├── init.py                 # Create default collections
└── README.md              # Configuration guide
```
**Collections**: user_profiles, content_library, market_segments, competitor_content

#### `/playwright-service` - Browser Automation
```
playwright-service/
├── app.py                  # FastAPI server
├── scraper.py             # Scraping logic
├── requirements.txt       # Dependencies
└── README.md             # Usage guide
```
**Endpoints**: `/scrape`, `/screenshot`, `/pdf`

#### `/scrapy-service` - Web Scraping
```
scrapy-service/
├── spiders/               # Scrapy spiders
│   ├── competitor.py      # Competitor content scraper
│   └── news.py           # News/trend scraper
├── settings.py           # Scrapy configuration
├── requirements.txt      # Dependencies
└── README.md            # Spider documentation
```

#### `/matomo` - Analytics Configuration
```
matomo/
├── config.ini.php        # Matomo configuration
└── README.md            # Setup instructions
```
**Access**: http://localhost:9000

#### `/nginx` - Reverse Proxy
```
nginx/
├── nginx.conf            # Reverse proxy config
└── README.md            # Configuration guide
```
**Routes**: Proxies all services through single domain

#### `/ollama` - LLM Configuration
```
ollama/
├── Modelfile             # Custom model configurations
└── README.md            # Model management guide
```
**Models**: llama3, mistral, mixtral

#### `/redis` - Cache Configuration
```
redis/
├── redis.conf            # Redis configuration
└── README.md            # Usage guide
```

#### `/searxng` - Search Engine
```
searxng/
├── settings.yml          # Search engine configuration
└── README.md            # Configuration guide
```
**Access**: http://localhost:8080

---

## Data Flow Architecture

### 1. Content Generation Flow
```
User Input (Streamlit/n8n)
    ↓
n8n Workflow (content_generation.json)
    ↓
LangChain Supervisor (/supervisor)
    ↓
Research Agent → SearXNG + Scrapy → Research Data
    ↓
Content Agent → Ollama LLM → Draft Content
    ↓
PostgreSQL (content_drafts table)
    ↓
Chroma Vector DB (embeddings)
    ↓
Streamlit Review Dashboard
    ↓
Human Review → Feedback
    ↓
n8n Review Loop (content_review_loop.json)
    ↓
Content Agent → LLM Revision → Updated Draft
    ↓
Approval → Publishing Pipeline
```

### 2. Image Generation Flow
```
Content Draft (PostgreSQL)
    ↓
n8n Workflow (image_generation.json)
    ↓
Image Agent (/agents/image)
    ↓
Image Prompt Builder Chain
    ↓
DALL-E 3 / Midjourney API
    ↓
Image URL
    ↓
Media Post-Processing (n8n)
    ↓
FFmpeg (resize, watermark, optimize)
    ↓
PostgreSQL (media_assets table)
    ↓
Streamlit Media Review Dashboard
```

### 3. Publishing Flow
```
Approved Content (status: approved)
    ↓
n8n Workflow (publishing_pipeline.json)
    ↓
Channel-Specific Formatting
    ↓
Publishing Adapters
    ├─→ LinkedIn API → LinkedIn Post
    ├─→ WordPress XML-RPC → Blog Post
    └─→ SMTP → Email Newsletter
    ↓
PostgreSQL (published_content table)
    ↓
Engagement Tracking (n8n)
    ↓
Matomo Analytics
    ↓
PostgreSQL (engagement_metrics table)
    ↓
Streamlit Analytics Dashboard
```

---

## Configuration Files

### Environment Variables (`.env`)

**Required Variables**:
```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=marketing_db
POSTGRES_USER=marketing_user
POSTGRES_PASSWORD=your_secure_password

# n8n
N8N_BASE_URL=http://localhost:5678
N8N_WEBHOOK_URL=http://localhost:5678/webhook

# LangChain Service
LANGCHAIN_SERVICE_URL=http://localhost:8001

# Ollama
OLLAMA_MODEL=llama3
```

**Optional Variables** (for full features):
```bash
# Media Generation
OPENAI_API_KEY=sk-...                    # For DALL-E 3
MIDJOURNEY_API_KEY=...                   # For Midjourney
RUNWAY_API_KEY=...                       # For Runway ML
PIKA_API_KEY=...                         # For Pika

# Publishing
LINKEDIN_ACCESS_TOKEN=...                # LinkedIn API
WORDPRESS_URL=https://yourblog.com
WORDPRESS_USERNAME=...
WORDPRESS_PASSWORD=...
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...

# Analytics
MATOMO_SITE_ID=1
MATOMO_AUTH_TOKEN=...
```

---

## Port Allocation

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Database |
| n8n | 5678 | Workflow UI & Webhooks |
| Streamlit | 8501 | Dashboard |
| LangChain Service | 8001 | AI Agents API |
| Chroma | 8000 | Vector Database |
| Ollama | 11434 | LLM Inference |
| SearXNG | 8080 | Search Engine |
| Matomo | 9000 | Analytics |
| Redis | 6379 | Cache |
| Nginx | 80 | Reverse Proxy |
| Playwright Service | 8002 | Browser Automation |
| Scrapy Service | 6800 | Web Scraping |

---

## Development Workflow

### Adding a New Agent

1. **Create agent file**: `langchain-service/agents/my_agent.py`
2. **Implement base class**:
   ```python
   from agents.base_agent import BaseAgent

   class MyAgent(BaseAgent):
       def run(self, task: str, context: dict) -> dict:
           # Agent logic here
           pass
   ```
3. **Add tools**: Create tools in `langchain-service/tools/`
4. **Update supervisor**: Add agent to supervisor routing
5. **Create API endpoint**: Add route in `langchain-service/routes/agents.py`
6. **Create n8n workflow**: Build workflow using new agent
7. **Add tests**: Create test file in `tests/`
8. **Update documentation**: Add to `docs/architecture.md`

### Adding a New Workflow

1. **Design in n8n UI**: http://localhost:5678
2. **Test with sample data**
3. **Export to JSON**: Settings → Export Workflow
4. **Save to** `n8n-workflows/my_workflow.json`
5. **Document in** `docs/workflow_guide.md`
6. **Add test**: Create test scenario in `tests/`
7. **Commit to git**

### Adding a New Publishing Channel

1. **Create adapter**: `publishing/my_channel_publisher.py`
2. **Implement interface**:
   ```python
   class MyChannelPublisher:
       def publish_content(self, content: str, media: List[str]) -> Dict:
           pass
   ```
3. **Add to** `publishing/__init__.py`
4. **Update n8n workflow**: Add channel to `publishing_pipeline.json`
5. **Add configuration**: Add credentials to `.env.example`
6. **Document**: Update `publishing/README.md`
7. **Test**: Add test to `tests/test_e2e_publishing.py`

---

## Maintenance Tasks

### Daily
- [ ] Check Docker container health: `docker-compose ps`
- [ ] Review error logs: `docker-compose logs --tail=100`
- [ ] Monitor disk space usage

### Weekly
- [ ] Run health checks: `python tests/run_tests.py --services`
- [ ] Review engagement metrics in Streamlit
- [ ] Check for failed workflows in n8n
- [ ] Backup PostgreSQL database

### Monthly
- [ ] Run full test suite: `python tests/run_tests.py --e2e`
- [ ] Update Python dependencies
- [ ] Review and rotate API keys
- [ ] Performance load testing
- [ ] Security audit

### Quarterly
- [ ] Update Docker images: `docker-compose pull`
- [ ] Review and optimize database indexes
- [ ] Archive old analytics data
- [ ] Update documentation
- [ ] Review and update agent prompts

---

## Deployment Checklist

See `TESTING_CHECKLIST.md` for complete deployment validation.

**Quick Checklist**:
1. ✅ Clone repository
2. ✅ Configure `.env` file
3. ✅ Start Docker containers
4. ✅ Initialize databases
5. ✅ Import n8n workflows
6. ✅ Pull Ollama models
7. ✅ Run service health checks
8. ✅ Run test suite
9. ✅ Verify dashboard accessible
10. ✅ Test content generation flow

---

## Troubleshooting

### Common Issues

**"Docker containers won't start"**
- Check: Docker Desktop running, ports not in use, disk space available
- Fix: `docker-compose down && docker-compose up -d`

**"Database connection failed"**
- Check: PostgreSQL container running, credentials in `.env` correct
- Fix: Restart PostgreSQL: `docker-compose restart postgres`

**"LLM inference is slow"**
- Check: GPU available, model size appropriate for system
- Fix: Use smaller model (mistral vs llama3:70b), add GPU

**"n8n workflows fail"**
- Check: LangChain service responding, database accessible
- Fix: Review workflow execution logs in n8n UI

**"Tests are failing"**
- Check: All services running, `.env` configured correctly
- Fix: Run service health check: `python tests/run_tests.py --services`

---

## Resource Requirements

### Minimum (MVP - Text Only)
- **CPU**: 4 cores
- **RAM**: 16GB
- **Storage**: 50GB
- **GPU**: Not required (CPU inference)

### Recommended (Full Features)
- **CPU**: 8+ cores
- **RAM**: 32GB
- **Storage**: 100GB SSD
- **GPU**: NVIDIA GPU with 8GB+ VRAM (for faster LLM inference)

### Production (Multi-User)
- **CPU**: 16+ cores
- **RAM**: 64GB
- **Storage**: 500GB SSD
- **GPU**: NVIDIA GPU with 16GB+ VRAM
- **Network**: 100 Mbps+

---

## Contributing

### Code Style
- Python: PEP 8, type hints, docstrings
- JavaScript (n8n): ESLint standard
- SQL: Lowercase keywords, snake_case tables
- Markdown: ATX headers, fenced code blocks

### Git Workflow
1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test locally
3. Commit with descriptive message: `git commit -m "Add feature: ..."`
4. Push to GitHub: `git push origin feature/my-feature`
5. Create pull request
6. Await review and merge

### Testing Requirements
- All new features must include tests
- Existing tests must pass
- Coverage should not decrease
- Performance benchmarks must be met

---

## License

This project integrates multiple open-source components. See individual component licenses.

---

## Support & Resources

**Documentation**:
- Setup Guide: `docs/setup_guide.md`
- API Reference: `docs/api_reference.md`
- Architecture: `docs/architecture.md`
- Workflows: `docs/workflow_guide.md`

**Community**:
- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share knowledge

**External Resources**:
- n8n Documentation: https://docs.n8n.io
- LangChain Documentation: https://python.langchain.com
- Ollama Documentation: https://ollama.ai/docs
- Streamlit Documentation: https://docs.streamlit.io

---

**Last Updated:** January 14, 2026
**Version:** 1.0
**Maintainer:** Development Team
