"""
Video Download Tool
Download videos from URLs and store locally
"""

import requests
from typing import Dict, List, Optional, Any
import os
from pathlib import Path
from urllib.parse import urlparse, unquote
import mimetypes
import hashlib
from datetime import datetime
import structlog
from config import settings

logger = structlog.get_logger()


class VideoDownloadTool:
    """
    Video download and local storage manager

    Features:
    - Download videos from URLs
    - Local file storage
    - Metadata extraction
    - File validation
    - Duplicate detection
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize video download tool

        Args:
            storage_dir: Directory for storing downloaded videos
        """
        self.storage_dir = storage_dir or os.path.join(
            os.getcwd(),
            "data",
            "videos"
        )

        # Create storage directory if it doesn't exist
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)

        # Supported video formats
        self.supported_formats = {
            '.mp4', '.mov', '.avi', '.mkv', '.webm',
            '.flv', '.wmv', '.m4v', '.mpeg', '.mpg'
        }

        logger.info("video_download_tool_initialized", storage_dir=self.storage_dir)

    def download_video(
        self,
        url: str,
        filename: Optional[str] = None,
        overwrite: bool = False,
        timeout: int = 300,
        chunk_size: int = 8192
    ) -> Dict[str, Any]:
        """
        Download video from URL to local storage

        Args:
            url: Video URL
            filename: Optional custom filename (auto-generated if not provided)
            overwrite: Overwrite existing file
            timeout: Download timeout in seconds
            chunk_size: Download chunk size in bytes

        Returns:
            Dict with download result and metadata
        """
        try:
            logger.info("downloading_video", url=url)

            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme in ['http', 'https']:
                return {
                    "success": False,
                    "error": f"Invalid URL scheme: {parsed_url.scheme}",
                    "url": url
                }

            # Get video metadata from URL
            head_response = requests.head(url, timeout=10, allow_redirects=True)
            head_response.raise_for_status()

            content_type = head_response.headers.get('Content-Type', '')
            content_length = head_response.headers.get('Content-Length')

            # Validate content type
            if not self._is_video_content_type(content_type):
                logger.warning(
                    "potentially_non_video_content",
                    content_type=content_type,
                    url=url
                )

            # Generate filename if not provided
            if not filename:
                filename = self._generate_filename(url, content_type)

            # Ensure proper extension
            file_ext = Path(filename).suffix.lower()
            if file_ext not in self.supported_formats:
                # Try to detect from content type
                detected_ext = mimetypes.guess_extension(content_type)
                if detected_ext and detected_ext in self.supported_formats:
                    filename = f"{Path(filename).stem}{detected_ext}"
                else:
                    filename = f"{filename}.mp4"  # Default to mp4

            file_path = os.path.join(self.storage_dir, filename)

            # Check if file already exists
            if os.path.exists(file_path) and not overwrite:
                logger.info("file_already_exists", file_path=file_path)
                return {
                    "success": True,
                    "status": "already_exists",
                    "file_path": file_path,
                    "filename": filename,
                    "url": url,
                    "file_size": os.path.getsize(file_path)
                }

            # Download the video
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()

            total_size = int(content_length) if content_length else 0
            downloaded_size = 0

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # Log progress for large files
                        if total_size > 0 and downloaded_size % (1024 * 1024) == 0:
                            progress = (downloaded_size / total_size) * 100
                            logger.debug(
                                "download_progress",
                                filename=filename,
                                progress=f"{progress:.1f}%"
                            )

            # Get final file stats
            file_size = os.path.getsize(file_path)
            file_hash = self._calculate_file_hash(file_path)

            logger.info(
                "video_downloaded_successfully",
                filename=filename,
                file_size=file_size,
                file_path=file_path
            )

            return {
                "success": True,
                "status": "downloaded",
                "file_path": file_path,
                "filename": filename,
                "url": url,
                "file_size": file_size,
                "file_hash": file_hash,
                "content_type": content_type,
                "downloaded_at": datetime.utcnow().isoformat()
            }

        except requests.exceptions.Timeout:
            logger.error("download_timeout", url=url, timeout=timeout)
            return {
                "success": False,
                "error": f"Download timeout after {timeout} seconds",
                "url": url
            }

        except requests.exceptions.RequestException as e:
            logger.error("download_request_error", error=str(e), url=url)
            return {
                "success": False,
                "error": str(e),
                "url": url
            }

        except Exception as e:
            logger.error("download_error", error=str(e), url=url)
            return {
                "success": False,
                "error": str(e),
                "url": url
            }

    def download_multiple(
        self,
        urls: List[str],
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        Download multiple videos

        Args:
            urls: List of video URLs
            overwrite: Overwrite existing files

        Returns:
            Dict with results for all downloads
        """
        results = []
        successful = 0
        failed = 0

        for url in urls:
            result = self.download_video(url=url, overwrite=overwrite)
            results.append(result)

            if result.get("success"):
                successful += 1
            else:
                failed += 1

        return {
            "success": failed == 0,
            "total": len(urls),
            "successful": successful,
            "failed": failed,
            "results": results
        }

    def get_video_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata for a local video file

        Args:
            file_path: Path to video file

        Returns:
            Video metadata
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": "File not found"
                }

            file_size = os.path.getsize(file_path)
            file_hash = self._calculate_file_hash(file_path)
            file_ext = Path(file_path).suffix.lower()

            return {
                "success": True,
                "file_path": file_path,
                "filename": os.path.basename(file_path),
                "file_size": file_size,
                "file_hash": file_hash,
                "file_extension": file_ext,
                "created_at": datetime.fromtimestamp(
                    os.path.getctime(file_path)
                ).isoformat(),
                "modified_at": datetime.fromtimestamp(
                    os.path.getmtime(file_path)
                ).isoformat()
            }

        except Exception as e:
            logger.error("get_video_info_error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def list_videos(self) -> List[Dict[str, Any]]:
        """
        List all downloaded videos

        Returns:
            List of video metadata
        """
        videos = []

        try:
            for file_name in os.listdir(self.storage_dir):
                file_path = os.path.join(self.storage_dir, file_name)

                if os.path.isfile(file_path):
                    file_ext = Path(file_path).suffix.lower()

                    if file_ext in self.supported_formats:
                        video_info = self.get_video_info(file_path)
                        if video_info.get("success"):
                            videos.append(video_info)

            return videos

        except Exception as e:
            logger.error("list_videos_error", error=str(e))
            return []

    def delete_video(self, filename: str) -> Dict[str, Any]:
        """
        Delete a downloaded video

        Args:
            filename: Video filename

        Returns:
            Deletion result
        """
        try:
            file_path = os.path.join(self.storage_dir, filename)

            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": "File not found",
                    "filename": filename
                }

            os.remove(file_path)

            logger.info("video_deleted", filename=filename)

            return {
                "success": True,
                "filename": filename,
                "message": "Video deleted successfully"
            }

        except Exception as e:
            logger.error("delete_video_error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }

    def _generate_filename(self, url: str, content_type: str) -> str:
        """
        Generate filename from URL and content type

        Args:
            url: Video URL
            content_type: Content MIME type

        Returns:
            Generated filename
        """
        # Try to extract filename from URL
        parsed_url = urlparse(url)
        url_path = unquote(parsed_url.path)
        url_filename = os.path.basename(url_path)

        if url_filename and '.' in url_filename:
            # Use URL filename if it looks valid
            return url_filename

        # Generate from URL hash and timestamp
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

        # Detect extension from content type
        extension = mimetypes.guess_extension(content_type) or '.mp4'

        return f"video_{timestamp}_{url_hash}{extension}"

    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate MD5 hash of file

        Args:
            file_path: Path to file

        Returns:
            MD5 hash string
        """
        hash_md5 = hashlib.md5()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    def _is_video_content_type(self, content_type: str) -> bool:
        """
        Check if content type is video

        Args:
            content_type: MIME content type

        Returns:
            True if video content type
        """
        video_types = [
            'video/',
            'application/octet-stream'  # Sometimes videos are served as binary
        ]

        return any(vtype in content_type.lower() for vtype in video_types)


def create_video_download_langchain_tool():
    """Create LangChain-compatible video download tool"""
    from langchain.tools import Tool

    downloader = VideoDownloadTool()

    def download_wrapper(url: str) -> str:
        """Download video from URL"""
        result = downloader.download_video(url=url)

        if result.get("success"):
            status = result.get("status")
            file_path = result.get("file_path", "")
            filename = result.get("filename", "")
            file_size = result.get("file_size", 0)
            file_size_mb = file_size / (1024 * 1024)

            if status == "already_exists":
                return f"""Video already exists locally.

Filename: {filename}
File Path: {file_path}
File Size: {file_size_mb:.2f} MB

No download needed."""
            else:
                return f"""Video downloaded successfully!

Filename: {filename}
File Path: {file_path}
File Size: {file_size_mb:.2f} MB
Downloaded At: {result.get('downloaded_at', 'N/A')}

Video is ready for use."""
        else:
            return f"Video download failed: {result.get('error', 'Unknown error')}"

    return Tool(
        name="Video_Downloader",
        func=download_wrapper,
        description="Download videos from URLs to local storage. "
                    "Input should be a valid video URL (http/https). "
                    "Supports common formats: MP4, MOV, AVI, WebM, etc. "
                    "Returns local file path for downloaded video."
    )


if __name__ == "__main__":
    # Test video download tool
    downloader = VideoDownloadTool()

    # Example: Download a sample video (using a placeholder URL)
    test_url = "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4"

    result = downloader.download_video(url=test_url)

    if result.get("success"):
        print(f"✓ Video downloaded: {result.get('filename')}")
        print(f"File Path: {result.get('file_path')}")
        print(f"File Size: {result.get('file_size')} bytes")
        print(f"Status: {result.get('status')}")
    else:
        print(f"✗ Download failed: {result.get('error')}")

    # List all videos
    videos = downloader.list_videos()
    print(f"\nTotal videos in storage: {len(videos)}")
