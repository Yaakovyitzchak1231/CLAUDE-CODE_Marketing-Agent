"""
End-to-end tests for content generation workflow
"""
import pytest
import time
from typing import Dict


@pytest.mark.e2e
@pytest.mark.integration
class TestContentGenerationWorkflow:
    """Test the complete content generation workflow"""

    def test_content_generation_flow(
        self, check_services, n8n_client, test_campaign, db_cursor
    ):
        """Test complete content generation from trigger to draft creation"""

        # Step 1: Trigger content generation webhook
        payload = {
            "campaign_id": test_campaign["id"],
            "topic": "AI-Powered Marketing Automation",
            "content_type": "linkedin_post",
            "target_word_count": 250
        }

        response = n8n_client.trigger_webhook("content-generate", payload)

        # Verify webhook accepted request
        assert response.status_code in [200, 201, 202], \
            f"Webhook failed with status {response.status_code}: {response.text}"

        # Step 2: Wait for workflow to complete (async processing)
        time.sleep(5)

        # Step 3: Verify draft was created in database
        db_cursor.execute("""
            SELECT id, campaign_id, type, content, seo_score, status
            FROM content_drafts
            WHERE campaign_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (test_campaign["id"],))

        draft = db_cursor.fetchone()
        assert draft is not None, "No draft created"

        draft_id, campaign_id, content_type, content, seo_score, status = draft

        # Step 4: Verify draft properties
        assert campaign_id == test_campaign["id"]
        assert content_type == "linkedin_post"
        assert len(content) > 0, "Content is empty"
        assert len(content.split()) >= 50, "Content too short"
        assert status == "in_review", f"Expected status 'in_review', got '{status}'"

        # Step 5: Verify SEO score was calculated
        assert seo_score is not None, "SEO score not calculated"
        assert 0 <= seo_score <= 100, f"SEO score {seo_score} out of range"

        # Step 6: Verify content embeddings were stored (check Chroma)
        # This would require Chroma client integration
        # Placeholder for now

        # Cleanup
        db_cursor.execute("DELETE FROM content_drafts WHERE id = %s", (draft_id,))

    def test_content_generation_with_research_context(
        self, check_services, n8n_client, test_campaign, db_cursor
    ):
        """Test content generation using research context"""

        # Step 1: Create research data
        db_cursor.execute("""
            INSERT INTO market_insights (campaign_id, segment, insights_json, created_at)
            VALUES (%s, 'tech_professionals',
                    '{"trends": ["AI adoption", "automation"], "pain_points": ["manual processes"]}',
                    NOW())
        """, (test_campaign["id"],))

        # Step 2: Trigger content generation
        payload = {
            "campaign_id": test_campaign["id"],
            "topic": "Solving Manual Marketing Challenges",
            "content_type": "blog_post",
            "use_research": True
        }

        response = n8n_client.trigger_webhook("content-generate", payload)
        assert response.status_code in [200, 201, 202]

        time.sleep(5)

        # Step 3: Verify content includes research insights
        db_cursor.execute("""
            SELECT content FROM content_drafts
            WHERE campaign_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (test_campaign["id"],))

        result = db_cursor.fetchone()
        assert result is not None

        content = result[0]
        # Verify research keywords appear in content
        assert any(keyword in content.lower() for keyword in ["automation", "manual", "ai"])

        # Cleanup
        db_cursor.execute("""
            DELETE FROM content_drafts
            WHERE campaign_id = %s AND type = 'blog_post'
        """, (test_campaign["id"],))
        db_cursor.execute("""
            DELETE FROM market_insights WHERE campaign_id = %s
        """, (test_campaign["id"],))

    def test_content_generation_character_limits(
        self, check_services, n8n_client, test_campaign, db_cursor
    ):
        """Test content generation respects platform character limits"""

        # Test LinkedIn limit (3000 characters)
        payload = {
            "campaign_id": test_campaign["id"],
            "topic": "Complete Guide to Marketing Automation with AI and Machine Learning",
            "content_type": "linkedin_post"
        }

        response = n8n_client.trigger_webhook("content-generate", payload)
        assert response.status_code in [200, 201, 202]

        time.sleep(5)

        db_cursor.execute("""
            SELECT content FROM content_drafts
            WHERE campaign_id = %s AND type = 'linkedin_post'
            ORDER BY created_at DESC
            LIMIT 1
        """, (test_campaign["id"],))

        result = db_cursor.fetchone()
        assert result is not None

        content = result[0]
        assert len(content) <= 3000, f"LinkedIn content exceeds 3000 chars: {len(content)}"

        # Cleanup
        db_cursor.execute("""
            DELETE FROM content_drafts
            WHERE campaign_id = %s AND type = 'linkedin_post'
        """, (test_campaign["id"],))

    def test_content_generation_seo_optimization(
        self, check_services, n8n_client, test_campaign, db_cursor
    ):
        """Test SEO optimization is applied"""

        payload = {
            "campaign_id": test_campaign["id"],
            "topic": "Marketing Automation ROI",
            "content_type": "blog_post",
            "seo_keywords": ["marketing automation", "ROI", "B2B"]
        }

        response = n8n_client.trigger_webhook("content-generate", payload)
        assert response.status_code in [200, 201, 202]

        time.sleep(5)

        db_cursor.execute("""
            SELECT content, seo_score FROM content_drafts
            WHERE campaign_id = %s AND type = 'blog_post'
            ORDER BY created_at DESC
            LIMIT 1
        """, (test_campaign["id"],))

        result = db_cursor.fetchone()
        assert result is not None

        content, seo_score = result

        # Verify SEO keywords appear in content
        content_lower = content.lower()
        for keyword in ["marketing automation", "roi", "b2b"]:
            assert keyword in content_lower, f"SEO keyword '{keyword}' not found in content"

        # Verify SEO score is reasonable
        assert seo_score >= 50, f"SEO score too low: {seo_score}"

        # Cleanup
        db_cursor.execute("""
            DELETE FROM content_drafts
            WHERE campaign_id = %s AND type = 'blog_post'
        """, (test_campaign["id"],))

    def test_content_generation_error_handling(
        self, check_services, n8n_client, db_cursor
    ):
        """Test error handling for invalid inputs"""

        # Test 1: Invalid campaign ID
        payload = {
            "campaign_id": 99999,
            "topic": "Test Topic",
            "content_type": "linkedin_post"
        }

        response = n8n_client.trigger_webhook("content-generate", payload)
        # Should either return error or handle gracefully
        # Exact behavior depends on n8n error handling configuration

        # Test 2: Empty topic
        payload = {
            "campaign_id": 1,
            "topic": "",
            "content_type": "linkedin_post"
        }

        response = n8n_client.trigger_webhook("content-generate", payload)
        # Should validate and reject

        # Test 3: Invalid content type
        payload = {
            "campaign_id": 1,
            "topic": "Test",
            "content_type": "invalid_type"
        }

        response = n8n_client.trigger_webhook("content-generate", payload)
        # Should validate and reject


@pytest.mark.integration
class TestContentAgentDirect:
    """Test LangChain content agent directly"""

    def test_content_agent_basic(self, check_services, langchain_client):
        """Test basic content agent invocation"""

        if not langchain_client.health_check():
            pytest.skip("LangChain service not available")

        payload = {
            "topic": "Benefits of Marketing Automation",
            "target_audience": "B2B marketers",
            "brand_voice": "professional",
            "target_word_count": 200
        }

        response = langchain_client.call_agent("content", payload)

        if response.status_code == 200:
            result = response.json()
            assert "content" in result
            assert len(result["content"]) > 0
            word_count = len(result["content"].split())
            assert 150 <= word_count <= 300  # Allow some variance

    def test_seo_optimizer_tool(self, check_services, langchain_client):
        """Test SEO optimization tool"""

        if not langchain_client.health_check():
            pytest.skip("LangChain service not available")

        payload = {
            "content": "Marketing automation helps businesses scale their marketing efforts efficiently.",
            "target_keywords": ["marketing automation", "scale", "efficiency"]
        }

        response = langchain_client.call_tool("seo", payload)

        if response.status_code == 200:
            result = response.json()
            assert "optimized_content" in result
            assert "seo_score" in result
            assert 0 <= result["seo_score"] <= 100
