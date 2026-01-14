"""
FFmpeg Video Editing Tool
Wrapper for video post-processing and editing using FFmpeg
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import structlog
import json

logger = structlog.get_logger()


class FFmpegTool:
    """
    FFmpeg video editing wrapper

    Features:
    - Video concatenation
    - Add captions/subtitles
    - Add watermarks/logos
    - Add background music
    - Trim and cut
    - Format conversion
    - Resolution scaling
    - Aspect ratio adjustment
    """

    def __init__(self):
        """Initialize FFmpeg tool"""
        # Test FFmpeg availability
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True
            )
            logger.info("ffmpeg_available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("ffmpeg_not_found")

    def concatenate_videos(
        self,
        video_paths: List[Path],
        output_path: Path,
        transition: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Concatenate multiple videos

        Args:
            video_paths: List of video file paths
            output_path: Output file path
            transition: Transition type (fade, cross, etc.)

        Returns:
            Dict with result status
        """
        try:
            # Create concat file list
            concat_file = output_path.parent / "concat_list.txt"
            with open(concat_file, 'w') as f:
                for path in video_paths:
                    f.write(f"file '{path.absolute()}'\n")

            # Build FFmpeg command
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                str(output_path)
            ]

            logger.info("concatenating_videos", count=len(video_paths))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Clean up concat file
            concat_file.unlink(missing_ok=True)

            if result.returncode == 0:
                logger.info("videos_concatenated", output=str(output_path))
                return {
                    "success": True,
                    "output_path": str(output_path),
                    "video_count": len(video_paths)
                }
            else:
                logger.error("concatenation_failed", error=result.stderr)
                return {
                    "success": False,
                    "error": result.stderr
                }

        except Exception as e:
            logger.error("concatenation_error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def add_captions(
        self,
        video_path: Path,
        captions: List[Dict[str, Any]],
        output_path: Path,
        font_size: int = 24,
        font_color: str = "white",
        position: str = "bottom"
    ) -> Dict[str, Any]:
        """
        Add captions/subtitles to video

        Args:
            video_path: Input video path
            captions: List of caption dicts with 'text', 'start', 'end'
            output_path: Output file path
            font_size: Font size in pixels
            font_color: Font color
            position: Caption position (top, bottom, center)

        Returns:
            Dict with result status
        """
        try:
            # Create SRT subtitle file
            srt_path = output_path.parent / "captions.srt"
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, caption in enumerate(captions, 1):
                    f.write(f"{i}\n")
                    f.write(f"{self._format_timestamp(caption['start'])} --> {self._format_timestamp(caption['end'])}\n")
                    f.write(f"{caption['text']}\n\n")

            # Position mapping
            position_map = {
                "top": "Alignment=2",
                "center": "Alignment=5",
                "bottom": "Alignment=2"
            }

            # Build FFmpeg command
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-vf", f"subtitles={srt_path}:force_style='FontSize={font_size},PrimaryColour={self._color_to_hex(font_color)},{position_map.get(position, 'Alignment=2')}'",
                "-c:a", "copy",
                str(output_path)
            ]

            logger.info("adding_captions", caption_count=len(captions))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Clean up SRT file
            srt_path.unlink(missing_ok=True)

            if result.returncode == 0:
                logger.info("captions_added", output=str(output_path))
                return {
                    "success": True,
                    "output_path": str(output_path),
                    "caption_count": len(captions)
                }
            else:
                logger.error("caption_addition_failed", error=result.stderr)
                return {
                    "success": False,
                    "error": result.stderr
                }

        except Exception as e:
            logger.error("caption_error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def add_watermark(
        self,
        video_path: Path,
        watermark_path: Path,
        output_path: Path,
        position: str = "bottom_right",
        opacity: float = 0.7
    ) -> Dict[str, Any]:
        """
        Add watermark/logo to video

        Args:
            video_path: Input video path
            watermark_path: Watermark image path
            output_path: Output file path
            position: Watermark position (top_left, top_right, bottom_left, bottom_right, center)
            opacity: Watermark opacity (0.0-1.0)

        Returns:
            Dict with result status
        """
        try:
            # Position mapping
            position_map = {
                "top_left": "10:10",
                "top_right": "W-w-10:10",
                "bottom_left": "10:H-h-10",
                "bottom_right": "W-w-10:H-h-10",
                "center": "(W-w)/2:(H-h)/2"
            }

            overlay_position = position_map.get(position, "W-w-10:H-h-10")

            # Build FFmpeg command
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-i", str(watermark_path),
                "-filter_complex", f"[1]format=rgba,colorchannelmixer=aa={opacity}[logo];[0][logo]overlay={overlay_position}",
                "-codec:a", "copy",
                str(output_path)
            ]

            logger.info("adding_watermark", position=position)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                logger.info("watermark_added", output=str(output_path))
                return {
                    "success": True,
                    "output_path": str(output_path),
                    "position": position
                }
            else:
                logger.error("watermark_addition_failed", error=result.stderr)
                return {
                    "success": False,
                    "error": result.stderr
                }

        except Exception as e:
            logger.error("watermark_error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def add_background_music(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
        volume: float = 0.3,
        fade_in: float = 1.0,
        fade_out: float = 1.0
    ) -> Dict[str, Any]:
        """
        Add background music to video

        Args:
            video_path: Input video path
            audio_path: Background music path
            output_path: Output file path
            volume: Music volume (0.0-1.0)
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds

        Returns:
            Dict with result status
        """
        try:
            # Get video duration
            duration = self._get_video_duration(video_path)

            # Build FFmpeg command
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-filter_complex",
                f"[1:a]volume={volume},afade=t=in:st=0:d={fade_in},afade=t=out:st={duration-fade_out}:d={fade_out}[a1];[0:a][a1]amix=inputs=2:duration=first[aout]",
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-shortest",
                str(output_path)
            ]

            logger.info("adding_background_music", volume=volume)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                logger.info("music_added", output=str(output_path))
                return {
                    "success": True,
                    "output_path": str(output_path),
                    "volume": volume
                }
            else:
                logger.error("music_addition_failed", error=result.stderr)
                return {
                    "success": False,
                    "error": result.stderr
                }

        except Exception as e:
            logger.error("music_error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def trim_video(
        self,
        video_path: Path,
        output_path: Path,
        start_time: float,
        end_time: float
    ) -> Dict[str, Any]:
        """
        Trim video to specific time range

        Args:
            video_path: Input video path
            output_path: Output file path
            start_time: Start time in seconds
            end_time: End time in seconds

        Returns:
            Dict with result status
        """
        try:
            duration = end_time - start_time

            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-ss", str(start_time),
                "-t", str(duration),
                "-c", "copy",
                str(output_path)
            ]

            logger.info("trimming_video", start=start_time, end=end_time)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                logger.info("video_trimmed", output=str(output_path))
                return {
                    "success": True,
                    "output_path": str(output_path),
                    "duration": duration
                }
            else:
                logger.error("trim_failed", error=result.stderr)
                return {
                    "success": False,
                    "error": result.stderr
                }

        except Exception as e:
            logger.error("trim_error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def scale_video(
        self,
        video_path: Path,
        output_path: Path,
        width: int,
        height: int,
        maintain_aspect: bool = True
    ) -> Dict[str, Any]:
        """
        Scale video to specific resolution

        Args:
            video_path: Input video path
            output_path: Output file path
            width: Target width
            height: Target height
            maintain_aspect: Maintain aspect ratio

        Returns:
            Dict with result status
        """
        try:
            if maintain_aspect:
                scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease"
            else:
                scale_filter = f"scale={width}:{height}"

            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-vf", scale_filter,
                "-c:a", "copy",
                str(output_path)
            ]

            logger.info("scaling_video", width=width, height=height)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                logger.info("video_scaled", output=str(output_path))
                return {
                    "success": True,
                    "output_path": str(output_path),
                    "resolution": f"{width}x{height}"
                }
            else:
                logger.error("scale_failed", error=result.stderr)
                return {
                    "success": False,
                    "error": result.stderr
                }

        except Exception as e:
            logger.error("scale_error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration in seconds"""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                return 0.0

        except Exception:
            return 0.0

    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _color_to_hex(self, color: str) -> str:
        """Convert color name to hex for FFmpeg"""
        color_map = {
            "white": "&HFFFFFF&",
            "black": "&H000000&",
            "red": "&H0000FF&",
            "green": "&H00FF00&",
            "blue": "&HFF0000&",
            "yellow": "&H00FFFF&"
        }
        return color_map.get(color.lower(), "&HFFFFFF&")


def create_ffmpeg_langchain_tool():
    """Create LangChain-compatible FFmpeg tool"""
    from langchain.tools import Tool

    ffmpeg = FFmpegTool()

    def ffmpeg_wrapper(command: str) -> str:
        """Execute FFmpeg command for video editing"""
        # Parse command (simplified)
        if "concatenate" in command.lower():
            return "Use FFmpegTool.concatenate_videos() method with video paths list."
        elif "caption" in command.lower():
            return "Use FFmpegTool.add_captions() method with caption data."
        elif "watermark" in command.lower():
            return "Use FFmpegTool.add_watermark() method with watermark image."
        elif "music" in command.lower():
            return "Use FFmpegTool.add_background_music() method with audio file."
        elif "trim" in command.lower():
            return "Use FFmpegTool.trim_video() method with start/end times."
        else:
            return "FFmpeg tool available for: concatenation, captions, watermarks, music, trimming, scaling."

    return Tool(
        name="FFmpeg_Video_Editor",
        func=ffmpeg_wrapper,
        description="Edit videos using FFmpeg: concatenate clips, add captions/subtitles, add watermarks, add background music, trim, scale. "
                    "Input should be editing operation description."
    )


if __name__ == "__main__":
    # Test FFmpeg tool
    ffmpeg = FFmpegTool()

    # Example: Get video duration
    print("FFmpeg tool initialized successfully!")
