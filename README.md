# Open-Source B2B Marketing Automation Platform

## Architecture Overview

A comprehensive multi-agent marketing automation system built entirely with open-source tools, featuring content generation, review workflows, competitor analysis, and multi-channel publishing.

### Key Features
- **Self-hosted LLMs** (Ollama with Llama 3/Mistral)
- **Multi-agent orchestration** via n8n workflows
- **Content review & feedback loop** with approval workflows
- **Competitor intelligence** via web scraping
- **Vector-based semantic search** for market insights
- **Multi-channel publishing** (LinkedIn, WordPress, Email)
- **Real-time analytics** with Matomo
- **GDPR-compliant** data handling

## System Components

### Core Infrastructure
- **n8n** - Workflow orchestration and agent coordination
- **Ollama** - Self-hosted LLM inference (Llama 3, Mistral)
- **PostgreSQL** - Primary relational database
- **Chroma** - Vector database for embeddings
- **Redis** - Caching and job queue

### AI & Analysis
- **LangChain** - Agent framework and chains
- **HuggingFace Models** - Sentiment analysis, NER, embeddings
- **Sentence Transformers** - Text embeddings

### Data Collection
- **SearXNG** - Meta-search engine
- **Scrapy** - Web scraping framework
- **Playwright** - Browser automation
- **Trafilatura** - Content extraction

### Publishing & Analytics
- **Matomo** - Web analytics
- **LinkedIn API** - Social publishing
- **WordPress XML-RPC** - Blog publishing
- **SMTP** - Email campaigns

### User Interface
- **Streamlit** - Interactive dashboard
- **n8n Web UI** - Workflow management

## Content Review & Feedback System

The platform includes a sophisticated content review workflow:

1. **Content Generation** → AI creates draft content
2. **Review Queue** → Content enters review dashboard
3. **Human Review** → User reviews via Streamlit UI or email
4. **Feedback Loop** → Comments/edits sent back to AI
5. **Revision** → AI regenerates based on feedback
6. **Approval** → Final approval before publishing
7. **Scheduling** → Queue for optimal posting times

### Review Workflow Features
- Side-by-side content comparison
- Inline editing and comments
- Version history tracking
- Multi-stakeholder approval
- Email notifications for review requests
- Mobile-friendly review interface
- Bulk approval/rejection
- Content quality scoring

## Quick Start

### Prerequisites
- Docker & Docker Compose
- 16GB+ RAM (32GB recommended for LLMs)
- NVIDIA GPU (optional, for faster LLM inference)
- 50GB+ free disk space

### Installation

**📋 Setup Guides:**
- **Windows users**: See [SETUP_WINDOWS.md](SETUP_WINDOWS.md) for Windows-specific instructions
- **Linux/Mac users**: See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup
- **Verification**: See [SETUP_VERIFICATION.md](SETUP_VERIFICATION.md) for testing

**Quick Start (Linux/Mac):**

```bash
# Clone repository
git clone https://github.com/Yaakovyitzchak1231/marketing-agent.git
cd marketing-agent

# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env

# Start all services
docker-compose up -d

# Wait 2-3 minutes for services to initialize

# Pull Ollama models (required)
docker exec -it ollama ollama pull llama3:8b
docker exec -it ollama ollama pull mistral:7b

# Initialize Chroma vector database
docker exec -it langchain_service python /app/chroma-init/init_collections.py

# Access services
# n8n: http://localhost:5678
# Dashboard: http://localhost:8501
# Matomo: http://localhost:8081
# Adminer (DB): http://localhost:8082
```

## Agent Architecture

### 1. Research Agent
- **Purpose**: Market research and trend analysis
- **Tools**: SearXNG, web scraping, NLP analysis
- **Output**: Research reports, trend data
- **Triggers**: Scheduled (daily/weekly), on-demand

### 2. Competitor Analysis Agent
- **Purpose**: Monitor competitor content and strategies
- **Tools**: Scrapy spiders, Playwright, sentiment analysis
- **Output**: Competitor insights, content gaps
- **Triggers**: Scheduled, on-demand

### 3. Target Market Analysis Agent
- **Purpose**: Audience profiling and segmentation
- **Tools**: Vector DB, clustering, NER
- **Output**: Buyer personas, segment profiles
- **Triggers**: On-demand, monthly refresh

### 4. Content Creation Agent
- **Purpose**: Generate marketing content
- **Tools**: Ollama LLM, LangChain chains, SEO tools
- **Output**: Blog posts, social content, emails
- **Triggers**: On-demand, content calendar

### 5. Content Review Agent
- **Purpose**: Coordinate human review and feedback
- **Tools**: n8n webhooks, email notifications, dashboard
- **Output**: Approved content, revision requests
- **Triggers**: Post-generation, scheduled reviews

### 6. Engagement Tracking Agent
- **Purpose**: Monitor content performance
- **Tools**: Matomo API, webhook receivers
- **Output**: Engagement metrics, performance reports
- **Triggers**: Real-time webhooks, scheduled aggregation

### 7. Publishing Agent
- **Purpose**: Multi-channel content distribution
- **Tools**: LinkedIn API, WordPress, SMTP
- **Output**: Published content, delivery confirmations
- **Triggers**: Scheduled, post-approval

### 8. Trend Tracking Agent
- **Purpose**: Monitor industry trends and news
- **Tools**: SearXNG, Reddit/HN scrapers, time-series analysis
- **Output**: Trending topics, content opportunities
- **Triggers**: Scheduled (hourly/daily)

## Database Schema

### PostgreSQL Databases
The system uses three PostgreSQL databases:
- `marketing` - Main application database (see tables below)
- `n8n` - n8n workflow execution data
- `matomo` - Analytics tracking data

### PostgreSQL Tables (marketing database)
- `users` - User profiles and preferences
- `campaigns` - Marketing campaign tracking
- `content_drafts` - Generated content with versions
- `content_versions` - Version history
- `review_feedback` - Review feedback and approvals
- `media_assets` - Generated images/videos
- `media_edits` - Media editing history
- `competitors` - Competitor profiles and data
- `market_insights` - Curated research findings
- `trends` - Trend tracking data
- `published_content` - Published content tracking
- `engagement_metrics` - Analytics data

### Chroma Collections
- `market_insights` - Vectorized research data
- `competitor_content` - Competitor analysis embeddings
- `user_preferences` - Personalization vectors
- `content_library` - Historical content embeddings

## Configuration

See `.env.example` for all configuration options.

Key settings:
- LLM model selection (Llama3, Mistral, etc.)
- Content review workflow (email vs dashboard)
- Publishing schedules and channels
- Analytics tracking configuration
- GDPR compliance settings

## GitHub Repositories Used

### Core Infrastructure
- n8n: https://github.com/n8n-io/n8n
- Ollama: https://github.com/ollama/ollama
- Chroma: https://github.com/chroma-core/chroma

### AI & ML
- LangChain: https://github.com/langchain-ai/langchain
- Sentence Transformers: https://github.com/UKPLab/sentence-transformers
- HuggingFace Models: https://huggingface.co/

### Scraping & Search
- SearXNG: https://github.com/searxng/searxng
- Scrapy: https://github.com/scrapy/scrapy
- Playwright: https://github.com/microsoft/playwright-python
- Trafilatura: https://github.com/adbar/trafilatura

### Analytics & UI
- Matomo: https://github.com/matomo-org/matomo
- Streamlit: https://github.com/streamlit/streamlit

## License

This project integrates multiple open-source components. See individual component licenses.

## Support

For issues and questions, please refer to the documentation in `/docs`.
