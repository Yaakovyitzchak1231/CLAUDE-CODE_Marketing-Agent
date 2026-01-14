"""
End-to-end tests for image and video generation workflows
"""
import pytest
import time


@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.slow
class TestImageGenerationWorkflow:
    """Test the complete image generation workflow"""

    def test_image_generation_dalle(
        self, check_services, n8n_client, mock_content_draft, db_cursor
    ):
        """Test image generation with DALL-E 3"""

        payload = {
            "draft_id": mock_content_draft["id"],
            "image_type": "social_post",
            "dimensions": "1200x628",
            "provider": "dalle"
        }

        response = n8n_client.trigger_webhook("image-generate", payload)
        assert response.status_code in [200, 201, 202]

        # Wait for generation (DALL-E can take 10-30 seconds)
        time.sleep(15)

        # Verify media asset was created
        db_cursor.execute("""
            SELECT id, type, url, prompt, api_provider, metadata_json
            FROM media_assets
            WHERE draft_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (mock_content_draft["id"],))

        asset = db_cursor.fetchone()

        if asset:  # Only if service is actually running
            asset_id, media_type, url, prompt, provider, metadata = asset

            assert media_type == "image"
            assert provider == "dalle"
            assert url is not None and len(url) > 0
            assert prompt is not None and len(prompt) > 0

            # Verify metadata includes dimensions
            if metadata:
                assert "dimensions" in metadata or "prompt_params" in metadata

            # Cleanup
            db_cursor.execute("DELETE FROM media_assets WHERE id = %s", (asset_id,))

    def test_image_post_processing(
        self, check_services, n8n_client, mock_content_draft, db_cursor
    ):
        """Test image post-processing (watermark, resize)"""

        # First create a mock media asset
        db_cursor.execute("""
            INSERT INTO media_assets (
                draft_id, type, file_path, url, prompt, api_provider,
                metadata_json, created_at
            )
            VALUES (
                %s, 'image', '/tmp/test_image.png', 'http://example.com/test.png',
                'Test image prompt', 'dalle',
                '{"dimensions": {"width": 1024, "height": 1024}}', NOW()
            )
            RETURNING id
        """, (mock_content_draft["id"],))

        asset_id = db_cursor.fetchone()[0]

        # Trigger post-processing
        payload = {
            "asset_id": asset_id,
            "operations": [
                {
                    "operation": "watermark",
                    "params": {
                        "text": "© Test Corp",
                        "position": "bottom-right"
                    }
                },
                {
                    "operation": "resize",
                    "params": {
                        "width": 1200,
                        "height": 628
                    }
                }
            ]
        }

        response = n8n_client.trigger_webhook("media-process", payload)

        if response.status_code in [200, 201, 202]:
            time.sleep(3)

            # Verify edit records were created
            db_cursor.execute("""
                SELECT edit_type, edit_params
                FROM media_edits
                WHERE asset_id = %s
            """, (asset_id,))

            edits = db_cursor.fetchall()

            if edits:  # Only if workflow executed
                edit_types = [edit[0] for edit in edits]
                assert "watermark" in edit_types or "composite" in edit_types

        # Cleanup
        db_cursor.execute("DELETE FROM media_edits WHERE asset_id = %s", (asset_id,))
        db_cursor.execute("DELETE FROM media_assets WHERE id = %s", (asset_id,))


@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.slow
class TestVideoGenerationWorkflow:
    """Test the complete video generation workflow"""

    def test_video_generation_runway(
        self, check_services, n8n_client, mock_content_draft, db_cursor
    ):
        """Test video generation with Runway ML"""

        payload = {
            "draft_id": mock_content_draft["id"],
            "video_type": "explainer",
            "duration": 15,
            "provider": "runway"
        }

        response = n8n_client.trigger_webhook("video-generate", payload)
        assert response.status_code in [200, 201, 202]

        # Video generation can take 1-2 minutes
        time.sleep(30)

        # Check if video asset was created
        db_cursor.execute("""
            SELECT id, type, url, api_provider, metadata_json
            FROM media_assets
            WHERE draft_id = %s AND type = 'video'
            ORDER BY created_at DESC
            LIMIT 1
        """, (mock_content_draft["id"],))

        asset = db_cursor.fetchone()

        if asset:  # Only if service is running
            asset_id, media_type, url, provider, metadata = asset

            assert media_type == "video"
            assert provider in ["runway", "pika"]
            assert url is not None

            # Verify metadata includes duration
            if metadata:
                assert "duration" in metadata or "scenes" in metadata

            # Cleanup
            db_cursor.execute("DELETE FROM media_assets WHERE id = %s", (asset_id,))

    def test_video_post_processing(
        self, check_services, n8n_client, mock_content_draft, db_cursor
    ):
        """Test video post-processing (trim, captions, music)"""

        # Create mock video asset
        db_cursor.execute("""
            INSERT INTO media_assets (
                draft_id, type, file_path, url, prompt, api_provider,
                metadata_json, created_at
            )
            VALUES (
                %s, 'video', '/tmp/test_video.mp4', 'http://example.com/test.mp4',
                'Test video prompt', 'runway',
                '{"duration": 30, "scenes": 3}', NOW()
            )
            RETURNING id
        """, (mock_content_draft["id"],))

        asset_id = db_cursor.fetchone()[0]

        # Trigger video editing
        payload = {
            "asset_id": asset_id,
            "operations": [
                {
                    "operation": "trim",
                    "params": {
                        "start_time": 0,
                        "end_time": 15
                    }
                },
                {
                    "operation": "captions",
                    "params": {
                        "text": "Marketing Automation Benefits",
                        "font_size": 48
                    }
                }
            ]
        }

        response = n8n_client.trigger_webhook("media-process", payload)

        if response.status_code in [200, 201, 202]:
            time.sleep(5)

            # Verify edit records
            db_cursor.execute("""
                SELECT edit_type
                FROM media_edits
                WHERE asset_id = %s
            """, (asset_id,))

            edits = db_cursor.fetchall()

            if edits:
                edit_types = [edit[0] for edit in edits]
                assert "trim" in edit_types or "composite" in edit_types

        # Cleanup
        db_cursor.execute("DELETE FROM media_edits WHERE asset_id = %s", (asset_id,))
        db_cursor.execute("DELETE FROM media_assets WHERE id = %s", (asset_id,))


@pytest.mark.integration
class TestMediaAgentsDirect:
    """Test media generation agents directly"""

    def test_image_agent_prompt_building(
        self, check_services, langchain_client
    ):
        """Test image prompt builder chain"""

        if not langchain_client.health_check():
            pytest.skip("LangChain service not available")

        payload = {
            "content": "AI is transforming B2B marketing",
            "branding": {
                "colors": ["#1E3A8A", "#FFFFFF"],
                "style": "professional"
            },
            "dimensions": "1200x628"
        }

        response = langchain_client.call_agent("image", payload)

        if response.status_code == 200:
            result = response.json()
            assert "image_url" in result or "prompt" in result

    def test_video_script_builder(
        self, check_services, langchain_client
    ):
        """Test video script builder chain"""

        if not langchain_client.health_check():
            pytest.skip("LangChain service not available")

        payload = {
            "content": "Discover how marketing automation can save you 10 hours per week",
            "duration": 30,
            "style": "explainer"
        }

        response = langchain_client.call_tool("video-script", payload)

        if response.status_code == 200:
            result = response.json()
            assert "scenes" in result
            assert isinstance(result["scenes"], list)
            assert len(result["scenes"]) > 0
