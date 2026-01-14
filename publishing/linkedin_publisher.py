"""
LinkedIn API Publisher
Handles publishing text posts and media content to LinkedIn via API
"""

import requests
import os
from typing import Dict, List, Optional
from datetime import datetime
import json
import time


class LinkedInPublisher:
    """LinkedIn API client for publishing content"""

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize LinkedIn publisher

        Args:
            access_token: LinkedIn OAuth 2.0 access token
        """
        self.access_token = access_token or os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.api_base_url = "https://api.linkedin.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }

    def get_user_info(self) -> Dict:
        """Get authenticated user's profile information"""
        url = f"{self.api_base_url}/me"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch user info: {str(e)}")

    def create_text_post(self, text: str, visibility: str = "PUBLIC") -> Dict:
        """
        Create a text-only post on LinkedIn

        Args:
            text: Post content (max 3000 characters)
            visibility: Post visibility (PUBLIC, CONNECTIONS, LOGGED_IN)

        Returns:
            Response containing post ID and URL
        """
        # Validate text length
        if len(text) > 3000:
            raise ValueError("LinkedIn posts are limited to 3000 characters")

        # Get user URN
        user_info = self.get_user_info()
        author_urn = f"urn:li:person:{user_info['id']}"

        # Prepare post payload
        payload = {
            "author": author_urn,
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

        # Create post
        url = f"{self.api_base_url}/ugcPosts"

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            post_data = response.json()
            post_id = post_data.get("id")

            # Construct post URL
            post_url = f"https://www.linkedin.com/feed/update/{post_id}/"

            return {
                "success": True,
                "post_id": post_id,
                "url": post_url,
                "created_at": datetime.now().isoformat()
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create LinkedIn post: {str(e)}")

    def upload_image(self, image_url: str) -> str:
        """
        Upload an image to LinkedIn and return the asset URN

        Args:
            image_url: Public URL of the image to upload

        Returns:
            LinkedIn asset URN
        """
        # Get user URN
        user_info = self.get_user_info()
        author_urn = f"urn:li:person:{user_info['id']}"

        # Step 1: Register upload
        register_payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                "owner": author_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }

        register_url = f"{self.api_base_url}/assets?action=registerUpload"

        try:
            register_response = requests.post(
                register_url,
                headers=self.headers,
                json=register_payload,
                timeout=30
            )
            register_response.raise_for_status()
            register_data = register_response.json()

            upload_url = register_data["value"]["uploadMechanism"][
                "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
            ]["uploadUrl"]
            asset_urn = register_data["value"]["asset"]

            # Step 2: Download image from URL
            image_response = requests.get(image_url, timeout=30)
            image_response.raise_for_status()
            image_data = image_response.content

            # Step 3: Upload image to LinkedIn
            upload_headers = {
                "Authorization": f"Bearer {self.access_token}"
            }

            upload_response = requests.put(
                upload_url,
                headers=upload_headers,
                data=image_data,
                timeout=60
            )
            upload_response.raise_for_status()

            # Wait for processing
            time.sleep(2)

            return asset_urn
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to upload image to LinkedIn: {str(e)}")

    def upload_video(self, video_url: str, title: str, description: str = "") -> str:
        """
        Upload a video to LinkedIn and return the asset URN

        Args:
            video_url: Public URL of the video to upload
            title: Video title
            description: Video description

        Returns:
            LinkedIn asset URN
        """
        # Get user URN
        user_info = self.get_user_info()
        author_urn = f"urn:li:person:{user_info['id']}"

        # Download video to get size
        video_response = requests.get(video_url, timeout=60)
        video_response.raise_for_status()
        video_data = video_response.content
        video_size = len(video_data)

        # Step 1: Initialize upload
        init_payload = {
            "initializeUploadRequest": {
                "owner": author_urn,
                "fileSizeBytes": video_size,
                "uploadCaptions": False,
                "uploadThumbnail": False
            }
        }

        init_url = f"{self.api_base_url}/videos?action=initializeUpload"

        try:
            init_response = requests.post(
                init_url,
                headers=self.headers,
                json=init_payload,
                timeout=30
            )
            init_response.raise_for_status()
            init_data = init_response.json()

            video_urn = init_data["value"]["video"]
            upload_instructions = init_data["value"]["uploadInstructions"]

            # Step 2: Upload video in parts
            for instruction in upload_instructions:
                upload_url = instruction["uploadUrl"]
                first_byte = instruction["firstByte"]
                last_byte = instruction["lastByte"]

                chunk = video_data[first_byte:last_byte + 1]

                upload_headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/octet-stream"
                }

                upload_response = requests.put(
                    upload_url,
                    headers=upload_headers,
                    data=chunk,
                    timeout=120
                )
                upload_response.raise_for_status()

            # Step 3: Finalize upload
            finalize_payload = {
                "finalizeUploadRequest": {
                    "video": video_urn,
                    "uploadToken": "",
                    "uploadedPartIds": []
                }
            }

            finalize_url = f"{self.api_base_url}/videos?action=finalizeUpload"
            finalize_response = requests.post(
                finalize_url,
                headers=self.headers,
                json=finalize_payload,
                timeout=30
            )
            finalize_response.raise_for_status()

            return video_urn
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to upload video to LinkedIn: {str(e)}")

    def create_post_with_media(self, text: str, media_urls: List[str],
                               media_type: str = "image",
                               visibility: str = "PUBLIC") -> Dict:
        """
        Create a LinkedIn post with media (images or video)

        Args:
            text: Post content
            media_urls: List of media URLs (max 9 images or 1 video)
            media_type: 'image' or 'video'
            visibility: Post visibility

        Returns:
            Response containing post ID and URL
        """
        # Validate
        if len(text) > 3000:
            raise ValueError("LinkedIn posts are limited to 3000 characters")

        if media_type == "image" and len(media_urls) > 9:
            raise ValueError("LinkedIn supports maximum 9 images per post")

        if media_type == "video" and len(media_urls) > 1:
            raise ValueError("LinkedIn supports only 1 video per post")

        # Get user URN
        user_info = self.get_user_info()
        author_urn = f"urn:li:person:{user_info['id']}"

        # Upload media
        media_assets = []

        if media_type == "image":
            for image_url in media_urls:
                asset_urn = self.upload_image(image_url)
                media_assets.append({
                    "status": "READY",
                    "description": {
                        "text": ""
                    },
                    "media": asset_urn,
                    "title": {
                        "text": ""
                    }
                })
        elif media_type == "video":
            video_urn = self.upload_video(media_urls[0], "Video Post", text)
            media_assets.append({
                "status": "READY",
                "description": {
                    "text": text
                },
                "media": video_urn,
                "title": {
                    "text": "Video Post"
                }
            })

        # Prepare post payload
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text
                    },
                    "shareMediaCategory": "IMAGE" if media_type == "image" else "VIDEO",
                    "media": media_assets
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": visibility
            }
        }

        # Create post
        url = f"{self.api_base_url}/ugcPosts"

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()

            post_data = response.json()
            post_id = post_data.get("id")

            # Construct post URL
            post_url = f"https://www.linkedin.com/feed/update/{post_id}/"

            return {
                "success": True,
                "post_id": post_id,
                "url": post_url,
                "media_count": len(media_urls),
                "created_at": datetime.now().isoformat()
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create LinkedIn post with media: {str(e)}")

    def create_article(self, title: str, content: str,
                      thumbnail_url: Optional[str] = None) -> Dict:
        """
        Create a LinkedIn article

        Args:
            title: Article title
            content: Article content (HTML supported)
            thumbnail_url: Optional thumbnail image URL

        Returns:
            Response containing article ID and URL
        """
        # Get user URN
        user_info = self.get_user_info()
        author_urn = f"urn:li:person:{user_info['id']}"

        # Prepare article payload
        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": title
                    },
                    "shareMediaCategory": "ARTICLE",
                    "media": [
                        {
                            "status": "READY",
                            "description": {
                                "text": content[:256]  # Preview
                            },
                            "originalUrl": thumbnail_url or "https://example.com",
                            "title": {
                                "text": title
                            }
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        # Create article
        url = f"{self.api_base_url}/ugcPosts"

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()

            post_data = response.json()
            article_id = post_data.get("id")

            # Construct article URL
            article_url = f"https://www.linkedin.com/feed/update/{article_id}/"

            return {
                "success": True,
                "article_id": article_id,
                "url": article_url,
                "created_at": datetime.now().isoformat()
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create LinkedIn article: {str(e)}")

    def get_post_analytics(self, post_id: str) -> Dict:
        """
        Get analytics for a specific post

        Args:
            post_id: LinkedIn post ID

        Returns:
            Analytics data (views, likes, comments, shares)
        """
        url = f"{self.api_base_url}/socialActions/{post_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            analytics = response.json()

            return {
                "post_id": post_id,
                "likes": analytics.get("likesSummary", {}).get("totalLikes", 0),
                "comments": analytics.get("commentsSummary", {}).get("totalComments", 0),
                "shares": analytics.get("sharesSummary", {}).get("totalShares", 0),
                "impressions": analytics.get("impressionCount", 0),
                "clicks": analytics.get("clickCount", 0)
            }
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch post analytics: {str(e)}")

    def format_post_content(self, content: str, hashtags: Optional[List[str]] = None) -> str:
        """
        Format content for LinkedIn with character limit and hashtags

        Args:
            content: Raw content text
            hashtags: Optional list of hashtags to append

        Returns:
            Formatted content string
        """
        # LinkedIn character limit
        max_length = 3000

        # Add hashtags
        if hashtags:
            hashtag_string = " " + " ".join([f"#{tag.strip('#')}" for tag in hashtags])

            # Ensure total length doesn't exceed limit
            available_space = max_length - len(hashtag_string) - 10  # Buffer

            if len(content) > available_space:
                content = content[:available_space - 3] + "..."

            content = content + hashtag_string

        # Final length check
        if len(content) > max_length:
            content = content[:max_length - 3] + "..."

        return content


# Convenience function for FastAPI/n8n integration
def publish_to_linkedin(content: str, media_urls: Optional[List[str]] = None,
                       media_type: str = "image", hashtags: Optional[List[str]] = None,
                       access_token: Optional[str] = None) -> Dict:
    """
    Publish content to LinkedIn

    Args:
        content: Post text content
        media_urls: Optional list of media URLs
        media_type: 'image' or 'video'
        hashtags: Optional list of hashtags
        access_token: LinkedIn OAuth token

    Returns:
        Publishing result with post URL
    """
    publisher = LinkedInPublisher(access_token=access_token)

    # Format content
    formatted_content = publisher.format_post_content(content, hashtags)

    # Publish
    if media_urls:
        result = publisher.create_post_with_media(
            text=formatted_content,
            media_urls=media_urls,
            media_type=media_type
        )
    else:
        result = publisher.create_text_post(text=formatted_content)

    return result


if __name__ == "__main__":
    # Example usage
    publisher = LinkedInPublisher()

    # Test text post
    # result = publisher.create_text_post(
    #     text="Excited to share our latest insights on B2B marketing automation! #Marketing #AI",
    #     visibility="PUBLIC"
    # )
    # print(json.dumps(result, indent=2))

    print("LinkedIn publisher initialized successfully")
