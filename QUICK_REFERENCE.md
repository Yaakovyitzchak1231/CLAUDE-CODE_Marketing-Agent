# B2B Marketing Automation Platform - Quick Reference Guide

## 📋 Essential Documents (Start Here)

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **README.md** | Project overview, quick start | First-time setup, understanding features |
| **SETUP_GUIDE.md** | Detailed installation steps | Deploying the system |
| **TESTING_CHECKLIST.md** | Complete testing guide | Validation before production |
| **PROJECT_STRUCTURE.md** | Repository layout explained | Understanding what each file does |
| **QUICK_REFERENCE.md** | This file - quick answers | Finding information fast |

---

## 🚀 Getting Started (5 Minutes)

### 1. **First Time Setup**
```bash
# Clone and configure
git clone https://github.com/Yaakovyitzchak1231/marketing-agent.git
cd marketing-agent
cp .env.example .env
# Edit .env with your credentials

# Start all services
docker-compose up -d

# Pull AI model
docker exec -it ollama ollama pull llama3

# Access dashboard
open http://localhost:8501
```

### 2. **Check Everything Works**
```bash
# Run health check
python tests/run_tests.py --services

# Expected: All services show ✓ green checkmark
```

### 3. **Test Content Generation**
1. Open dashboard: http://localhost:8501
2. Go to "Campaigns" page
3. Create new campaign
4. Navigate to "Content Review" to see generated content

---

## 📂 Where is Everything?

### "I want to..."

**...understand the system architecture**
→ Read: `docs/architecture.md`

**...set up the system for the first time**
→ Follow: `SETUP_GUIDE.md` or `docs/setup_guide.md`

**...test if everything works**
→ Use: `TESTING_CHECKLIST.md`

**...understand what each folder does**
→ Read: `PROJECT_STRUCTURE.md`

**...create a new AI agent**
→ Look at: `langchain-service/agents/` (use `base_agent.py` as template)

**...modify a workflow**
→ Edit in: n8n UI (http://localhost:5678) or `n8n-workflows/*.json`

**...add a new publishing channel**
→ Create in: `publishing/` (follow `linkedin_publisher.py` pattern)

**...customize the dashboard**
→ Edit: `streamlit-dashboard/pages/*.py`

**...check API endpoints**
→ Read: `docs/api_reference.md`

**...see all workflows explained**
→ Read: `docs/workflow_guide.md`

**...understand test coverage**
→ Read: `docs/testing_summary.md`

---

## 🌐 Service URLs (After `docker-compose up -d`)

| Service | URL | Purpose |
|---------|-----|---------|
| **Streamlit Dashboard** | http://localhost:8501 | Content review & campaign management |
| **n8n Workflows** | http://localhost:5678 | Workflow orchestration & monitoring |
| **Matomo Analytics** | http://localhost:9000 | Web analytics dashboard |
| **SearXNG Search** | http://localhost:8080 | Self-hosted search engine |
| **PostgreSQL** | localhost:5432 | Database (use DBeaver/pgAdmin) |
| **LangChain API** | http://localhost:8001 | AI agents API |
| **Ollama** | http://localhost:11434 | LLM inference |
| **Chroma** | http://localhost:8000 | Vector database |

---

## 🧪 Testing Commands

```bash
# Health check (all services)
python tests/run_tests.py --services

# Quick tests (< 1 min)
python tests/run_tests.py --quick

# Full test suite (~5 min)
python tests/run_tests.py --e2e

# With coverage report
python tests/run_tests.py --coverage

# Load testing (interactive)
python tests/run_tests.py --load
```

---

## 🔑 Required API Keys (Optional Features)

Set these in `.env` file:

### For Media Generation
- `OPENAI_API_KEY` - DALL-E 3 image generation
- `MIDJOURNEY_API_KEY` - Midjourney image generation (alternative)
- `RUNWAY_API_KEY` - Runway ML video generation
- `PIKA_API_KEY` - Pika video generation (alternative)

### For Publishing
- `LINKEDIN_ACCESS_TOKEN` - LinkedIn posting
- `WORDPRESS_URL`, `WORDPRESS_USERNAME`, `WORDPRESS_PASSWORD` - Blog publishing
- `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD` - Email newsletters

**Note**: System works without these (text-only mode). Add them when ready.

---

## 🎯 Core Workflows (What They Do)

| Workflow | Trigger | What It Does |
|----------|---------|--------------|
| **user_onboarding** | Manual | Conversational signup wizard |
| **research_pipeline** | Scheduled/Manual | Market research & competitor analysis |
| **content_generation** | Webhook | AI creates text content drafts |
| **image_generation** | Webhook | AI creates images (DALL-E/Midjourney) |
| **video_generation** | Webhook | AI creates videos (Runway/Pika) |
| **content_review_loop** | Webhook | Human review & revision cycle |
| **media_post_processing** | Webhook | Image/video optimization |
| **publishing_pipeline** | Webhook | Multi-channel publishing |
| **engagement_tracking** | Scheduled | Real-time analytics collection |
| **trend_monitoring** | Scheduled | Daily trend detection |

**Activate workflows**: n8n UI → each workflow → toggle to "Active"

---

## 🤖 AI Agents (What They Do)

| Agent | Purpose | Used By |
|-------|---------|---------|
| **Supervisor** | Routes tasks to specialist agents | All workflows |
| **Research Agent** | Market research, web scraping | research_pipeline |
| **Competitor Agent** | Competitor content analysis | research_pipeline |
| **Market Agent** | Audience segmentation | user_onboarding |
| **Content Agent** | Text content generation | content_generation |
| **Image Agent** | Image generation (DALL-E/Midjourney) | image_generation |
| **Video Agent** | Video generation (Runway/Pika) | video_generation |
| **Review Coordinator** | Human-in-the-loop management | content_review_loop |
| **Trend Agent** | Trend detection & analysis | trend_monitoring |

**Direct access**: `POST http://localhost:8001/agents/{agent_name}`

---

## 💾 Database Tables (What They Store)

| Table | Contents |
|-------|----------|
| `users` | User accounts and profiles |
| `campaigns` | Marketing campaigns |
| `content_drafts` | AI-generated content |
| `content_versions` | Revision history |
| `review_feedback` | Human review comments |
| `media_assets` | Images and videos |
| `media_edits` | Media editing history |
| `published_content` | Published content tracking |
| `engagement_metrics` | Analytics data |
| `competitors` | Competitor profiles |
| `market_insights` | Research findings |
| `trends` | Trending topics |

**Access**: `docker exec -it postgres psql -U marketing_user -d marketing_db`

---

## 🛠️ Common Troubleshooting

### "Docker won't start"
```bash
# Check Docker Desktop is running
# Then restart services
docker-compose down
docker-compose up -d
```

### "Database connection failed"
```bash
# Verify PostgreSQL is running
docker ps | grep postgres

# Check credentials in .env file
cat .env | grep POSTGRES
```

### "LLM is too slow"
```bash
# Use smaller model (faster on CPU)
docker exec -it ollama ollama pull mistral

# Update .env:
OLLAMA_MODEL=mistral
```

### "Tests are failing"
```bash
# Check all services healthy
python tests/run_tests.py --services

# Fix any ✗ (red X) services first
```

### "Can't access Streamlit dashboard"
```bash
# Check container logs
docker-compose logs streamlit-dashboard

# Restart service
docker-compose restart streamlit-dashboard
```

---

## 📊 Performance Benchmarks (Expected)

| Operation | Target | System |
|-----------|--------|--------|
| Content generation | < 5s | p95 latency |
| Image generation | < 30s | p95 latency |
| Video generation | < 60s | p95 latency |
| Review submission | < 1s | p95 latency |
| Publishing | < 10s | p95 latency |

**Test performance**: `python tests/run_tests.py --load`

---

## 🔄 Daily Workflow

### For Content Creators
1. Open dashboard: http://localhost:8501
2. Check "Content Review" for drafts
3. Review, edit, approve/reject content
4. Monitor "Analytics" for performance

### For Marketers
1. Create new campaign in "Campaigns" page
2. Trigger content generation (automatic or manual)
3. Review generated assets in "Media Review"
4. Publish approved content (automatic)
5. Track engagement in "Analytics"

### For Developers
1. Monitor n8n workflows: http://localhost:5678
2. Check execution logs for errors
3. Review system health: `python tests/run_tests.py --services`
4. Update agent prompts in `langchain-service/agents/`

---

## 📚 Documentation Hierarchy

```
Quick Start
└── README.md (5 min overview)
    └── SETUP_GUIDE.md (30 min installation)
        └── TESTING_CHECKLIST.md (2 hour validation)
            └── docs/
                ├── setup_guide.md (comprehensive)
                ├── api_reference.md (API docs)
                ├── architecture.md (deep dive)
                ├── workflow_guide.md (workflows explained)
                └── testing_summary.md (test results)
```

**Start at the top, drill down as needed.**

---

## 🎓 Learning Path

### Day 1: Setup & Basics
1. Read: README.md
2. Follow: SETUP_GUIDE.md
3. Run: `docker-compose up -d`
4. Test: `python tests/run_tests.py --services`
5. Explore: Streamlit dashboard (http://localhost:8501)

### Day 2: Understanding Architecture
1. Read: docs/architecture.md
2. Read: PROJECT_STRUCTURE.md
3. Explore: n8n workflows (http://localhost:5678)
4. Review: langchain-service/agents/

### Day 3: Creating Content
1. Create first campaign in dashboard
2. Trigger content generation
3. Review and approve content
4. Monitor analytics

### Day 4: Customization
1. Read: docs/api_reference.md
2. Modify agent prompts in `langchain-service/agents/`
3. Create custom workflow in n8n
4. Test changes with `pytest`

### Week 2: Production Deployment
1. Complete: TESTING_CHECKLIST.md
2. Configure: Publishing channels (.env)
3. Set up: Media generation APIs
4. Monitor: Performance and logs

---

## 🆘 Getting Help

### Check These First:
1. **Error in logs**: `docker-compose logs [service_name]`
2. **Service status**: `python tests/run_tests.py --services`
3. **Troubleshooting**: See TESTING_CHECKLIST.md → Troubleshooting section
4. **Architecture questions**: docs/architecture.md
5. **API questions**: docs/api_reference.md

### Common Error Solutions:
- **Port conflict**: Change port in `docker-compose.yml`
- **Out of memory**: Increase Docker Desktop memory limit
- **Database errors**: Check credentials in `.env`
- **LLM errors**: Verify Ollama model pulled: `docker exec -it ollama ollama list`

---

## 📝 Cheat Sheet

### Essential Commands
```bash
# Start system
docker-compose up -d

# Stop system
docker-compose down

# View logs
docker-compose logs -f [service]

# Restart service
docker-compose restart [service]

# Access database
docker exec -it postgres psql -U marketing_user -d marketing_db

# Pull new LLM model
docker exec -it ollama ollama pull [model_name]

# Run tests
python tests/run_tests.py --e2e

# Check services
python tests/run_tests.py --services
```

### Essential URLs
- Dashboard: http://localhost:8501
- n8n: http://localhost:5678
- Analytics: http://localhost:9000

### Essential Files
- Configuration: `.env`
- Database schema: `init-scripts/init.sql`
- Main workflows: `n8n-workflows/*.json`
- AI agents: `langchain-service/agents/*.py`

---

## ✅ Production Readiness Checklist

**Before going live**:
- [ ] All tests passing (`python tests/run_tests.py --e2e`)
- [ ] `.env` configured with production credentials
- [ ] API keys set for publishing channels
- [ ] Database backup strategy in place
- [ ] Monitoring and alerting configured
- [ ] Documentation reviewed and updated
- [ ] Team trained on dashboard usage
- [ ] Performance tested under load

**See full checklist**: `TESTING_CHECKLIST.md`

---

## 🎯 Next Steps

**Just finished setup?**
→ Run: `python tests/run_tests.py --services`
→ Then: Create first campaign in dashboard

**System is running?**
→ Follow: TESTING_CHECKLIST.md
→ Then: Configure publishing channels

**Tests are passing?**
→ Read: docs/workflow_guide.md
→ Then: Customize agent prompts

**Ready for production?**
→ Complete: TESTING_CHECKLIST.md (all phases)
→ Then: Deploy and monitor

---

**Last Updated:** January 14, 2026
**Version:** 1.0
**Purpose:** Fast answers to common questions
**For Details:** See referenced documents above
