"""
Pytest configuration and fixtures for test suite
"""
import pytest
import psycopg2
import requests
from typing import Dict, Generator
import os
from dotenv import load_dotenv

load_dotenv()

# Test configuration
TEST_CONFIG = {
    "postgres": {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", 5432)),
        "database": os.getenv("POSTGRES_DB", "marketing_db"),
        "user": os.getenv("POSTGRES_USER", "marketing_user"),
        "password": os.getenv("POSTGRES_PASSWORD", "marketing_pass")
    },
    "n8n": {
        "base_url": os.getenv("N8N_BASE_URL", "http://localhost:5678"),
        "webhook_base": os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook")
    },
    "langchain": {
        "base_url": os.getenv("LANGCHAIN_SERVICE_URL", "http://localhost:8001")
    },
    "streamlit": {
        "base_url": os.getenv("STREAMLIT_URL", "http://localhost:8501")
    }
}


@pytest.fixture(scope="session")
def db_connection() -> Generator:
    """Provide database connection for tests"""
    conn = psycopg2.connect(**TEST_CONFIG["postgres"])
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def db_cursor(db_connection):
    """Provide database cursor with transaction rollback"""
    cursor = db_connection.cursor()
    yield cursor
    db_connection.rollback()  # Rollback any changes made during test
    cursor.close()


@pytest.fixture(scope="session")
def test_user(db_connection) -> Dict:
    """Create a test user for the session"""
    cursor = db_connection.cursor()

    # Create test user
    cursor.execute("""
        INSERT INTO users (email, company, created_at)
        VALUES ('test@example.com', 'Test Corp', NOW())
        ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
        RETURNING id, email, company
    """)
    user = cursor.fetchone()
    db_connection.commit()
    cursor.close()

    return {
        "id": user[0],
        "email": user[1],
        "company": user[2]
    }


@pytest.fixture(scope="session")
def test_campaign(db_connection, test_user) -> Dict:
    """Create a test campaign for the session"""
    cursor = db_connection.cursor()

    # Create test campaign
    cursor.execute("""
        INSERT INTO campaigns (
            user_id, name, target_audience, branding_json, status, created_at
        )
        VALUES (
            %s, 'Test Campaign', 'Marketing professionals',
            '{"colors": ["#1E3A8A", "#FFFFFF"], "voice": "professional"}',
            'active', NOW()
        )
        RETURNING id, name, target_audience, branding_json
    """, (test_user["id"],))

    campaign = cursor.fetchone()
    db_connection.commit()
    cursor.close()

    return {
        "id": campaign[0],
        "name": campaign[1],
        "target_audience": campaign[2],
        "branding_json": campaign[3]
    }


@pytest.fixture
def mock_content_draft(db_connection, test_campaign) -> Dict:
    """Create a mock content draft for testing"""
    cursor = db_connection.cursor()

    cursor.execute("""
        INSERT INTO content_drafts (
            campaign_id, type, content, seo_score, status, created_at
        )
        VALUES (
            %s, 'linkedin_post',
            'This is test content for LinkedIn about AI in marketing.',
            85, 'draft', NOW()
        )
        RETURNING id, campaign_id, type, content, status
    """, (test_campaign["id"],))

    draft = cursor.fetchone()
    db_connection.commit()
    cursor.close()

    draft_dict = {
        "id": draft[0],
        "campaign_id": draft[1],
        "type": draft[2],
        "content": draft[3],
        "status": draft[4]
    }

    yield draft_dict

    # Cleanup after test
    cursor = db_connection.cursor()
    cursor.execute("DELETE FROM content_drafts WHERE id = %s", (draft_dict["id"],))
    db_connection.commit()
    cursor.close()


@pytest.fixture
def n8n_client():
    """Provide n8n API client"""
    class N8NClient:
        def __init__(self, base_url: str):
            self.base_url = base_url
            self.webhook_base = TEST_CONFIG["n8n"]["webhook_base"]

        def trigger_webhook(self, path: str, data: Dict) -> requests.Response:
            """Trigger an n8n webhook"""
            url = f"{self.webhook_base}/{path}"
            return requests.post(url, json=data, timeout=30)

        def get_workflow_status(self, workflow_id: str) -> Dict:
            """Get workflow execution status"""
            # Note: This requires n8n API to be accessible
            # In production, would use n8n API endpoints
            pass

    return N8NClient(TEST_CONFIG["n8n"]["base_url"])


@pytest.fixture
def langchain_client():
    """Provide LangChain service client"""
    class LangChainClient:
        def __init__(self, base_url: str):
            self.base_url = base_url

        def call_agent(self, agent: str, data: Dict) -> requests.Response:
            """Call a LangChain agent"""
            url = f"{self.base_url}/agents/{agent}"
            return requests.post(url, json=data, timeout=60)

        def call_tool(self, tool: str, data: Dict) -> requests.Response:
            """Call a LangChain tool"""
            url = f"{self.base_url}/tools/{tool}"
            return requests.post(url, json=data, timeout=30)

        def health_check(self) -> bool:
            """Check if LangChain service is healthy"""
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                return response.status_code == 200
            except:
                return False

    return LangChainClient(TEST_CONFIG["langchain"]["base_url"])


@pytest.fixture(scope="session")
def check_services():
    """Check if all required services are running"""
    services = {
        "PostgreSQL": TEST_CONFIG["postgres"],
        "n8n": TEST_CONFIG["n8n"]["base_url"],
        "LangChain": TEST_CONFIG["langchain"]["base_url"]
    }

    failures = []

    # Check PostgreSQL
    try:
        conn = psycopg2.connect(**TEST_CONFIG["postgres"])
        conn.close()
    except Exception as e:
        failures.append(f"PostgreSQL: {str(e)}")

    # Check n8n
    try:
        response = requests.get(TEST_CONFIG["n8n"]["base_url"], timeout=5)
    except Exception as e:
        failures.append(f"n8n: {str(e)}")

    # Check LangChain
    try:
        response = requests.get(f"{TEST_CONFIG['langchain']['base_url']}/health", timeout=5)
    except Exception as e:
        failures.append(f"LangChain: {str(e)}")

    if failures:
        pytest.skip(f"Required services not available: {', '.join(failures)}")

    return True


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires services running)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
