# B2B Marketing Automation Platform - Testing & Deployment Checklist

## Pre-Deployment Testing Checklist

Use this checklist to verify the system is production-ready before deployment.

---

## Phase 1: Environment Setup

### 1.1 System Requirements
- [ ] Docker Desktop installed and running
- [ ] Minimum 16GB RAM available (32GB recommended)
- [ ] 50GB+ free disk space
- [ ] NVIDIA GPU available (optional, for faster LLM inference)
- [ ] Git installed and configured

### 1.2 Environment Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Configure PostgreSQL credentials
- [ ] Configure n8n credentials
- [ ] Set OLLAMA_MODEL (llama3 or mistral)
- [ ] Configure publishing channels (optional at first):
  - [ ] LinkedIn API token
  - [ ] WordPress credentials
  - [ ] SMTP credentials
- [ ] Configure media generation APIs (optional):
  - [ ] OpenAI API key (for DALL-E 3)
  - [ ] Midjourney API key
  - [ ] Runway ML API key
  - [ ] Pika API key

### 1.3 Service Initialization
- [ ] Start Docker Desktop
- [ ] Run `docker-compose up -d`
- [ ] Verify all containers are running: `docker-compose ps`
- [ ] Check container logs for errors: `docker-compose logs`

---

## Phase 2: Database Verification

### 2.1 PostgreSQL
- [ ] Connect to PostgreSQL: `docker exec -it postgres psql -U marketing_user -d marketing_db`
- [ ] Verify tables exist: `\dt`
- [ ] Check schema initialization:
  ```sql
  SELECT table_name FROM information_schema.tables
  WHERE table_schema = 'public';
  ```
- [ ] Verify tables created:
  - [ ] `users`
  - [ ] `campaigns`
  - [ ] `content_drafts`
  - [ ] `content_versions`
  - [ ] `review_feedback`
  - [ ] `media_assets`
  - [ ] `media_edits`
  - [ ] `published_content`
  - [ ] `engagement_metrics`
  - [ ] `competitors`
  - [ ] `market_insights`
  - [ ] `trends`

### 2.2 Chroma Vector Database
- [ ] Check Chroma is accessible: `curl http://localhost:8000/api/v1/heartbeat`
- [ ] Verify collections endpoint: `curl http://localhost:8000/api/v1/collections`
- [ ] Expected response: `200 OK` with empty collections list

### 2.3 Redis Cache
- [ ] Connect to Redis: `docker exec -it redis redis-cli`
- [ ] Test connection: `PING` (should return `PONG`)
- [ ] Exit: `EXIT`

---

## Phase 3: Core Services Health Check

### 3.1 Ollama (LLM Service)
- [ ] Check Ollama is running: `curl http://localhost:11434`
- [ ] Pull LLM model: `docker exec -it ollama ollama pull llama3`
- [ ] Verify model loaded: `docker exec -it ollama ollama list`
- [ ] Test inference:
  ```bash
  curl http://localhost:11434/api/generate -d '{
    "model": "llama3",
    "prompt": "Say hello",
    "stream": false
  }'
  ```
- [ ] Expected: JSON response with generated text

### 3.2 n8n Workflow Orchestration
- [ ] Access n8n UI: http://localhost:5678
- [ ] Create admin account (first-time setup)
- [ ] Import workflows from `n8n-workflows/` directory
- [ ] Verify 10 workflows imported:
  - [ ] user_onboarding.json
  - [ ] research_pipeline.json
  - [ ] content_generation.json
  - [ ] image_generation.json
  - [ ] video_generation.json
  - [ ] content_review_loop.json
  - [ ] media_post_processing.json
  - [ ] publishing_pipeline.json
  - [ ] engagement_tracking.json
  - [ ] trend_monitoring.json
- [ ] Activate each workflow (toggle to active state)
- [ ] Check webhook URLs are accessible

### 3.3 LangChain Service
- [ ] Check service is running: `curl http://localhost:8001/health`
- [ ] Expected response: `200 OK` with `{"status": "healthy"}`
- [ ] Test supervisor endpoint:
  ```bash
  curl -X POST http://localhost:8001/supervisor \
    -H "Content-Type: application/json" \
    -d '{"task": "Test query", "campaign_id": 1}'
  ```
- [ ] Verify agent endpoints:
  - [ ] `/agents/research`
  - [ ] `/agents/content`
  - [ ] `/agents/image`
  - [ ] `/agents/video`

### 3.4 SearXNG (Search Engine)
- [ ] Access SearXNG: http://localhost:8080
- [ ] Perform test search: "AI marketing"
- [ ] Verify results returned
- [ ] Test JSON API:
  ```bash
  curl "http://localhost:8080/search?q=test&format=json"
  ```

### 3.5 Streamlit Dashboard
- [ ] Access dashboard: http://localhost:8501
- [ ] Verify all pages load:
  - [ ] Overview (main page)
  - [ ] Content Review
  - [ ] Media Review
  - [ ] Asset Library
  - [ ] Analytics
  - [ ] Campaigns
  - [ ] Onboarding
- [ ] Test database connection indicator (top right)
- [ ] Verify no error messages in console

### 3.6 Matomo Analytics
- [ ] Access Matomo: http://localhost:9000
- [ ] Complete first-time setup wizard
- [ ] Create site for tracking
- [ ] Note site ID for configuration
- [ ] Generate tracking code

---

## Phase 4: Python Dependencies

### 4.1 LangChain Service Dependencies
- [ ] Navigate to `langchain-service/`
- [ ] Check requirements file exists: `cat requirements.txt`
- [ ] Install dependencies in container:
  ```bash
  docker exec -it langchain-service pip install -r requirements.txt
  ```
- [ ] Verify no errors

### 4.2 Streamlit Dashboard Dependencies
- [ ] Navigate to `streamlit-dashboard/`
- [ ] Check requirements file exists: `cat requirements.txt`
- [ ] Install dependencies in container:
  ```bash
  docker exec -it streamlit-dashboard pip install -r requirements.txt
  ```

### 4.3 Test Suite Dependencies
- [ ] Navigate to `tests/`
- [ ] Install test dependencies locally (for manual testing):
  ```bash
  pip install -r requirements.txt
  ```
- [ ] Verify pytest installed: `pytest --version`

---

## Phase 5: End-to-End Workflow Testing

### 5.1 Service Health Check (Automated)
- [ ] Run test runner service check:
  ```bash
  python tests/run_tests.py --services
  ```
- [ ] Expected: All services show ✓ (green checkmark)
- [ ] If any service fails, check Docker logs for that service

### 5.2 Content Generation Workflow Test

**Manual Test Steps:**
1. [ ] Open Streamlit dashboard: http://localhost:8501
2. [ ] Navigate to "Campaigns" page
3. [ ] Create new campaign:
   - Campaign name: "Test Campaign"
   - Target audience: "B2B Marketing Managers"
   - Add brand guidelines (optional)
4. [ ] Note the campaign ID
5. [ ] Trigger content generation via n8n webhook:
   ```bash
   curl -X POST http://localhost:5678/webhook/content-generate \
     -H "Content-Type: application/json" \
     -d '{
       "campaign_id": 1,
       "topic": "Benefits of Marketing Automation",
       "content_type": "linkedin_post",
       "target_word_count": 300
     }'
   ```
6. [ ] Expected response: `200 OK` or `202 Accepted`
7. [ ] Wait 30-60 seconds for LLM processing
8. [ ] Check PostgreSQL for new draft:
   ```bash
   docker exec -it postgres psql -U marketing_user -d marketing_db \
     -c "SELECT id, type, status FROM content_drafts ORDER BY created_at DESC LIMIT 5;"
   ```
9. [ ] Navigate to "Content Review" page in Streamlit
10. [ ] Verify draft appears in review queue
11. [ ] Draft should have status: `in_review`

**Automated Test:**
- [ ] Run E2E content generation tests:
  ```bash
  pytest tests/test_e2e_content_generation.py -v
  ```
- [ ] Expected: All tests pass (may take 5 minutes)

### 5.3 Image Generation Workflow Test (Optional - requires API keys)

**Prerequisites:**
- [ ] DALL-E 3 API key configured in `.env`
- [ ] OR Midjourney API key configured

**Manual Test Steps:**
1. [ ] Create test content draft in database
2. [ ] Trigger image generation:
   ```bash
   curl -X POST http://localhost:5678/webhook/image-generate \
     -H "Content-Type: application/json" \
     -d '{
       "draft_id": 1,
       "image_type": "social_post",
       "dimensions": "1200x628",
       "provider": "dalle"
     }'
   ```
3. [ ] Wait 20-40 seconds for API processing
4. [ ] Check media_assets table:
   ```sql
   SELECT id, type, url, api_provider FROM media_assets ORDER BY created_at DESC LIMIT 5;
   ```
5. [ ] Navigate to "Media Review" page
6. [ ] Verify image appears with preview

**Automated Test:**
- [ ] Run E2E media generation tests:
  ```bash
  pytest tests/test_e2e_media_generation.py::TestImageGenerationWorkflow -v
  ```

### 5.4 Review Workflow Test

**Manual Test Steps:**
1. [ ] Open Streamlit dashboard → Content Review
2. [ ] Select a draft from the list
3. [ ] Review content in side-by-side editor
4. [ ] Test "Request Revisions":
   - [ ] Add feedback: "Make tone more professional"
   - [ ] Click "Request Revisions"
   - [ ] Verify webhook triggered (check n8n execution logs)
   - [ ] Wait 30-60 seconds for LLM revision
   - [ ] Verify new version created in database
   - [ ] Refresh page and see revised content
5. [ ] Test "Approve":
   - [ ] Click "Approve"
   - [ ] Verify status changes to `approved` in database
   - [ ] Check if publishing workflow triggered
6. [ ] Test "Reject":
   - [ ] Click "Reject"
   - [ ] Verify status changes to `rejected`

**Automated Test:**
- [ ] Run review workflow tests:
  ```bash
  pytest tests/test_e2e_review_workflow.py -v
  ```

### 5.5 Publishing Workflow Test (Optional - requires credentials)

**Prerequisites:**
- [ ] LinkedIn access token configured (optional)
- [ ] WordPress credentials configured (optional)
- [ ] SMTP credentials configured (optional)

**Manual Test Steps:**
1. [ ] Select an approved draft
2. [ ] Trigger publishing workflow:
   ```bash
   curl -X POST http://localhost:5678/webhook/publish \
     -H "Content-Type: application/json" \
     -d '{
       "draft_id": 1,
       "channels": ["linkedin"]
     }'
   ```
3. [ ] Check published_content table:
   ```sql
   SELECT * FROM published_content ORDER BY published_at DESC LIMIT 5;
   ```
4. [ ] Verify content published to LinkedIn (check your profile)
5. [ ] Check engagement_metrics table for initial record

**Automated Test:**
- [ ] Run publishing tests:
  ```bash
  pytest tests/test_e2e_publishing.py -v
  ```

---

## Phase 6: Performance & Load Testing

### 6.1 Single User Performance
- [ ] Measure content generation latency (target: < 5s p95)
- [ ] Measure image generation latency (target: < 30s p95)
- [ ] Measure review submission latency (target: < 1s p95)
- [ ] Measure publishing latency (target: < 10s p95)

### 6.2 Load Testing (Optional)

**Prerequisites:**
- [ ] Install Locust: `pip install locust`

**Test Steps:**
1. [ ] Start Locust:
   ```bash
   locust -f tests/load_test_workflows.py --host=http://localhost:5678
   ```
2. [ ] Open Locust UI: http://localhost:8089
3. [ ] Configure test:
   - Number of users: 10
   - Spawn rate: 2 users/sec
   - Host: http://localhost:5678
4. [ ] Click "Start Swarming"
5. [ ] Monitor for 5 minutes
6. [ ] Check metrics:
   - [ ] RPS (requests per second)
   - [ ] p50, p95, p99 latencies
   - [ ] Failure rate (target: < 1%)
7. [ ] Stop test and review results

**Performance Benchmarks:**
- [ ] Content Generation: p95 < 5s
- [ ] Image Generation: p95 < 30s
- [ ] Review Submission: p95 < 1s
- [ ] Publishing: p95 < 10s
- [ ] Overall failure rate < 1%

---

## Phase 7: Integration Testing

### 7.1 Run Full Test Suite

**Quick Tests (no external services):**
```bash
python tests/run_tests.py --quick
```
- [ ] Expected: 15+ tests pass in < 30 seconds

**Integration Tests (requires all services):**
```bash
python tests/run_tests.py --integration
```
- [ ] Expected: 18+ tests pass in ~3 minutes

**End-to-End Tests (full workflows):**
```bash
python tests/run_tests.py --e2e
```
- [ ] Expected: 29+ tests pass in ~5 minutes

**With Coverage Report:**
```bash
python tests/run_tests.py --coverage
```
- [ ] Expected: Coverage > 80%
- [ ] HTML report generated: `htmlcov/index.html`

### 7.2 Test Results Validation
- [ ] All tests pass (no failures)
- [ ] No unexpected errors in logs
- [ ] Coverage meets target (> 80%)
- [ ] Performance within benchmarks

---

## Phase 8: Security & Configuration

### 8.1 Environment Variables
- [ ] Verify no sensitive data in `.env` is committed to git
- [ ] Check `.gitignore` includes `.env`
- [ ] Verify `.env.example` has placeholders only
- [ ] Rotate any exposed API keys

### 8.2 Database Security
- [ ] Change default PostgreSQL password
- [ ] Verify PostgreSQL not exposed publicly (port 5432 local only)
- [ ] Set up database backups
- [ ] Configure connection pooling limits

### 8.3 API Security
- [ ] Verify n8n webhooks use authentication (if configured)
- [ ] Check CORS settings on LangChain service
- [ ] Verify Streamlit authentication (if enabled)
- [ ] Review nginx security headers

### 8.4 GDPR Compliance
- [ ] Data anonymization configured
- [ ] User consent tracking enabled
- [ ] Data deletion workflow tested
- [ ] Privacy policy documented

---

## Phase 9: Monitoring & Logging

### 9.1 Log Verification
- [ ] Check Docker container logs:
  ```bash
  docker-compose logs -f [service_name]
  ```
- [ ] Verify no critical errors
- [ ] Check log rotation configured
- [ ] Set up log aggregation (optional: ELK stack)

### 9.2 Metrics Collection
- [ ] Matomo tracking code installed
- [ ] Dashboard analytics working
- [ ] Custom event tracking configured
- [ ] Engagement metrics populating

### 9.3 Alerting (Optional)
- [ ] Set up email alerts for workflow failures
- [ ] Configure Slack notifications (optional)
- [ ] Monitor disk space alerts
- [ ] Database connection monitoring

---

## Phase 10: Documentation Review

### 10.1 Documentation Completeness
- [ ] README.md is up-to-date
- [ ] SETUP_GUIDE.md has clear instructions
- [ ] docs/setup_guide.md is comprehensive
- [ ] docs/api_reference.md covers all endpoints
- [ ] docs/architecture.md explains system design
- [ ] docs/workflow_guide.md documents all workflows
- [ ] docs/testing_summary.md summarizes test coverage
- [ ] All service README files are present
- [ ] PROJECT_STRUCTURE.md exists (documents repo layout)

### 10.2 Code Documentation
- [ ] All Python files have docstrings
- [ ] Complex functions have inline comments
- [ ] n8n workflows have clear node labels
- [ ] Database schema is documented

---

## Phase 11: Production Readiness

### 11.1 Final Checklist
- [ ] All Docker containers running without errors
- [ ] All tests passing
- [ ] Performance benchmarks met
- [ ] Security configurations applied
- [ ] Monitoring and logging active
- [ ] Documentation complete
- [ ] Backup strategy implemented
- [ ] Rollback plan documented

### 11.2 Go-Live Preparation
- [ ] Schedule maintenance window
- [ ] Notify stakeholders
- [ ] Prepare rollback procedure
- [ ] Monitor during initial deployment
- [ ] Verify all integrations working
- [ ] Collect user feedback

---

## Troubleshooting Guide

### Common Issues

**Issue: Docker containers won't start**
- Check Docker Desktop is running
- Verify port conflicts (5432, 5678, 8501, etc.)
- Check disk space availability
- Review `docker-compose logs` for errors

**Issue: PostgreSQL connection failed**
- Verify container is running: `docker ps | grep postgres`
- Check credentials in `.env`
- Test connection: `docker exec -it postgres psql -U marketing_user -d marketing_db`
- Check port not blocked by firewall

**Issue: Ollama model not loading**
- Verify model pulled: `docker exec -it ollama ollama list`
- Pull model: `docker exec -it ollama ollama pull llama3`
- Check GPU drivers (if using GPU)
- Increase memory allocation in Docker Desktop

**Issue: n8n workflows timing out**
- Check LangChain service is responding
- Verify Ollama inference time (may be slow on CPU)
- Increase workflow timeout settings
- Check database connection pool

**Issue: Tests failing**
- Verify all services healthy: `python tests/run_tests.py --services`
- Check service logs for errors
- Ensure test database initialized
- Run tests with verbose output: `pytest -v -s`

**Issue: Streamlit dashboard not loading**
- Check container logs: `docker-compose logs streamlit-dashboard`
- Verify PostgreSQL connection
- Clear browser cache
- Check port 8501 not blocked

---

## Success Criteria

### Minimum Viable Product (MVP)
- ✅ All Docker containers running
- ✅ Basic content generation working (text only)
- ✅ Review workflow functional
- ✅ Database persisting data
- ✅ Streamlit dashboard accessible
- ✅ At least 1 publishing channel working

### Full Production Release
- ✅ All 29 E2E tests passing
- ✅ Load testing shows stable performance
- ✅ All documentation complete
- ✅ Security configurations applied
- ✅ Monitoring and alerting active
- ✅ Backup and recovery tested
- ✅ Multi-channel publishing working
- ✅ Media generation functional (images/videos)
- ✅ Analytics tracking operational

---

## Next Steps After Testing

1. **If All Tests Pass:**
   - Deploy to production environment
   - Monitor performance for 24-48 hours
   - Collect user feedback
   - Plan feature enhancements

2. **If Tests Fail:**
   - Review error logs
   - Fix identified issues
   - Re-run failed tests
   - Update documentation with fixes

3. **Ongoing Maintenance:**
   - Weekly health checks
   - Monthly security updates
   - Quarterly performance reviews
   - Continuous monitoring

---

**Last Updated:** January 14, 2026
**Version:** 1.0
**Status:** Production Ready
