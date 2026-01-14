# Test Suite Documentation

Comprehensive testing suite for the B2B Marketing Automation Platform.

## Overview

This test suite includes:
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows
- **Load Tests**: Performance and scalability testing

## Prerequisites

### Required Services

All services must be running for full test coverage:

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

Required services:
- PostgreSQL (port 5432)
- n8n (port 5678)
- LangChain Service (port 8001)
- Chroma (port 8000)
- Ollama (port 11434)

### Database Setup

Initialize the test database with schema:

```bash
# Run database initialization
docker exec -it postgres psql -U marketing_user -d marketing_db -f /docker-entrypoint-initdb.d/init.sql
```

### Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install test dependencies
pip install -r tests/requirements.txt
```

## Test Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=marketing_db
POSTGRES_USER=marketing_user
POSTGRES_PASSWORD=marketing_pass

# n8n
N8N_BASE_URL=http://localhost:5678
N8N_WEBHOOK_URL=http://localhost:5678/webhook

# LangChain Service
LANGCHAIN_SERVICE_URL=http://localhost:8001

# Streamlit
STREAMLIT_URL=http://localhost:8501
```

## Running Tests

### Quick Start

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html
```

### Running Specific Test Categories

```bash
# Run only integration tests (requires services)
pytest tests/ -m integration

# Run only e2e tests
pytest tests/ -m e2e

# Run only fast tests (exclude slow tests)
pytest tests/ -m "not slow"

# Run specific test file
pytest tests/test_e2e_content_generation.py

# Run specific test class
pytest tests/test_e2e_content_generation.py::TestContentGenerationWorkflow

# Run specific test method
pytest tests/test_e2e_content_generation.py::TestContentGenerationWorkflow::test_content_generation_flow
```

### Parallel Test Execution

```bash
# Run tests in parallel (faster)
pytest tests/ -n 4  # 4 parallel workers

# Auto-detect CPU count
pytest tests/ -n auto
```

### Test Output Options

```bash
# Show print statements
pytest tests/ -s

# Show test durations
pytest tests/ --durations=10

# Stop on first failure
pytest tests/ -x

# Run last failed tests only
pytest tests/ --lf

# Run failed tests first, then others
pytest tests/ --ff
```

## Test Structure

### File Organization

```
tests/
├── __init__.py                          # Test package
├── conftest.py                          # Pytest fixtures and configuration
├── requirements.txt                     # Test dependencies
├── README.md                            # This file
│
├── test_e2e_content_generation.py      # Content generation workflow tests
├── test_e2e_media_generation.py        # Image/video generation tests
├── test_e2e_review_workflow.py         # Review loop tests
├── test_e2e_publishing.py              # Publishing pipeline tests
│
├── load_test_workflows.py              # Load testing with Locust
│
└── test_report.html                     # Generated coverage report
```

### Test Fixtures

Common fixtures available in all tests (defined in `conftest.py`):

- `db_connection`: Database connection (session scope)
- `db_cursor`: Database cursor with auto-rollback (function scope)
- `test_user`: Test user account (session scope)
- `test_campaign`: Test campaign (session scope)
- `mock_content_draft`: Mock content draft (function scope, auto-cleanup)
- `n8n_client`: n8n webhook client
- `langchain_client`: LangChain service client
- `check_services`: Ensures all services are running

## End-to-End Test Scenarios

### 1. Content Generation Flow

Tests the complete workflow from trigger to draft creation:

```bash
pytest tests/test_e2e_content_generation.py::TestContentGenerationWorkflow::test_content_generation_flow -v
```

**What it tests**:
1. Webhook triggers content generation
2. Campaign details retrieved from database
3. Research context retrieved
4. Similar content found via RAG (Chroma)
5. LLM generates content
6. SEO optimization applied
7. Grammar check applied
8. Draft saved to database
9. Embeddings stored in Chroma
10. Review notification sent

### 2. Image Generation Flow

Tests image creation with DALL-E 3 or Midjourney:

```bash
pytest tests/test_e2e_media_generation.py::TestImageGenerationWorkflow::test_image_generation_dalle -v
```

**What it tests**:
1. Image prompt built from content + branding
2. DALL-E 3 API called
3. Image downloaded
4. Watermark added
5. Image resized for platform
6. File optimized
7. Media asset record created
8. Review notification sent

### 3. Review Loop Flow

Tests human-in-the-loop review workflow:

```bash
pytest tests/test_e2e_review_workflow.py::TestContentReviewWorkflow::test_review_approve_flow -v
```

**What it tests**:
1. Reviewer approves content
2. Feedback saved to database
3. Draft status updated to "approved"
4. Publishing workflow triggered

### 4. Publishing Flow

Tests multi-channel publishing:

```bash
pytest tests/test_e2e_publishing.py::TestPublishingWorkflow::test_publish_multi_channel -v
```

**What it tests**:
1. Content formatted for each channel
2. LinkedIn API publishes post
3. WordPress XML-RPC creates blog post
4. SMTP sends email newsletter
5. Published records created
6. Engagement tracking initialized

## Load Testing

### Using Locust

Load testing simulates realistic user traffic to identify performance bottlenecks.

#### Start Locust Web UI

```bash
# Start Locust with web interface
locust -f tests/load_test_workflows.py --host=http://localhost:5678

# Open browser to http://localhost:8089
# Enter number of users and spawn rate
# Click "Start Swarming"
```

#### Headless Load Testing

```bash
# Run load test without web UI
locust -f tests/load_test_workflows.py \
    --host=http://localhost:5678 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --headless

# Export results to CSV
locust -f tests/load_test_workflows.py \
    --host=http://localhost:5678 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --headless \
    --csv=load_test_results
```

#### Load Test Scenarios

**Scenario 1: Content Generation Burst**
- Simulates 50 users generating content simultaneously
- Tests Ollama LLM throughput
- Identifies PostgreSQL connection pool limits

```bash
locust -f tests/load_test_workflows.py \
    --host=http://localhost:5678 \
    --users 50 \
    --spawn-rate 10 \
    --run-time 3m \
    --headless \
    ContentGenerationUser
```

**Scenario 2: Mixed Workload**
- Simulates realistic user distribution
- 50% content generation, 20% research, 30% analytics

```bash
locust -f tests/load_test_workflows.py \
    --host=http://localhost:5678 \
    --users 100 \
    --spawn-rate 5 \
    --run-time 10m \
    --headless \
    MixedWorkloadUser
```

**Scenario 3: Ramp-Up Test**
- Gradual increase from 10 to 100 users
- Identifies performance degradation points

```bash
locust -f tests/load_test_workflows.py \
    --host=http://localhost:5678 \
    StepLoadShape
```

### Interpreting Load Test Results

**Key Metrics**:
- **RPS (Requests Per Second)**: Throughput
- **Response Time (ms)**: Latency
  - p50: Median response time
  - p95: 95th percentile (slow requests)
  - p99: 99th percentile (slowest requests)
- **Failure Rate (%)**: Error percentage

**Healthy Benchmarks**:
- Content generation: < 5s p95
- Image generation: < 30s p95
- Review submission: < 1s p95
- Publishing: < 10s p95
- Failure rate: < 1%

**Warning Signs**:
- p95 > 10s for content generation
- Failure rate > 5%
- RPS decreases as users increase
- Memory/CPU usage > 80%

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/tests.yml`:

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: marketing_db
          POSTGRES_USER: marketing_user
          POSTGRES_PASSWORD: marketing_pass
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r tests/requirements.txt

      - name: Run tests
        run: |
          pytest tests/ -v --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

**Issue**: `pytest: command not found`
- **Solution**: Ensure virtual environment is activated and pytest is installed

**Issue**: `psycopg2.OperationalError: could not connect to server`
- **Solution**: Verify PostgreSQL is running: `docker ps | grep postgres`

**Issue**: `requests.exceptions.ConnectionError` for n8n webhooks
- **Solution**: Verify n8n is accessible: `curl http://localhost:5678`

**Issue**: Tests hang indefinitely
- **Solution**: Use `--timeout=30` flag: `pytest tests/ --timeout=30`

**Issue**: `FAILED tests/conftest.py::check_services`
- **Solution**: Not all services are running. Check `docker-compose ps`

**Issue**: Load test shows high failure rate
- **Solution**: Reduce user count or spawn rate. System may be overloaded.

### Debug Mode

```bash
# Run with debug output
pytest tests/ -v -s --log-cli-level=DEBUG

# Drop into debugger on failure
pytest tests/ --pdb

# Drop into debugger on first failure
pytest tests/ -x --pdb
```

### Checking Service Health

```bash
# PostgreSQL
docker exec -it postgres psql -U marketing_user -d marketing_db -c "SELECT 1;"

# n8n
curl http://localhost:5678

# LangChain
curl http://localhost:8001/health

# Ollama
curl http://localhost:11434/api/generate -d '{"model":"llama3","prompt":"test"}'

# Chroma
curl http://localhost:8000/api/v1/heartbeat
```

## Test Coverage Goals

Target coverage metrics:
- **Overall**: > 80%
- **Critical paths** (content generation, publishing): > 95%
- **Error handling**: > 90%

Generate coverage report:

```bash
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html  # View detailed coverage report
```

## Writing New Tests

### Example Test Template

```python
import pytest

@pytest.mark.e2e
@pytest.mark.integration
class TestNewFeature:
    """Test new feature description"""

    def test_happy_path(
        self, check_services, n8n_client, test_campaign, db_cursor
    ):
        """Test successful execution"""

        # Arrange
        payload = {"campaign_id": test_campaign["id"], "param": "value"}

        # Act
        response = n8n_client.trigger_webhook("new-feature", payload)

        # Assert
        assert response.status_code in [200, 201, 202]

        # Verify database changes
        db_cursor.execute("SELECT * FROM new_table WHERE campaign_id = %s",
                         (test_campaign["id"],))
        result = db_cursor.fetchone()
        assert result is not None

        # Cleanup (if needed)
        db_cursor.execute("DELETE FROM new_table WHERE id = %s", (result[0],))

    def test_error_handling(self, n8n_client):
        """Test error scenarios"""

        # Invalid input
        payload = {"invalid": "data"}
        response = n8n_client.trigger_webhook("new-feature", payload)

        # Should return error or handle gracefully
        # Exact behavior depends on implementation
```

### Best Practices

1. **Use fixtures**: Leverage existing fixtures for common setup
2. **Cleanup**: Always cleanup test data in database
3. **Isolation**: Tests should not depend on other tests
4. **Realistic data**: Use Faker for generating realistic test data
5. **Error cases**: Test both success and failure scenarios
6. **Timeouts**: Set reasonable timeouts for async operations
7. **Markers**: Tag tests appropriately (e2e, integration, slow)

## Performance Benchmarks

Expected performance on recommended hardware (32GB RAM, 8 CPU cores):

| Workflow | p50 Latency | p95 Latency | Throughput |
|----------|------------|-------------|------------|
| Content Generation | 2s | 4s | 10 req/s |
| Image Generation | 15s | 25s | 2 req/s |
| Video Generation | 45s | 90s | 1 req/s |
| Review Submission | 0.5s | 1s | 50 req/s |
| Publishing | 3s | 8s | 5 req/s |

## Support

For issues with tests:
1. Check service logs: `docker-compose logs [service]`
2. Review test output with `-v` flag
3. Check GitHub Issues for known problems
4. Refer to main documentation: `docs/setup_guide.md`

## License

MIT License - See LICENSE file for details
