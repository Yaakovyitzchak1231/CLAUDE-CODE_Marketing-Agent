"""
LinkedIn Publisher
Handles posting content to LinkedIn using the LinkedIn API
"""

import httpx
import structlog
from typing import Optional, List, Dict, Any

logger = structlog.get_logger()


class LinkedInPublisher:
    """
    LinkedIn content publisher

    Uses LinkedIn Marketing API to create posts
    """

    def __init__(self):
        self.api_base_url = "https://api.linkedin.com/v2"

    async def publish(
        self,
        access_token: str,
        text: str,
        title: Optional[str] = None,
        media_urls: Optional[List[str]] = None,
        visibility: str = "PUBLIC"
    ) -> Dict[str, Any]:
        """
        Publish content to LinkedIn

        Args:
            access_token: LinkedIn OAuth access token
            text: Post content text
            title: Optional post title (for articles)
            media_urls: Optional list of media URLs to attach
            visibility: Post visibility (PUBLIC, CONNECTIONS)

        Returns:
            Dictionary with post details and LinkedIn post ID
        """
        try:
            # Get the authenticated user's ID
            user_urn = await self._get_user_urn(access_token)

            # Build the post content
            post_data = {
                "author": user_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": visibility
                }
            }

            # Handle media attachments if provided
            if media_urls:
                media_assets = await self._upload_media(access_token, user_urn, media_urls)
                if media_assets:
                    post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
                    post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = media_assets

            # Create the post
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/ugcPosts",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                        "X-Restli-Protocol-Version": "2.0.0"
                    },
                    json=post_data
                )

                if response.status_code != 201:
                    error_detail = response.text
                    logger.error("linkedin_post_failed", status=response.status_code, error=error_detail)
                    raise Exception(f"LinkedIn post failed: {error_detail}")

                post_id = response.headers.get("X-RestLi-Id", "")

                logger.info("linkedin_post_created", post_id=post_id)

                return {
                    "post_id": post_id,
                    "platform": "linkedin",
                    "url": f"https://www.linkedin.com/feed/update/{post_id}",
                    "visibility": visibility,
                    "text_length": len(text),
                    "media_count": len(media_urls) if media_urls else 0
                }

        except Exception as e:
            logger.error("linkedin_publish_error", error=str(e))
            raise

    async def _get_user_urn(self, access_token: str) -> str:
        """Get the authenticated user's LinkedIn URN"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_base_url}/me",
                headers={
                    "Authorization": f"Bearer {access_token}"
                }
            )

            if response.status_code != 200:
                raise Exception(f"Failed to get LinkedIn user info: {response.text}")

            user_data = response.json()
            return f"urn:li:person:{user_data['id']}"

    async def _upload_media(
        self,
        access_token: str,
        user_urn: str,
        media_urls: List[str]
    ) -> List[Dict[str, Any]]:
        """Upload media files to LinkedIn and return asset URNs"""
        media_assets = []

        for media_url in media_urls:
            try:
                # Register the upload
                register_data = {
                    "registerUploadRequest": {
                        "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                        "owner": user_urn,
                        "serviceRelationships": [
                            {
                                "relationshipType": "OWNER",
                                "identifier": "urn:li:userGeneratedContent"
                            }
                        ]
                    }
                }

                async with httpx.AsyncClient() as client:
                    # Register upload
                    register_response = await client.post(
                        f"{self.api_base_url}/assets?action=registerUpload",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Content-Type": "application/json"
                        },
                        json=register_data
                    )

                    if register_response.status_code != 200:
                        logger.warning("linkedin_media_register_failed", url=media_url)
                        continue

                    register_result = register_response.json()
                    upload_url = register_result["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
                    asset_urn = register_result["value"]["asset"]

                    # Download the image
                    image_response = await client.get(media_url)
                    if image_response.status_code != 200:
                        logger.warning("linkedin_media_download_failed", url=media_url)
                        continue

                    # Upload to LinkedIn
                    upload_response = await client.put(
                        upload_url,
                        headers={
                            "Authorization": f"Bearer {access_token}"
                        },
                        content=image_response.content
                    )

                    if upload_response.status_code in [200, 201]:
                        media_assets.append({
                            "status": "READY",
                            "media": asset_urn
                        })

            except Exception as e:
                logger.warning("linkedin_media_upload_error", url=media_url, error=str(e))
                continue

        return media_assets
