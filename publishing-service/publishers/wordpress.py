"""
WordPress Publisher
Handles posting content to WordPress sites via XML-RPC API
"""

import httpx
import structlog
from typing import Optional, List, Dict, Any
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods import posts, media

logger = structlog.get_logger()


class WordPressPublisher:
    """
    WordPress content publisher

    Uses WordPress XML-RPC API to create posts
    """

    async def publish(
        self,
        wp_url: str,
        wp_username: str,
        wp_password: str,
        title: str,
        content: str,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        featured_image_url: Optional[str] = None,
        status: str = "publish"
    ) -> Dict[str, Any]:
        """
        Publish content to WordPress

        Args:
            wp_url: WordPress site URL
            wp_username: WordPress username
            wp_password: WordPress password or app password
            title: Post title
            content: Post HTML content
            categories: Optional list of category names
            tags: Optional list of tag names
            featured_image_url: Optional featured image URL
            status: Post status (publish, draft, pending)

        Returns:
            Dictionary with post details and WordPress post ID
        """
        try:
            # Construct XML-RPC URL
            xmlrpc_url = f"{wp_url.rstrip('/')}/xmlrpc.php"

            # Create WordPress client
            client = Client(xmlrpc_url, wp_username, wp_password)

            # Create the post
            post = WordPressPost()
            post.title = title
            post.content = content
            post.post_status = status

            # Set categories if provided
            if categories:
                post.terms_names = {'category': categories}

            # Set tags if provided
            if tags:
                if not hasattr(post, 'terms_names') or not post.terms_names:
                    post.terms_names = {}
                post.terms_names['post_tag'] = tags

            # Handle featured image if provided
            thumbnail_id = None
            if featured_image_url:
                thumbnail_id = await self._upload_featured_image(
                    client, featured_image_url
                )
                if thumbnail_id:
                    post.thumbnail = thumbnail_id

            # Publish the post
            post_id = client.call(posts.NewPost(post))

            # Get the post URL
            post_url = f"{wp_url.rstrip('/')}/?p={post_id}"

            logger.info(
                "wordpress_post_created",
                post_id=post_id,
                status=status
            )

            return {
                "post_id": post_id,
                "platform": "wordpress",
                "url": post_url,
                "title": title,
                "status": status,
                "categories": categories or [],
                "tags": tags or [],
                "has_featured_image": thumbnail_id is not None
            }

        except Exception as e:
            logger.error("wordpress_publish_error", error=str(e))
            raise

    async def _upload_featured_image(
        self,
        client: Client,
        image_url: str
    ) -> Optional[int]:
        """
        Download and upload featured image to WordPress

        Args:
            client: WordPress XML-RPC client
            image_url: URL of the image to upload

        Returns:
            WordPress media ID or None if upload fails
        """
        try:
            # Download the image
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(image_url)
                if response.status_code != 200:
                    logger.warning("wordpress_image_download_failed", url=image_url)
                    return None

                image_data = response.content

            # Get filename from URL
            filename = image_url.split('/')[-1].split('?')[0]
            if not filename:
                filename = "featured-image.jpg"

            # Determine mime type
            content_type = response.headers.get('content-type', 'image/jpeg')

            # Upload to WordPress
            media_data = {
                'name': filename,
                'type': content_type,
                'bits': image_data,
                'overwrite': True
            }

            media_response = client.call(media.UploadFile(media_data))
            media_id = media_response.get('id')

            logger.info("wordpress_image_uploaded", media_id=media_id)
            return media_id

        except Exception as e:
            logger.warning("wordpress_image_upload_error", error=str(e))
            return None
