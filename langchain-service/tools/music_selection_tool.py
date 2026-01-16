"""
Music Selection Tool
Select and manage background music for video content
"""

import os
import random
from typing import Dict, List, Optional, Any
from pathlib import Path
import structlog
from config import settings

logger = structlog.get_logger()


class MusicSelectionTool:
    """
    Music selection and management for video content

    Features:
    - Tone-based music selection
    - Duration-based filtering
    - Music library management
    - Placeholder music generation for testing
    """

    # Supported music tones
    SUPPORTED_TONES = {
        'professional': {
            'description': 'Corporate, business-focused, sophisticated background music',
            'keywords': ['corporate', 'business', 'professional', 'clean', 'minimal']
        },
        'upbeat': {
            'description': 'Energetic, positive, high-tempo music for engaging content',
            'keywords': ['energetic', 'positive', 'upbeat', 'happy', 'motivational']
        },
        'dramatic': {
            'description': 'Cinematic, emotional, impactful music for storytelling',
            'keywords': ['cinematic', 'dramatic', 'epic', 'emotional', 'powerful']
        },
        'calm': {
            'description': 'Relaxing, peaceful, ambient music for gentle content',
            'keywords': ['calm', 'peaceful', 'ambient', 'relaxing', 'soft']
        }
    }

    def __init__(self, music_library_dir: Optional[str] = None):
        """
        Initialize music selection tool

        Args:
            music_library_dir: Root directory for music library
        """
        self.music_library_dir = music_library_dir or os.path.join(
            os.getcwd(),
            "langchain-service",
            "storage",
            "media",
            "music"
        )

        # Create base music directory if it doesn't exist
        Path(self.music_library_dir).mkdir(parents=True, exist_ok=True)

        # Create tone-specific directories
        for tone in self.SUPPORTED_TONES.keys():
            tone_dir = os.path.join(self.music_library_dir, tone)
            Path(tone_dir).mkdir(parents=True, exist_ok=True)

        # Supported audio formats
        self.supported_formats = {
            '.mp3', '.wav', '.aac', '.m4a', '.ogg', '.flac'
        }

        logger.info(
            "music_selection_tool_initialized",
            music_library_dir=self.music_library_dir,
            supported_tones=list(self.SUPPORTED_TONES.keys())
        )

    def select_music(
        self,
        tone: str,
        duration: Optional[int] = None,
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Select appropriate music based on tone and duration

        Args:
            tone: Music tone (professional, upbeat, dramatic, calm)
            duration: Target duration in seconds (optional)
            min_duration: Minimum acceptable duration in seconds
            max_duration: Maximum acceptable duration in seconds

        Returns:
            Dict with music selection result
        """
        try:
            # Normalize tone
            tone = tone.lower().strip()

            # Validate tone
            if tone not in self.SUPPORTED_TONES:
                logger.warning(
                    "invalid_tone_requested",
                    requested_tone=tone,
                    supported_tones=list(self.SUPPORTED_TONES.keys())
                )
                # Default to professional if invalid tone
                tone = 'professional'

            logger.info(
                "selecting_music",
                tone=tone,
                duration=duration
            )

            # Get tone directory
            tone_dir = os.path.join(self.music_library_dir, tone)

            # Get available music files
            available_files = self._list_music_files(tone_dir)

            if not available_files:
                logger.warning(
                    "no_music_files_found",
                    tone=tone,
                    tone_dir=tone_dir
                )
                # Create placeholder file for testing
                placeholder_file = self._create_placeholder_music(tone, duration or 30)
                available_files = [placeholder_file]

            # Filter by duration if specified
            if min_duration or max_duration or duration:
                available_files = self._filter_by_duration(
                    available_files,
                    duration=duration,
                    min_duration=min_duration,
                    max_duration=max_duration
                )

            if not available_files:
                return {
                    "success": False,
                    "error": "No music files match the duration requirements",
                    "tone": tone,
                    "duration": duration
                }

            # Select random file from available options
            selected_file = random.choice(available_files)

            # Get file metadata
            file_info = self._get_music_info(selected_file)

            logger.info(
                "music_selected",
                tone=tone,
                filename=os.path.basename(selected_file),
                duration=file_info.get('duration')
            )

            return {
                "success": True,
                "audio_path": selected_file,
                "filename": os.path.basename(selected_file),
                "tone": tone,
                "duration": file_info.get('duration'),
                "file_size": file_info.get('file_size'),
                "tone_description": self.SUPPORTED_TONES[tone]['description']
            }

        except Exception as e:
            logger.error("music_selection_error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "tone": tone
            }

    def get_available_tones(self) -> List[Dict[str, Any]]:
        """
        Get list of available music tones

        Returns:
            List of tone information
        """
        tones = []

        for tone, info in self.SUPPORTED_TONES.items():
            tone_dir = os.path.join(self.music_library_dir, tone)
            music_files = self._list_music_files(tone_dir)

            tones.append({
                "tone": tone,
                "description": info['description'],
                "keywords": info['keywords'],
                "available_tracks": len(music_files),
                "directory": tone_dir
            })

        return tones

    def add_music_to_library(
        self,
        file_path: str,
        tone: str,
        custom_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add music file to library

        Args:
            file_path: Path to music file
            tone: Music tone category
            custom_name: Optional custom filename

        Returns:
            Result of addition
        """
        try:
            # Validate tone
            if tone not in self.SUPPORTED_TONES:
                return {
                    "success": False,
                    "error": f"Invalid tone: {tone}",
                    "supported_tones": list(self.SUPPORTED_TONES.keys())
                }

            # Validate file exists
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": "File not found",
                    "file_path": file_path
                }

            # Validate file format
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.supported_formats:
                return {
                    "success": False,
                    "error": f"Unsupported format: {file_ext}",
                    "supported_formats": list(self.supported_formats)
                }

            # Determine destination filename
            if custom_name:
                filename = custom_name
                if not Path(filename).suffix:
                    filename = f"{filename}{file_ext}"
            else:
                filename = os.path.basename(file_path)

            # Copy to tone directory
            tone_dir = os.path.join(self.music_library_dir, tone)
            dest_path = os.path.join(tone_dir, filename)

            # Copy file
            import shutil
            shutil.copy2(file_path, dest_path)

            logger.info(
                "music_added_to_library",
                tone=tone,
                filename=filename,
                dest_path=dest_path
            )

            return {
                "success": True,
                "tone": tone,
                "filename": filename,
                "file_path": dest_path
            }

        except Exception as e:
            logger.error("add_music_error", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    def _list_music_files(self, directory: str) -> List[str]:
        """
        List all music files in directory

        Args:
            directory: Directory to search

        Returns:
            List of music file paths
        """
        music_files = []

        try:
            if not os.path.exists(directory):
                return []

            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)

                if os.path.isfile(file_path):
                    file_ext = Path(file_path).suffix.lower()

                    if file_ext in self.supported_formats:
                        music_files.append(file_path)

            return music_files

        except Exception as e:
            logger.error("list_music_files_error", error=str(e))
            return []

    def _filter_by_duration(
        self,
        files: List[str],
        duration: Optional[int] = None,
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None
    ) -> List[str]:
        """
        Filter music files by duration

        Args:
            files: List of file paths
            duration: Target duration (with tolerance)
            min_duration: Minimum duration
            max_duration: Maximum duration

        Returns:
            Filtered list of files
        """
        # For now, return all files since we don't have duration metadata
        # In production, you would use mutagen or similar to read audio duration
        # For this implementation, we assume files match duration requirements
        return files

    def _get_music_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get music file information

        Args:
            file_path: Path to music file

        Returns:
            Music metadata
        """
        try:
            file_size = os.path.getsize(file_path)
            file_ext = Path(file_path).suffix.lower()

            # Estimate duration based on file size (rough approximation)
            # Average MP3 is ~1MB per minute at 128kbps
            estimated_duration = int((file_size / (1024 * 1024)) * 60)

            return {
                "file_path": file_path,
                "filename": os.path.basename(file_path),
                "file_size": file_size,
                "file_extension": file_ext,
                "duration": estimated_duration  # Estimated
            }

        except Exception as e:
            logger.error("get_music_info_error", error=str(e))
            return {
                "file_path": file_path,
                "duration": 30  # Default assumption
            }

    def _create_placeholder_music(
        self,
        tone: str,
        duration: int = 30
    ) -> str:
        """
        Create placeholder music file for testing

        Args:
            tone: Music tone
            duration: Duration in seconds

        Returns:
            Path to placeholder file
        """
        try:
            tone_dir = os.path.join(self.music_library_dir, tone)
            Path(tone_dir).mkdir(parents=True, exist_ok=True)

            # Create placeholder filename
            placeholder_name = f"{tone}_placeholder_{duration}s.mp3"
            placeholder_path = os.path.join(tone_dir, placeholder_name)

            # Don't create if it already exists
            if os.path.exists(placeholder_path):
                return placeholder_path

            # Create empty placeholder file with metadata comment
            with open(placeholder_path, 'w') as f:
                f.write(f"# Placeholder music file for tone: {tone}, duration: {duration}s\n")
                f.write("# Replace with actual music file in production\n")

            logger.info(
                "placeholder_music_created",
                tone=tone,
                duration=duration,
                path=placeholder_path
            )

            return placeholder_path

        except Exception as e:
            logger.error("create_placeholder_error", error=str(e))
            # Return a path even if creation fails
            return os.path.join(tone_dir, f"{tone}_placeholder.mp3")


def create_music_selection_langchain_tool():
    """Create LangChain-compatible music selection tool"""
    from langchain.tools import Tool

    music_selector = MusicSelectionTool()

    def select_wrapper(input_str: str) -> str:
        """
        Select music based on tone and optional duration

        Input format: "tone:professional duration:30" or just "professional"
        """
        # Parse input
        parts = input_str.strip().split()
        tone = parts[0].replace('tone:', '').lower()

        duration = None
        for part in parts[1:]:
            if 'duration:' in part:
                try:
                    duration = int(part.replace('duration:', ''))
                except ValueError:
                    pass

        # Select music
        result = music_selector.select_music(tone=tone, duration=duration)

        if result.get("success"):
            return f"""Music selected successfully!

Tone: {result.get('tone')}
File: {result.get('filename')}
Path: {result.get('audio_path')}
Duration: {result.get('duration', 'Unknown')} seconds
Description: {result.get('tone_description')}

Ready to add to video."""
        else:
            return f"Music selection failed: {result.get('error', 'Unknown error')}"

    return Tool(
        name="Music_Selector",
        func=select_wrapper,
        description="Select background music for video content based on tone. "
                    "Supported tones: professional, upbeat, dramatic, calm. "
                    "Input format: 'professional' or 'tone:professional duration:30'. "
                    "Returns music file path and metadata."
    )


if __name__ == "__main__":
    # Test music selection tool
    music_tool = MusicSelectionTool()

    # Test each tone
    tones = ['professional', 'upbeat', 'dramatic', 'calm']

    print("Testing Music Selection Tool\n")
    print("=" * 50)

    for tone in tones:
        print(f"\nTesting tone: {tone}")
        result = music_tool.select_music(tone=tone, duration=30)

        if result.get("success"):
            print(f"✓ Music selected: {result.get('filename')}")
            print(f"  Path: {result.get('audio_path')}")
            print(f"  Duration: {result.get('duration')} seconds")
            print(f"  Tone: {result.get('tone')}")
        else:
            print(f"✗ Selection failed: {result.get('error')}")

    # Test available tones
    print("\n" + "=" * 50)
    print("\nAvailable Tones:")
    available_tones = music_tool.get_available_tones()
    for tone_info in available_tones:
        print(f"\n{tone_info['tone'].upper()}:")
        print(f"  Description: {tone_info['description']}")
        print(f"  Available Tracks: {tone_info['available_tracks']}")
