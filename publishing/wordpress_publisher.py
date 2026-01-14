"""
WordPress XML-RPC Publisher
Handles publishing blog posts and media content to WordPress via XML-RPC
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
import requests
from xmlrpc.client import ServerProxy, Binary
import mimetypes


class WordPressPublisher:
    """WordPress XML-RPC client for publishing content"""

    def __init__(self, url: Optional[str] = None, username: Optional[str] = None,
                 password: Optional[str] = None):
        """
        Initialize WordPress publisher

        Args:
            url: WordPress site URL
            username: WordPress username
            password: WordPress password or application password
        """
        self.url = url or os.getenv("WORDPRESS_URL")
        self.username = username or os.getenv("WORDPRESS_USERNAME")
        self.password = password or os.getenv("WORDPRESS_PASSWORD")

        # XML-RPC endpoint
        if not self.url.endswith("/xmlrpc.php"):
            self.xmlrpc_url = f"{self.url.rstrip('/')}/xmlrpc.php"
        else:
            self.xmlrpc_url = self.url

        self.client = ServerProxy(self.xmlrpc_url)
        self.blog_id = 0  # Default blog ID (for single-site installations)

    def test_connection(self) -> bool:
        """Test WordPress XML-RPC connection"""
        try:
            # Test with getUsersBlogs method
            blogs = self.client.wp.getUsersBlogs(self.username, self.password)
            return len(blogs) > 0
        except Exception as e:
            raise Exception(f"WordPress connection test failed: {str(e)}")

    def upload_media(self, media_url: str, filename: Optional[str] = None,
                    media_type: Optional[str] = None) -> Dict:
        """
        Upload media file to WordPress

        Args:
            media_url: Public URL of media to upload
            filename: Optional filename (auto-detected from URL if not provided)
            media_type: Optional MIME type (auto-detected if not provided)

        Returns:
            Media upload result with URL and ID
        """
        # Download media
        try:
            response = requests.get(media_url, timeout=60)
            response.raise_for_status()
            media_data = response.content
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to download media from URL: {str(e)}")

        # Determine filename
        if not filename:
            filename = media_url.split("/")[-1].split("?")[0]
            if not filename:
                filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Determine MIME type
        if not media_type:
            media_type, _ = mimetypes.guess_type(filename)
            if not media_type:
                media_type = "application/octet-stream"

        # Prepare upload data
        upload_data = {
            "name": filename,
            "type": media_type,
            "bits": Binary(media_data),
            "overwrite": False
        }

        # Upload to WordPress
        try:
            result = self.client.wp.uploadFile(
                self.blog_id,
                self.username,
                self.password,
                upload_data
            )

            return {
                "success": True,
                "id": result.get("id"),
                "url": result.get("url"),
                "file": result.get("file"),
                "type": result.get("type")
            }
        except Exception as e:
            raise Exception(f"Failed to upload media to WordPress: {str(e)}")

    def create_post(self, title: str, content: str, status: str = "publish",
                   categories: Optional[List[str]] = None,
                   tags: Optional[List[str]] = None,
                   featured_image_id: Optional[int] = None,
                   excerpt: Optional[str] = None) -> Dict:
        """
        Create a WordPress blog post

        Args:
            title: Post title
            content: Post content (HTML supported)
            status: Post status (publish, draft, private, pending)
            categories: List of category names
            tags: List of tag names
            featured_image_id: WordPress media ID for featured image
            excerpt: Post excerpt/summary

        Returns:
            Response containing post ID and URL
        """
        # Prepare post content
        post_content = {
            "post_type": "post",
            "post_status": status,
            "post_title": title,
            "post_content": content
        }

        # Add optional fields
        if excerpt:
            post_content["post_excerpt"] = excerpt

        if categories:
            # Get category IDs (create if not exists)
            category_ids = []
            for category_name in categories:
                cat_id = self._get_or_create_category(category_name)
                if cat_id:
                    category_ids.append(cat_id)

            if category_ids:
                post_content["terms_names"] = {"category": categories}

        if tags:
            post_content["terms_names"] = post_content.get("terms_names", {})
            post_content["terms_names"]["post_tag"] = tags

        if featured_image_id:
            post_content["post_thumbnail"] = featured_image_id

        # Create post
        try:
            post_id = self.client.wp.newPost(
                self.blog_id,
                self.username,
                self.password,
                post_content
            )

            # Get post permalink
            post_data = self.client.wp.getPost(
                self.blog_id,
                self.username,
                self.password,
                post_id
            )

            return {
                "success": True,
                "post_id": post_id,
                "url": post_data.get("link"),
                "status": status,
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            raise Exception(f"Failed to create WordPress post: {str(e)}")

    def create_post_with_media(self, title: str, content: str,
                              media_urls: Optional[List[str]] = None,
                              featured_image_url: Optional[str] = None,
                              status: str = "publish",
                              categories: Optional[List[str]] = None,
                              tags: Optional[List[str]] = None) -> Dict:
        """
        Create a WordPress post with media attachments

        Args:
            title: Post title
            content: Post content
            media_urls: List of media URLs to embed in post
            featured_image_url: URL of featured image
            status: Post status
            categories: Category names
            tags: Tag names

        Returns:
            Response containing post ID and URL
        """
        featured_image_id = None

        # Upload featured image
        if featured_image_url:
            try:
                upload_result = self.upload_media(featured_image_url)
                featured_image_id = upload_result["id"]

                # Add featured image to beginning of content
                content = f'<img src="{upload_result["url"]}" alt="{title}" class="wp-image-{featured_image_id} featured-image" />\n\n{content}'
            except Exception as e:
                print(f"Warning: Failed to upload featured image: {str(e)}")

        # Upload and embed additional media
        if media_urls:
            for media_url in media_urls:
                try:
                    upload_result = self.upload_media(media_url)
                    media_html = f'<img src="{upload_result["url"]}" alt="" class="wp-image-{upload_result["id"]}" />'

                    # Append to content
                    content += f"\n\n{media_html}"
                except Exception as e:
                    print(f"Warning: Failed to upload media {media_url}: {str(e)}")

        # Create post
        return self.create_post(
            title=title,
            content=content,
            status=status,
            categories=categories,
            tags=tags,
            featured_image_id=featured_image_id
        )

    def update_post(self, post_id: int, title: Optional[str] = None,
                   content: Optional[str] = None, status: Optional[str] = None) -> Dict:
        """
        Update an existing WordPress post

        Args:
            post_id: WordPress post ID
            title: New title (optional)
            content: New content (optional)
            status: New status (optional)

        Returns:
            Update result
        """
        post_content = {}

        if title:
            post_content["post_title"] = title
        if content:
            post_content["post_content"] = content
        if status:
            post_content["post_status"] = status

        try:
            result = self.client.wp.editPost(
                self.blog_id,
                self.username,
                self.password,
                post_id,
                post_content
            )

            return {
                "success": result,
                "post_id": post_id,
                "updated_at": datetime.now().isoformat()
            }
        except Exception as e:
            raise Exception(f"Failed to update WordPress post: {str(e)}")

    def delete_post(self, post_id: int) -> Dict:
        """
        Delete a WordPress post

        Args:
            post_id: WordPress post ID

        Returns:
            Deletion result
        """
        try:
            result = self.client.wp.deletePost(
                self.blog_id,
                self.username,
                self.password,
                post_id
            )

            return {
                "success": result,
                "post_id": post_id,
                "deleted_at": datetime.now().isoformat()
            }
        except Exception as e:
            raise Exception(f"Failed to delete WordPress post: {str(e)}")

    def get_post(self, post_id: int) -> Dict:
        """
        Get a specific WordPress post

        Args:
            post_id: WordPress post ID

        Returns:
            Post data
        """
        try:
            post = self.client.wp.getPost(
                self.blog_id,
                self.username,
                self.password,
                post_id
            )

            return {
                "post_id": post.get("post_id"),
                "title": post.get("post_title"),
                "content": post.get("post_content"),
                "status": post.get("post_status"),
                "url": post.get("link"),
                "date": post.get("post_date"),
                "modified": post.get("post_modified")
            }
        except Exception as e:
            raise Exception(f"Failed to get WordPress post: {str(e)}")

    def get_recent_posts(self, count: int = 10) -> List[Dict]:
        """
        Get recent WordPress posts

        Args:
            count: Number of posts to retrieve

        Returns:
            List of recent posts
        """
        try:
            posts = self.client.wp.getPosts(
                self.blog_id,
                self.username,
                self.password,
                {"number": count}
            )

            return [
                {
                    "post_id": post.get("post_id"),
                    "title": post.get("post_title"),
                    "url": post.get("link"),
                    "status": post.get("post_status"),
                    "date": post.get("post_date")
                }
                for post in posts
            ]
        except Exception as e:
            raise Exception(f"Failed to get recent posts: {str(e)}")

    def _get_or_create_category(self, category_name: str) -> Optional[int]:
        """
        Get category ID or create if it doesn't exist

        Args:
            category_name: Category name

        Returns:
            Category ID
        """
        try:
            # Get all categories
            categories = self.client.wp.getTerms(
                self.blog_id,
                self.username,
                self.password,
                "category"
            )

            # Find matching category
            for category in categories:
                if category.get("name") == category_name:
                    return category.get("term_id")

            # Create new category if not found
            new_category = self.client.wp.newTerm(
                self.blog_id,
                self.username,
                self.password,
                {
                    "name": category_name,
                    "taxonomy": "category"
                }
            )

            return new_category
        except Exception as e:
            print(f"Warning: Failed to get/create category: {str(e)}")
            return None

    def format_html_content(self, content: str, add_paragraphs: bool = True) -> str:
        """
        Format plain text content as HTML for WordPress

        Args:
            content: Plain text content
            add_paragraphs: Whether to wrap paragraphs in <p> tags

        Returns:
            HTML formatted content
        """
        if add_paragraphs:
            # Split by double newlines and wrap in <p> tags
            paragraphs = content.split("\n\n")
            formatted = "\n\n".join([f"<p>{p.strip()}</p>" for p in paragraphs if p.strip()])
            return formatted

        # Replace single newlines with <br>
        return content.replace("\n", "<br>\n")


# Convenience function for FastAPI/n8n integration
def publish_to_wordpress(title: str, content: str,
                        featured_image_url: Optional[str] = None,
                        media_urls: Optional[List[str]] = None,
                        categories: Optional[List[str]] = None,
                        tags: Optional[List[str]] = None,
                        status: str = "publish",
                        url: Optional[str] = None,
                        username: Optional[str] = None,
                        password: Optional[str] = None) -> Dict:
    """
    Publish content to WordPress

    Args:
        title: Post title
        content: Post content
        featured_image_url: Featured image URL
        media_urls: Additional media URLs
        categories: Category names
        tags: Tag names
        status: Post status
        url: WordPress URL
        username: WordPress username
        password: WordPress password

    Returns:
        Publishing result with post URL
    """
    publisher = WordPressPublisher(url=url, username=username, password=password)

    # Format content as HTML
    html_content = publisher.format_html_content(content)

    # Publish
    result = publisher.create_post_with_media(
        title=title,
        content=html_content,
        featured_image_url=featured_image_url,
        media_urls=media_urls,
        status=status,
        categories=categories,
        tags=tags
    )

    return result


if __name__ == "__main__":
    # Example usage
    publisher = WordPressPublisher()

    # Test connection
    # if publisher.test_connection():
    #     print("WordPress connection successful")
    # else:
    #     print("WordPress connection failed")

    print("WordPress publisher initialized successfully")
