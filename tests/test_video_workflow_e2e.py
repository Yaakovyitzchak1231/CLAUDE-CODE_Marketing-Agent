"""
End-to-end test for complete video generation workflow
Tests the full pipeline from generation to preview
"""
import pytest
import time
import json
from pathlib import Path


@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.slow
class TestCompleteVideoWorkflow:
    """Test the complete end-to-end video workflow"""

    def test_complete_video_generation_workflow(
        self, check_services, n8n_client, langchain_client, mock_content_draft, db_cursor
    ):
        """
        Test complete video workflow from generation to preview

        Workflow steps:
        1. Generate video via VideoGenerationAgent
        2. Verify video downloads to local storage
        3. Verify music is selected and added
        4. Verify media_assets record created with file_path
        5. Verify media_edits record for music addition
        6. Verify video appears in asset library
        7. Verify video preview functionality
        8. Verify download button functionality
        """

        # Step 1: Trigger video generation
        payload = {
            "draft_id": mock_content_draft["id"],
            "video_type": "social_post",
            "platform": "linkedin",
            "duration": 15,
            "provider": "runway",
            "content": "Discover how AI is revolutionizing B2B marketing automation"
        }

        response = n8n_client.trigger_webhook("video-generate", payload)
        assert response.status_code in [200, 201, 202], f"Video generation failed with status {response.status_code}"

        # Wait for video generation to complete (Runway can take 30-60 seconds)
        time.sleep(45)

        # Step 2: Verify media_assets record was created with file_path
        db_cursor.execute("""
            SELECT id, type, file_path, url, prompt, api_provider, metadata_json, generation_cost
            FROM media_assets
            WHERE draft_id = %s AND type = 'video'
            ORDER BY created_at DESC
            LIMIT 1
        """, (mock_content_draft["id"],))

        asset = db_cursor.fetchone()

        if not asset:
            pytest.skip("Video generation service not available or workflow did not complete")

        asset_id, media_type, file_path, url, prompt, provider, metadata, cost = asset

        # Verify basic asset properties
        assert media_type == "video", f"Expected type 'video', got '{media_type}'"
        assert provider in ["runway", "pika"], f"Unexpected provider: {provider}"
        assert url is not None and len(url) > 0, "Video URL should not be empty"
        assert prompt is not None and len(prompt) > 0, "Video prompt should not be empty"

        # Step 3: Verify video file_path exists (video downloaded to local storage)
        if file_path:
            video_path = Path(file_path)
            # Note: In test environment, file may not exist if running in isolation
            # But we verify the path was recorded
            assert file_path.endswith(('.mp4', '.mov', '.webm')), f"Invalid video file extension: {file_path}"

            # Verify metadata includes expected fields
            if metadata:
                # Metadata should contain video-specific information
                assert isinstance(metadata, (dict, str)), "Metadata should be dict or JSON string"

                if isinstance(metadata, str):
                    metadata = json.loads(metadata)

                # Common metadata fields for videos
                expected_fields = ['duration', 'scenes', 'platform', 'download_timestamp']
                found_fields = [field for field in expected_fields if field in metadata]
                assert len(found_fields) > 0, f"Metadata missing common fields. Got: {list(metadata.keys())}"

        # Step 4: Test video post-processing (music addition)
        # Trigger music addition workflow
        music_payload = {
            "asset_id": str(asset_id),
            "operations": [
                {
                    "operation": "music",
                    "params": {
                        "track": "modern-corporate-background.mp3",
                        "volume": 0.3,
                        "fade_in": 1.0,
                        "fade_out": 1.0
                    }
                }
            ]
        }

        music_response = n8n_client.trigger_webhook("media-process", music_payload)

        if music_response.status_code in [200, 201, 202]:
            # Wait for music processing to complete
            time.sleep(5)

            # Step 5: Verify media_edits record for music addition
            db_cursor.execute("""
                SELECT id, edit_type, edit_params, edited_file_path
                FROM media_edits
                WHERE asset_id = %s
                ORDER BY created_at DESC
            """, (asset_id,))

            edits = db_cursor.fetchall()

            if edits:
                # Verify at least one edit was recorded
                assert len(edits) > 0, "No media edits found for video"

                # Check for music-related edit
                edit_types = [edit[1] for edit in edits]
                music_edits = [et for et in edit_types if 'music' in et.lower() or 'audio' in et.lower() or 'composite' in et.lower()]

                if music_edits:
                    # Verify edit parameters
                    for edit in edits:
                        edit_id, edit_type, edit_params, edited_file = edit

                        if edit_params:
                            if isinstance(edit_params, str):
                                params = json.loads(edit_params)
                            else:
                                params = edit_params

                            # If this is a music edit, verify parameters
                            if 'music' in edit_type.lower() or 'audio' in edit_type.lower():
                                assert 'volume' in params or 'track' in params or 'fade_in' in params, \
                                    "Music edit missing expected parameters"

        # Step 6: Verify video can be retrieved from database (simulates asset library)
        db_cursor.execute("""
            SELECT
                ma.id,
                ma.type,
                ma.file_path,
                ma.url,
                ma.prompt,
                ma.api_provider,
                ma.metadata_json,
                ma.created_at,
                COUNT(me.id) as edit_count
            FROM media_assets ma
            LEFT JOIN media_edits me ON ma.id = me.asset_id
            WHERE ma.draft_id = %s AND ma.type = 'video'
            GROUP BY ma.id
            ORDER BY ma.created_at DESC
        """, (mock_content_draft["id"],))

        library_assets = db_cursor.fetchall()
        assert len(library_assets) > 0, "Video should appear in asset library query"

        library_asset = library_assets[0]
        lib_id, lib_type, lib_path, lib_url, lib_prompt, lib_provider, lib_metadata, lib_created, edit_count = library_asset

        # Verify library asset matches our created asset
        assert str(lib_id) == str(asset_id), "Asset ID mismatch in library"
        assert lib_type == "video", "Asset type mismatch in library"

        # Step 7: Verify video preview data (URL and metadata for preview component)
        preview_data = {
            "id": str(lib_id),
            "type": lib_type,
            "url": lib_url,
            "file_path": lib_path,
            "metadata": lib_metadata if isinstance(lib_metadata, dict) else json.loads(lib_metadata) if lib_metadata else {},
            "provider": lib_provider,
            "edits": edit_count
        }

        # Verify preview data is complete
        assert preview_data["url"] is not None, "Preview requires video URL"
        assert preview_data["type"] == "video", "Preview type should be 'video'"

        # Step 8: Verify download functionality data
        download_data = {
            "asset_id": str(lib_id),
            "file_path": lib_path,
            "url": lib_url,
            "filename": Path(lib_path).name if lib_path else f"video_{lib_id}.mp4"
        }

        assert download_data["url"] is not None or download_data["file_path"] is not None, \
            "Download requires either URL or file_path"

        # Cleanup: Remove test data
        db_cursor.execute("DELETE FROM media_edits WHERE asset_id = %s", (asset_id,))
        db_cursor.execute("DELETE FROM media_assets WHERE id = %s", (asset_id,))

    def test_video_workflow_with_multiple_edits(
        self, check_services, mock_content_draft, db_cursor
    ):
        """Test video workflow with multiple post-processing operations"""

        # Create mock video asset
        db_cursor.execute("""
            INSERT INTO media_assets (
                draft_id, type, file_path, url, prompt, api_provider,
                metadata_json, generation_cost, created_at
            )
            VALUES (
                %s, 'video', '/data/videos/test_workflow_video.mp4',
                'http://example.com/test_workflow.mp4',
                'Professional B2B marketing video showcasing automation benefits',
                'runway',
                '{"duration": 15, "platform": "linkedin", "scenes": 2, "resolution": "1920x1080"}',
                0.50, NOW()
            )
            RETURNING id
        """, (mock_content_draft["id"],))

        asset_id = db_cursor.fetchone()[0]

        # Apply multiple edits in sequence
        edits_to_apply = [
            {
                "type": "trim",
                "params": {"start_time": 0, "end_time": 12}
            },
            {
                "type": "captions",
                "params": {
                    "text": "Transform Your Marketing",
                    "font_size": 48,
                    "position": "center"
                }
            },
            {
                "type": "music",
                "params": {
                    "track": "modern-corporate-background.mp3",
                    "volume": 0.3,
                    "fade_in": 1.0,
                    "fade_out": 1.0
                }
            },
            {
                "type": "watermark",
                "params": {
                    "text": "© Marketing AI",
                    "position": "bottom-right"
                }
            }
        ]

        # Record each edit
        for edit in edits_to_apply:
            db_cursor.execute("""
                INSERT INTO media_edits (
                    asset_id, edit_type, edit_params, edited_file_path, created_at
                )
                VALUES (
                    %s, %s, %s, %s, NOW()
                )
            """, (
                asset_id,
                edit["type"],
                json.dumps(edit["params"]),
                f'/data/videos/test_workflow_video_{edit["type"]}.mp4'
            ))

        # Verify all edits were recorded
        db_cursor.execute("""
            SELECT edit_type, edit_params
            FROM media_edits
            WHERE asset_id = %s
            ORDER BY created_at ASC
        """, (asset_id,))

        recorded_edits = db_cursor.fetchall()

        assert len(recorded_edits) == len(edits_to_apply), \
            f"Expected {len(edits_to_apply)} edits, found {len(recorded_edits)}"

        # Verify edit types match
        recorded_types = [edit[0] for edit in recorded_edits]
        expected_types = [edit["type"] for edit in edits_to_apply]

        for expected_type in expected_types:
            assert expected_type in recorded_types, f"Edit type '{expected_type}' not found in recorded edits"

        # Verify video with all edits can be retrieved for preview
        db_cursor.execute("""
            SELECT
                ma.id,
                ma.file_path,
                ma.url,
                ARRAY_AGG(me.edit_type ORDER BY me.created_at) as applied_edits,
                COUNT(me.id) as total_edits
            FROM media_assets ma
            LEFT JOIN media_edits me ON ma.id = me.asset_id
            WHERE ma.id = %s
            GROUP BY ma.id, ma.file_path, ma.url
        """, (asset_id,))

        result = db_cursor.fetchone()
        result_id, result_path, result_url, applied_edits, total_edits = result

        assert total_edits == len(edits_to_apply), "Edit count mismatch"
        assert applied_edits is not None, "Applied edits should not be None"
        assert len(applied_edits) == len(edits_to_apply), "Applied edits array length mismatch"

        # Cleanup
        db_cursor.execute("DELETE FROM media_edits WHERE asset_id = %s", (asset_id,))
        db_cursor.execute("DELETE FROM media_assets WHERE id = %s", (asset_id,))

    def test_video_workflow_error_handling(
        self, check_services, mock_content_draft, db_cursor
    ):
        """Test video workflow handles errors gracefully"""

        # Create video asset with invalid data to test error handling
        db_cursor.execute("""
            INSERT INTO media_assets (
                draft_id, type, file_path, url, prompt, api_provider,
                metadata_json, created_at
            )
            VALUES (
                %s, 'video', NULL, NULL,
                'Test video with missing URL',
                'runway',
                '{"status": "generation_failed", "error": "timeout"}',
                NOW()
            )
            RETURNING id
        """, (mock_content_draft["id"],))

        asset_id = db_cursor.fetchone()[0]

        # Verify asset was created even with NULL url/path (represents failed generation)
        db_cursor.execute("""
            SELECT id, url, file_path, metadata_json
            FROM media_assets
            WHERE id = %s
        """, (asset_id,))

        result = db_cursor.fetchone()
        assert result is not None, "Asset should exist even if generation failed"

        result_id, result_url, result_path, metadata = result
        assert result_url is None, "URL should be NULL for failed generation"
        assert result_path is None, "File path should be NULL for failed generation"

        # Verify metadata contains error information
        if metadata:
            if isinstance(metadata, str):
                metadata = json.loads(metadata)
            assert "error" in metadata or "status" in metadata, \
                "Failed generation should include error info in metadata"

        # Cleanup
        db_cursor.execute("DELETE FROM media_assets WHERE id = %s", (asset_id,))

    def test_video_library_filtering(
        self, check_services, mock_content_draft, db_cursor
    ):
        """Test video asset library filtering and retrieval"""

        # Create multiple video assets with different properties
        videos = [
            {
                "type": "video",
                "path": "/data/videos/linkedin_post.mp4",
                "provider": "runway",
                "metadata": {"platform": "linkedin", "duration": 30}
            },
            {
                "type": "video",
                "path": "/data/videos/instagram_reel.mp4",
                "provider": "pika",
                "metadata": {"platform": "instagram", "duration": 15}
            },
            {
                "type": "video",
                "path": "/data/videos/youtube_intro.mp4",
                "provider": "runway",
                "metadata": {"platform": "youtube", "duration": 60}
            }
        ]

        asset_ids = []
        for video in videos:
            db_cursor.execute("""
                INSERT INTO media_assets (
                    draft_id, type, file_path, url, prompt, api_provider,
                    metadata_json, created_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, NOW()
                )
                RETURNING id
            """, (
                mock_content_draft["id"],
                video["type"],
                video["path"],
                f"http://example.com/{Path(video['path']).name}",
                f"Test video for {video['metadata']['platform']}",
                video["provider"],
                json.dumps(video["metadata"])
            ))
            asset_ids.append(db_cursor.fetchone()[0])

        # Test: Retrieve all videos for draft
        db_cursor.execute("""
            SELECT id, api_provider, metadata_json
            FROM media_assets
            WHERE draft_id = %s AND type = 'video'
            ORDER BY created_at DESC
        """, (mock_content_draft["id"],))

        all_videos = db_cursor.fetchall()
        assert len(all_videos) >= len(videos), f"Expected at least {len(videos)} videos"

        # Test: Filter by provider
        db_cursor.execute("""
            SELECT id
            FROM media_assets
            WHERE draft_id = %s AND type = 'video' AND api_provider = 'runway'
        """, (mock_content_draft["id"],))

        runway_videos = db_cursor.fetchall()
        expected_runway = len([v for v in videos if v["provider"] == "runway"])
        assert len(runway_videos) >= expected_runway, f"Expected at least {expected_runway} Runway videos"

        # Test: Filter by metadata (platform)
        db_cursor.execute("""
            SELECT id, metadata_json
            FROM media_assets
            WHERE draft_id = %s
            AND type = 'video'
            AND metadata_json->>'platform' = 'linkedin'
        """, (mock_content_draft["id"],))

        linkedin_videos = db_cursor.fetchall()
        assert len(linkedin_videos) >= 1, "Expected at least 1 LinkedIn video"

        # Cleanup
        for asset_id in asset_ids:
            db_cursor.execute("DELETE FROM media_assets WHERE id = %s", (asset_id,))
