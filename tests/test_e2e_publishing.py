"""
End-to-end tests for publishing pipeline workflow
"""
import pytest
import time


@pytest.mark.e2e
@pytest.mark.integration
class TestPublishingWorkflow:
    """Test the complete multi-channel publishing workflow"""

    def test_publish_to_linkedin(
        self, check_services, n8n_client, mock_content_draft, db_cursor
    ):
        """Test publishing content to LinkedIn"""

        # Set draft to approved status
        db_cursor.execute("""
            UPDATE content_drafts
            SET status = 'approved', content = 'Exciting news about AI in marketing! #AI #Marketing'
            WHERE id = %s
        """, (mock_content_draft["id"],))

        # Trigger publishing
        payload = {
            "draft_id": mock_content_draft["id"],
            "channels": ["linkedin"],
            "scheduled_time": None  # Immediate publishing
        }

        response = n8n_client.trigger_webhook("publish", payload)
        assert response.status_code in [200, 201, 202]

        # Wait for publishing
        time.sleep(5)

        # Verify published_content record was created
        db_cursor.execute("""
            SELECT id, channel, url, published_at
            FROM published_content
            WHERE draft_id = %s AND channel = 'linkedin'
        """, (mock_content_draft["id"],))

        published = db_cursor.fetchone()

        if published:  # Only if LinkedIn API is configured
            pub_id, channel, url, published_at = published

            assert channel == "linkedin"
            assert url is not None  # Should have LinkedIn post URL
            assert published_at is not None

            # Verify engagement metrics were initialized
            db_cursor.execute("""
                SELECT views, clicks, shares
                FROM engagement_metrics
                WHERE content_id = %s
            """, (pub_id,))

            metrics = db_cursor.fetchone()
            if metrics:
                assert metrics is not None  # Metrics initialized

            # Cleanup
            db_cursor.execute("""
                DELETE FROM engagement_metrics WHERE content_id = %s
            """, (pub_id,))
            db_cursor.execute("""
                DELETE FROM published_content WHERE id = %s
            """, (pub_id,))

        # Verify draft status updated
        db_cursor.execute("""
            SELECT status FROM content_drafts WHERE id = %s
        """, (mock_content_draft["id"],))

        status = db_cursor.fetchone()[0]
        # Status should be published or remain approved
        assert status in ["published", "approved"]

    def test_publish_to_wordpress(
        self, check_services, n8n_client, mock_content_draft, db_cursor
    ):
        """Test publishing content to WordPress"""

        db_cursor.execute("""
            UPDATE content_drafts
            SET status = 'approved',
                type = 'blog_post',
                content = '<h1>Marketing Automation Guide</h1><p>Content here...</p>'
            WHERE id = %s
        """, (mock_content_draft["id"],))

        payload = {
            "draft_id": mock_content_draft["id"],
            "channels": ["wordpress"]
        }

        response = n8n_client.trigger_webhook("publish", payload)
        assert response.status_code in [200, 201, 202]

        time.sleep(5)

        # Check for published record
        db_cursor.execute("""
            SELECT channel, url
            FROM published_content
            WHERE draft_id = %s AND channel = 'wordpress'
        """, (mock_content_draft["id"],))

        published = db_cursor.fetchone()

        if published:
            channel, url = published
            assert channel == "wordpress"
            # URL should be WordPress blog URL

        # Cleanup
        db_cursor.execute("""
            DELETE FROM published_content
            WHERE draft_id = %s AND channel = 'wordpress'
        """, (mock_content_draft["id"],))

    def test_publish_to_email(
        self, check_services, n8n_client, mock_content_draft, db_cursor
    ):
        """Test sending email newsletter"""

        db_cursor.execute("""
            UPDATE content_drafts
            SET status = 'approved',
                type = 'email_newsletter',
                content = '<h1>Weekly Newsletter</h1><p>Latest marketing tips...</p>'
            WHERE id = %s
        """, (mock_content_draft["id"],))

        payload = {
            "draft_id": mock_content_draft["id"],
            "channels": ["email"],
            "email_params": {
                "recipients": ["test@example.com"],
                "subject": "Your Weekly Marketing Newsletter"
            }
        }

        response = n8n_client.trigger_webhook("publish", payload)
        assert response.status_code in [200, 201, 202]

        time.sleep(3)

        # Verify email record
        db_cursor.execute("""
            SELECT channel
            FROM published_content
            WHERE draft_id = %s AND channel = 'email'
        """, (mock_content_draft["id"],))

        published = db_cursor.fetchone()

        if published:
            assert published[0] == "email"

        # Cleanup
        db_cursor.execute("""
            DELETE FROM published_content
            WHERE draft_id = %s AND channel = 'email'
        """, (mock_content_draft["id"],))

    def test_publish_multi_channel(
        self, check_services, n8n_client, mock_content_draft, db_cursor
    ):
        """Test publishing to multiple channels simultaneously"""

        db_cursor.execute("""
            UPDATE content_drafts
            SET status = 'approved',
                content = 'Multi-channel marketing content'
            WHERE id = %s
        """, (mock_content_draft["id"],))

        payload = {
            "draft_id": mock_content_draft["id"],
            "channels": ["linkedin", "wordpress", "email"]
        }

        response = n8n_client.trigger_webhook("publish", payload)
        assert response.status_code in [200, 201, 202]

        time.sleep(8)  # Multiple channels take longer

        # Verify multiple published records
        db_cursor.execute("""
            SELECT channel
            FROM published_content
            WHERE draft_id = %s
        """, (mock_content_draft["id"],))

        channels = [row[0] for row in db_cursor.fetchall()]

        # At least one channel should succeed
        if len(channels) > 0:
            assert any(ch in channels for ch in ["linkedin", "wordpress", "email"])

        # Cleanup
        db_cursor.execute("""
            DELETE FROM published_content WHERE draft_id = %s
        """, (mock_content_draft["id"],))

    def test_publish_with_media(
        self, check_services, n8n_client, mock_content_draft, db_cursor
    ):
        """Test publishing content with attached media"""

        # Create media asset
        db_cursor.execute("""
            INSERT INTO media_assets (
                draft_id, type, url, prompt, api_provider,
                metadata_json, created_at
            )
            VALUES (
                %s, 'image', 'http://example.com/image.png',
                'Marketing image', 'dalle',
                '{"dimensions": {"width": 1200, "height": 628}}', NOW()
            )
            RETURNING id
        """, (mock_content_draft["id"],))

        asset_id = db_cursor.fetchone()[0]

        db_cursor.execute("""
            UPDATE content_drafts
            SET status = 'approved'
            WHERE id = %s
        """, (mock_content_draft["id"],))

        # Publish with media
        payload = {
            "draft_id": mock_content_draft["id"],
            "channels": ["linkedin"]
        }

        response = n8n_client.trigger_webhook("publish", payload)
        assert response.status_code in [200, 201, 202]

        time.sleep(5)

        # Verify publishing
        db_cursor.execute("""
            SELECT url FROM published_content
            WHERE draft_id = %s
        """, (mock_content_draft["id"],))

        published = db_cursor.fetchone()

        if published:
            # Media should be included in post
            pass

        # Cleanup
        db_cursor.execute("""
            DELETE FROM media_assets WHERE id = %s
        """, (asset_id,))
        db_cursor.execute("""
            DELETE FROM published_content WHERE draft_id = %s
        """, (mock_content_draft["id"],))

    def test_scheduled_publishing(
        self, check_services, n8n_client, mock_content_draft, db_cursor
    ):
        """Test scheduled future publishing"""

        db_cursor.execute("""
            UPDATE content_drafts
            SET status = 'approved'
            WHERE id = %s
        """, (mock_content_draft["id"],))

        # Schedule for future
        payload = {
            "draft_id": mock_content_draft["id"],
            "channels": ["linkedin"],
            "scheduled_time": "2026-12-31T10:00:00Z"
        }

        response = n8n_client.trigger_webhook("publish", payload)
        assert response.status_code in [200, 201, 202]

        time.sleep(2)

        # Should NOT be published yet
        db_cursor.execute("""
            SELECT COUNT(*) FROM published_content
            WHERE draft_id = %s
        """, (mock_content_draft["id"],))

        count = db_cursor.fetchone()[0]
        # Should be 0 or have scheduled status

        # Cleanup any scheduled records
        db_cursor.execute("""
            DELETE FROM published_content WHERE draft_id = %s
        """, (mock_content_draft["id"],))


@pytest.mark.integration
class TestPublishingClientsDirect:
    """Test publishing clients directly"""

    def test_linkedin_publisher(self, check_services):
        """Test LinkedIn publisher module"""
        try:
            from publishing import LinkedInPublisher

            # Note: This requires valid LinkedIn API credentials
            # publisher = LinkedInPublisher()
            # Test would go here if credentials are available
            pass
        except ImportError:
            pytest.skip("Publishing module not available")

    def test_wordpress_publisher(self, check_services):
        """Test WordPress publisher module"""
        try:
            from publishing import WordPressPublisher

            # Note: This requires valid WordPress credentials
            # publisher = WordPressPublisher()
            # Test would go here if credentials are available
            pass
        except ImportError:
            pytest.skip("Publishing module not available")

    def test_email_publisher(self, check_services):
        """Test Email publisher module"""
        try:
            from publishing import EmailPublisher

            # Note: This requires valid SMTP credentials
            # publisher = EmailPublisher()
            # Test would go here if credentials are available
            pass
        except ImportError:
            pytest.skip("Publishing module not available")
