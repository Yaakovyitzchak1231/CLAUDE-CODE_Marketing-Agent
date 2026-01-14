# Setup Verification Checklist

Use this checklist to verify your B2B Marketing Automation Platform installation.

## Pre-Installation Checklist

- [ ] Docker Desktop installed (version 24.0+)
- [ ] Docker Compose V2 available
- [ ] At least 16GB RAM available
- [ ] At least 50GB free disk space
- [ ] Git installed
- [ ] `.env` file created from `.env.example`
- [ ] All required API keys obtained (OpenAI, Runway, etc.)

## Installation Verification

### 1. Docker Services Status

Run: `docker-compose ps`

Expected: All services should show status "Up" or "healthy"

- [ ] postgres (port 5432)
- [ ] redis (port 6379)
- [ ] ollama (port 11434)
- [ ] chroma (port 8000)
- [ ] langchain_service (port 8001)
- [ ] streamlit_dashboard (port 8501)
- [ ] searxng (port 8080)
- [ ] playwright_service (port 8002)
- [ ] scrapy_service (port 8003)
- [ ] matomo (port 8081)
- [ ] adminer (port 8082)
- [ ] nginx (ports 80, 443) - optional
- [ ] n8n (port 5678) - optional if using external n8n

### 2. Database Verification

**Check PostgreSQL is running:**
```bash
docker exec postgres pg_isready -U n8n
```
Expected: `postgres:5432 - accepting connections`

**Verify databases exist:**
```bash
docker exec postgres psql -U n8n -c "\l"
```
Expected: Should list three databases:
- [ ] `marketing`
- [ ] `n8n`
- [ ] `matomo`

**Check marketing database tables:**
```bash
docker exec postgres psql -U n8n -d marketing -c "\dt"
```
Expected: Should list tables including:
- [ ] users
- [ ] campaigns
- [ ] content_drafts
- [ ] media_assets
- [ ] competitors
- [ ] trends
- [ ] published_content
- [ ] engagement_metrics

### 3. Ollama Model Verification

**Check Ollama is running:**
```bash
curl http://localhost:11434/api/tags
```

**List installed models:**
```bash
docker exec ollama ollama list
```
Expected models:
- [ ] llama3:8b (or llama3:latest)
- [ ] mistral:7b (or mistral:latest)

**Test model inference:**
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3:8b",
  "prompt": "What is B2B marketing?",
  "stream": false
}'
```
Expected: Should return JSON with generated text response

### 4. Chroma Vector Database

**Check Chroma is running:**
```bash
curl http://localhost:8000/api/v1/heartbeat
```
Expected: Response with heartbeat timestamp

**Verify collections exist:**
```bash
docker exec langchain_service python -c "
import chromadb
client = chromadb.HttpClient(host='chroma', port=8000)
collections = [c.name for c in client.list_collections()]
print('Collections:', collections)
"
```
Expected collections:
- [ ] user_profiles
- [ ] content_library
- [ ] market_segments
- [ ] competitor_content

**If collections don't exist, initialize:**
```bash
docker exec langchain_service python /app/chroma-init/init_collections.py
```

### 5. Redis Cache

**Check Redis is running:**
```bash
docker exec redis redis-cli ping
```
Expected: `PONG`

### 6. LangChain Service

**Check service health:**
```bash
curl http://localhost:8001/health
```
Expected: `{"status": "healthy"}` or similar response

**Test research agent:**
```bash
curl -X POST http://localhost:8001/agents/research \
  -H "Content-Type: application/json" \
  -d '{"query": "B2B marketing trends"}'
```
Expected: JSON response with research data

### 7. n8n Configuration

**Option A: Local Docker n8n**

- [ ] Access http://localhost:5678
- [ ] Login with credentials from `.env`
- [ ] Can see n8n dashboard

**Option B: External n8n (Cloud Run, etc.)**

- [ ] `.env` has `N8N_EXTERNAL_URL` configured
- [ ] `.env` has `N8N_API_KEY` configured
- [ ] Can access external n8n URL
- [ ] Local n8n service commented out in docker-compose.yml

### 8. Streamlit Dashboard

- [ ] Access http://localhost:8501
- [ ] Dashboard loads without errors
- [ ] Can see main navigation menu
- [ ] Database connection successful (check bottom of page)

### 9. Matomo Analytics

- [ ] Access http://localhost:8081
- [ ] Matomo installation wizard appears OR existing installation loads
- [ ] Can login with configured credentials

### 10. SearXNG Search

- [ ] Access http://localhost:8080
- [ ] Search interface loads
- [ ] Can perform test search query

### 11. Service Integration Test

Run the automated test script:

**Linux/Mac:**
```bash
chmod +x test-services.sh
./test-services.sh
```

**Windows PowerShell:**
```powershell
.\test-services.ps1
```

Expected: All service checks pass

### 12. API Keys Validation

Verify in `.env` file:

**Required for Image Generation:**
- [ ] `OPENAI_API_KEY` is set (starts with `sk-`)

**Required for Video Generation:**
- [ ] `RUNWAY_API_KEY` is set

**Optional Publishing:**
- [ ] `LINKEDIN_ACCESS_TOKEN` is set (if using LinkedIn)
- [ ] `WORDPRESS_URL`, `WORDPRESS_USERNAME`, `WORDPRESS_PASSWORD` are set (if using WordPress)
- [ ] `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD` are set (if using email)

### 13. Network Connectivity

**Test internal service communication:**
```bash
# LangChain can reach Ollama
docker exec langchain_service curl -s http://ollama:11434/api/tags

# LangChain can reach Chroma
docker exec langchain_service curl -s http://chroma:8000/api/v1/heartbeat

# LangChain can reach PostgreSQL
docker exec langchain_service pg_isready -h postgres -U n8n
```

All commands should succeed without errors.

## Common Issues and Fixes

### Issue: Containers keep restarting
**Check logs:**
```bash
docker-compose logs [service-name]
```

**Common causes:**
- Port already in use: Check with `docker ps` or `netstat -an | grep [port]`
- Insufficient memory: Increase Docker memory limit
- Missing environment variables: Check `.env` file

### Issue: Ollama models not found
**Solution:**
```bash
docker exec ollama ollama pull llama3:8b
docker exec ollama ollama pull mistral:7b
```

### Issue: Database connection failed
**Solution:**
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Wait for it to be ready
docker exec postgres pg_isready -U n8n

# Restart dependent services
docker-compose restart langchain_service streamlit_dashboard
```

### Issue: Chroma collections missing
**Solution:**
```bash
docker exec langchain_service python /app/chroma-init/init_collections.py
```

### Issue: Out of memory
**Solution:**
1. Increase Docker Desktop memory limit (Settings → Resources → Memory)
2. Use smaller Ollama model: `ollama pull phi:2` (only 2.7GB)
3. Stop non-essential services temporarily:
   ```bash
   docker-compose stop matomo adminer
   ```

## Performance Verification

### Response Time Tests

**Ollama inference speed:**
```bash
time curl http://localhost:11434/api/generate -d '{
  "model": "llama3:8b",
  "prompt": "Hello",
  "stream": false
}'
```
Expected: < 30 seconds on CPU, < 5 seconds on GPU

**Database query performance:**
```bash
time docker exec postgres psql -U n8n -d marketing -c "SELECT COUNT(*) FROM users;"
```
Expected: < 1 second

## Security Checklist

- [ ] Changed all default passwords in `.env`
- [ ] `.env` file has secure permissions (not committed to git)
- [ ] PostgreSQL uses strong password
- [ ] Redis password configured (if enabled)
- [ ] n8n basic auth enabled with strong password
- [ ] API keys stored securely in `.env` only

## Production Readiness

For production deployment, additionally verify:

- [ ] SSL certificates configured in nginx
- [ ] Firewall rules configured
- [ ] Backup strategy implemented
- [ ] Monitoring alerts configured
- [ ] Log rotation configured
- [ ] Resource limits set in docker-compose.yml
- [ ] External n8n properly secured with authentication

## Final Check

Run a complete end-to-end test:

1. Create a test campaign in Streamlit dashboard
2. Trigger content generation workflow in n8n
3. Verify content appears in dashboard
4. Check database for new records
5. Verify Ollama was used for generation (check logs)
6. Check Chroma for new embeddings

If all steps succeed, your installation is complete and verified! 🎉

## Next Steps

- [ ] Import n8n workflows from `/n8n-workflows`
- [ ] Configure publishing channels (LinkedIn, WordPress)
- [ ] Set up campaign templates
- [ ] Create first marketing campaign
- [ ] Review documentation in `/docs`

## Support

If you encounter issues not covered here:

1. Check logs: `docker-compose logs -f [service-name]`
2. Review documentation in `/docs`
3. Check GitHub Issues: https://github.com/Yaakovyitzchak1231/marketing-agent/issues
4. Verify your setup matches the requirements

---

**Last Updated:** 2026-01-14
**Version:** 1.0
