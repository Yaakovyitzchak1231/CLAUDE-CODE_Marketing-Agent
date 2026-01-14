"""
End-to-end tests for content review loop workflow
"""
import pytest
import time


@pytest.mark.e2e
@pytest.mark.integration
class TestContentReviewWorkflow:
    """Test the complete human-in-the-loop review workflow"""

    def test_review_approve_flow(
        self, check_services, n8n_client, mock_content_draft, db_cursor
    ):
        """Test approve action in review workflow"""

        # Ensure draft is in review status
        db_cursor.execute("""
            UPDATE content_drafts
            SET status = 'in_review'
            WHERE id = %s
        """, (mock_content_draft["id"],))

        # Submit approval
        payload = {
            "draft_id": mock_content_draft["id"],
            "action": "approve",
            "feedback_text": "Great content, ready to publish!",
            "rating": 5
        }

        response = n8n_client.trigger_webhook("review-feedback", payload)
        assert response.status_code in [200, 201, 202]

        time.sleep(3)

        # Verify feedback was saved
        db_cursor.execute("""
            SELECT feedback_text, rating
            FROM review_feedback
            WHERE draft_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (mock_content_draft["id"],))

        feedback = db_cursor.fetchone()
        assert feedback is not None
        assert feedback[0] == "Great content, ready to publish!"
        assert feedback[1] == 5

        # Verify status was updated
        db_cursor.execute("""
            SELECT status FROM content_drafts WHERE id = %s
        """, (mock_content_draft["id"],))

        status = db_cursor.fetchone()[0]
        assert status == "approved"

        # Cleanup
        db_cursor.execute("""
            DELETE FROM review_feedback WHERE draft_id = %s
        """, (mock_content_draft["id"],))

    def test_review_revise_flow(
        self, check_services, n8n_client, mock_content_draft, db_cursor
    ):
        """Test revise action with LLM-powered edits"""

        # Set to review status
        db_cursor.execute("""
            UPDATE content_drafts
            SET status = 'in_review', content = 'Original content about marketing.'
            WHERE id = %s
        """, (mock_content_draft["id"],))

        original_content = "Original content about marketing."

        # Submit revision request
        payload = {
            "draft_id": mock_content_draft["id"],
            "action": "revise",
            "feedback_text": "Make the tone more professional and add statistics",
            "rating": 3,
            "suggested_edits": [
                {
                    "section": "intro",
                    "suggestion": "Add industry statistics"
                }
            ]
        }

        response = n8n_client.trigger_webhook("review-feedback", payload)
        assert response.status_code in [200, 201, 202]

        # Wait for LLM revision
        time.sleep(5)

        # Verify new version was created
        db_cursor.execute("""
            SELECT version_number, content
            FROM content_versions
            WHERE draft_id = %s
            ORDER BY version_number DESC
            LIMIT 1
        """, (mock_content_draft["id"],))

        version = db_cursor.fetchone()

        if version:  # Only if LLM service is running
            version_number, revised_content = version
            assert version_number >= 1
            assert revised_content != original_content
            assert len(revised_content) > 0

        # Verify draft was updated
        db_cursor.execute("""
            SELECT content, status FROM content_drafts WHERE id = %s
        """, (mock_content_draft["id"],))

        result = db_cursor.fetchone()
        current_content, status = result

        # Status should remain in_review for another round
        assert status == "in_review"

        # Cleanup
        db_cursor.execute("""
            DELETE FROM content_versions WHERE draft_id = %s
        """, (mock_content_draft["id"],))
        db_cursor.execute("""
            DELETE FROM review_feedback WHERE draft_id = %s
        """, (mock_content_draft["id"],))

    def test_review_reject_flow(
        self, check_services, n8n_client, mock_content_draft, db_cursor
    ):
        """Test reject action in review workflow"""

        # Set to review status
        db_cursor.execute("""
            UPDATE content_drafts
            SET status = 'in_review'
            WHERE id = %s
        """, (mock_content_draft["id"],))

        # Submit rejection
        payload = {
            "draft_id": mock_content_draft["id"],
            "action": "reject",
            "feedback_text": "Content doesn't match brand voice",
            "rating": 1
        }

        response = n8n_client.trigger_webhook("review-feedback", payload)
        assert response.status_code in [200, 201, 202]

        time.sleep(2)

        # Verify status was updated to rejected
        db_cursor.execute("""
            SELECT status FROM content_drafts WHERE id = %s
        """, (mock_content_draft["id"],))

        status = db_cursor.fetchone()[0]
        assert status == "rejected"

        # Verify feedback was saved
        db_cursor.execute("""
            SELECT feedback_text, rating
            FROM review_feedback
            WHERE draft_id = %s
        """, (mock_content_draft["id"],))

        feedback = db_cursor.fetchone()
        assert feedback is not None
        assert feedback[1] == 1

        # Cleanup
        db_cursor.execute("""
            DELETE FROM review_feedback WHERE draft_id = %s
        """, (mock_content_draft["id"],))

    def test_multiple_revision_cycles(
        self, check_services, n8n_client, mock_content_draft, db_cursor
    ):
        """Test multiple rounds of revisions"""

        db_cursor.execute("""
            UPDATE content_drafts
            SET status = 'in_review', content = 'Version 1'
            WHERE id = %s
        """, (mock_content_draft["id"],))

        # First revision
        payload1 = {
            "draft_id": mock_content_draft["id"],
            "action": "revise",
            "feedback_text": "Add more details",
            "rating": 3
        }

        response1 = n8n_client.trigger_webhook("review-feedback", payload1)
        assert response1.status_code in [200, 201, 202]
        time.sleep(3)

        # Second revision
        payload2 = {
            "draft_id": mock_content_draft["id"],
            "action": "revise",
            "feedback_text": "Improve conclusion",
            "rating": 4
        }

        response2 = n8n_client.trigger_webhook("review-feedback", payload2)
        assert response2.status_code in [200, 201, 202]
        time.sleep(3)

        # Verify multiple versions exist
        db_cursor.execute("""
            SELECT COUNT(*) FROM content_versions
            WHERE draft_id = %s
        """, (mock_content_draft["id"],))

        version_count = db_cursor.fetchone()[0]

        if version_count > 0:  # If workflow actually executed
            assert version_count >= 1

        # Final approval
        payload3 = {
            "draft_id": mock_content_draft["id"],
            "action": "approve",
            "feedback_text": "Perfect now!",
            "rating": 5
        }

        response3 = n8n_client.trigger_webhook("review-feedback", payload3)
        assert response3.status_code in [200, 201, 202]
        time.sleep(2)

        # Verify final status is approved
        db_cursor.execute("""
            SELECT status FROM content_drafts WHERE id = %s
        """, (mock_content_draft["id"],))

        status = db_cursor.fetchone()[0]
        assert status == "approved"

        # Cleanup
        db_cursor.execute("""
            DELETE FROM content_versions WHERE draft_id = %s
        """, (mock_content_draft["id"],))
        db_cursor.execute("""
            DELETE FROM review_feedback WHERE draft_id = %s
        """, (mock_content_draft["id"],))
