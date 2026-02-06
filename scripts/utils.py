"""Utility functions for YouTube to Podcast converter."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from mutagen.mp3 import MP3


def get_audio_duration(file_path: str) -> str:
    """
    Get audio duration in HH:MM:SS format.

    Args:
        file_path: Path to the audio file

    Returns:
        Duration formatted as HH:MM:SS
    """
    try:
        audio = MP3(file_path)
        duration_seconds = int(audio.info.length)

        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        seconds = duration_seconds % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except Exception as e:
        print(f"Error getting duration for {file_path}: {e}")
        return "00:00:00"


def format_rfc2822_date(dt: datetime) -> str:
    """
    Format datetime to RFC 2822 format for RSS feeds.

    Args:
        dt: datetime object to format

    Returns:
        RFC 2822 formatted date string (e.g., "Wed, 05 Feb 2026 10:00:00 +0000")
    """
    from email.utils import formatdate

    # Convert to timestamp and format
    timestamp = dt.timestamp()
    return formatdate(timestamp, usegmt=True)


def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in bytes
    """
    return os.path.getsize(file_path)


def get_state_file_path() -> Path:
    """Get the path to the state file."""
    return Path(__file__).parent.parent / "state" / "processed_videos.json"


def load_state() -> Dict:
    """
    Load state from processed_videos.json.

    Returns:
        Dictionary containing last_updated and videos list
    """
    state_file = get_state_file_path()

    if not state_file.exists():
        return {
            "last_updated": None,
            "videos": []
        }

    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON in {state_file}, returning empty state")
        return {
            "last_updated": None,
            "videos": []
        }


def save_state(videos: List[Dict]) -> None:
    """
    Save state to processed_videos.json.

    Args:
        videos: List of video dictionaries with metadata
    """
    state_file = get_state_file_path()

    # Ensure directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)

    state = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "videos": videos
    }

    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    print(f"State saved with {len(videos)} videos")


def get_processed_video_ids() -> set:
    """
    Get set of already processed video IDs.

    Returns:
        Set of video IDs
    """
    state = load_state()
    return {video['video_id'] for video in state['videos']}


def add_video_to_state(video_info: Dict) -> None:
    """
    Add a single video to the state file.

    Args:
        video_info: Dictionary with video metadata
    """
    state = load_state()
    state['videos'].append(video_info)
    save_state(state['videos'])


def ensure_downloads_dir() -> Path:
    """
    Ensure downloads directory exists and return its path.

    Returns:
        Path to downloads directory
    """
    downloads_dir = Path(__file__).parent.parent / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    return downloads_dir
