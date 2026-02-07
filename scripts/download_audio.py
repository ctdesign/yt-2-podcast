"""Download audio from YouTube playlist and convert to MP3."""

import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import yt_dlp

from scripts.utils import (
    ensure_downloads_dir,
    get_audio_duration,
    get_file_size,
    get_processed_video_ids,
    load_state,
    save_state
)


# Path to cookies file (set up by the workflow from YT_COOKIES_B64 secret)
COOKIES_FILE = '/tmp/yt_cookies.txt'


def get_base_ydl_opts() -> dict:
    """
    Build shared yt-dlp options including cookies if available.

    Returns:
        Dictionary of yt-dlp options
    """
    opts = {}

    # Use cookies file if it exists (exported from browser, stored as secret)
    if Path(COOKIES_FILE).exists():
        print(f"Using YouTube cookies from {COOKIES_FILE}")
        opts['cookiefile'] = COOKIES_FILE
    else:
        print("No cookies file found - YouTube may block downloads from CI")

    return opts


def get_playlist_url() -> str:
    """
    Get playlist URL from environment variable.

    Returns:
        YouTube playlist URL

    Raises:
        ValueError: If PLAYLIST_URL environment variable is not set
    """
    playlist_url = os.environ.get('PLAYLIST_URL')
    if not playlist_url:
        raise ValueError(
            "PLAYLIST_URL environment variable is required. "
            "Set it to your YouTube playlist URL."
        )
    return playlist_url


def fetch_playlist_videos(playlist_url: str) -> List[Dict]:
    """
    Fetch video metadata from YouTube playlist.

    Args:
        playlist_url: YouTube playlist URL

    Returns:
        List of video metadata dictionaries
    """
    ydl_opts = {
        **get_base_ydl_opts(),
        'extract_flat': True,  # Don't download, just get metadata
        'quiet': False,
        'no_warnings': False,
        'extractor_retries': 3,
        'ignoreerrors': True,  # Don't abort if individual entries fail
    }

    print(f"Fetching playlist metadata from: {playlist_url}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        playlist_info = ydl.extract_info(playlist_url, download=False)

        if not playlist_info:
            raise RuntimeError(
                f"yt-dlp returned no data for: {playlist_url}\n"
                "Check that the PLAYLIST_URL secret is set to a valid YouTube playlist URL.\n"
                "Example format: https://www.youtube.com/playlist?list=PLxxxxxxxx"
            )

        # Handle single video URLs (not a playlist)
        if playlist_info.get('_type') != 'playlist' and 'entries' not in playlist_info:
            print(f"Warning: URL appears to be a single video, not a playlist")
            print(f"  Type: {playlist_info.get('_type', 'unknown')}")
            print(f"  Title: {playlist_info.get('title', 'unknown')}")
            if playlist_info.get('id'):
                return [{
                    'video_id': playlist_info['id'],
                    'title': playlist_info.get('title', 'Unknown Title'),
                    'url': f"https://www.youtube.com/watch?v={playlist_info['id']}",
                    'upload_date': playlist_info.get('upload_date'),
                }]
            raise RuntimeError(
                f"URL is not a playlist and has no video ID: {playlist_url}\n"
                "Use a playlist URL like: https://www.youtube.com/playlist?list=PLxxxxxxxx"
            )

        entries = list(playlist_info.get('entries', []))
        print(f"Playlist title: {playlist_info.get('title', 'unknown')}")
        print(f"Raw entries count: {len(entries)}")

        videos = []
        for entry in entries:
            if entry:  # Some entries might be None if video is unavailable
                videos.append({
                    'video_id': entry['id'],
                    'title': entry.get('title', 'Unknown Title'),
                    'url': f"https://www.youtube.com/watch?v={entry['id']}",
                    'upload_date': entry.get('upload_date'),  # Format: YYYYMMDD
                })

        if not videos:
            raise RuntimeError(
                f"Playlist was fetched but contained no accessible videos.\n"
                f"Playlist title: {playlist_info.get('title', 'unknown')}\n"
                "All entries may be private, deleted, or region-blocked."
            )

        print(f"Found {len(videos)} videos in playlist")
        return videos


def download_video_audio(video_url: str, video_id: str, downloads_dir: Path) -> bool:
    """
    Download audio from a YouTube video and convert to MP3.

    Args:
        video_url: YouTube video URL
        video_id: YouTube video ID
        downloads_dir: Directory to save downloaded files

    Returns:
        True if download successful, False otherwise
    """
    ydl_opts = {
        **get_base_ydl_opts(),
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'outtmpl': str(downloads_dir / f'{video_id}.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'retries': 3,
        'extractor_retries': 3,
    }

    try:
        print(f"Downloading audio for video ID: {video_id}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        print(f"Successfully downloaded: {video_id}")
        return True

    except yt_dlp.utils.DownloadError as e:
        print(f"Download error for {video_id}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error downloading {video_id}: {e}")
        return False


def parse_upload_date(upload_date: str) -> datetime:
    """
    Parse YouTube upload_date format (YYYYMMDD) to datetime.

    Args:
        upload_date: Date string in YYYYMMDD format

    Returns:
        datetime object
    """
    if not upload_date or len(upload_date) != 8:
        return datetime.utcnow()

    try:
        return datetime.strptime(upload_date, '%Y%m%d')
    except ValueError:
        return datetime.utcnow()


def get_full_video_metadata(video_url: str) -> Dict:
    """
    Get full metadata for a video including description.

    Args:
        video_url: YouTube video URL

    Returns:
        Dictionary with full video metadata
    """
    ydl_opts = {
        **get_base_ydl_opts(),
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return {
                'title': info.get('title', 'Unknown Title'),
                'description': info.get('description', ''),
                'upload_date': info.get('upload_date'),
            }
    except Exception as e:
        print(f"Error getting metadata for {video_url}: {e}")
        return {
            'title': 'Unknown Title',
            'description': '',
            'upload_date': None,
        }


def process_new_videos() -> List[Dict]:
    """
    Download and process new videos from the playlist.

    Returns:
        List of newly processed video metadata dictionaries
    """
    # Get playlist URL
    playlist_url = get_playlist_url()

    # Get already processed video IDs
    processed_ids = get_processed_video_ids()
    print(f"Already processed {len(processed_ids)} videos")

    # Fetch playlist videos
    playlist_videos = fetch_playlist_videos(playlist_url)

    # Filter out already processed videos
    new_videos = [v for v in playlist_videos if v['video_id'] not in processed_ids]

    if not new_videos:
        print("No new videos to process")
        return []

    print(f"Found {len(new_videos)} new videos to process")

    # Ensure downloads directory exists
    downloads_dir = ensure_downloads_dir()

    # Process each new video
    newly_processed = []

    for idx, video in enumerate(new_videos, 1):
        video_id = video['video_id']
        video_url = video['url']

        print(f"\n[{idx}/{len(new_videos)}] Processing: {video['title']}")

        # Download audio
        success = download_video_audio(video_url, video_id, downloads_dir)

        if not success:
            print(f"Skipping {video_id} due to download failure")
            continue

        # Get full metadata
        full_metadata = get_full_video_metadata(video_url)

        # Get file path
        mp3_file = downloads_dir / f"{video_id}.mp3"

        if not mp3_file.exists():
            print(f"Warning: MP3 file not found at {mp3_file}")
            continue

        # Extract audio metadata
        duration = get_audio_duration(str(mp3_file))
        file_size = get_file_size(str(mp3_file))

        # Parse upload date
        pub_date = parse_upload_date(video.get('upload_date'))

        # Create video info for state
        video_info = {
            'video_id': video_id,
            'title': full_metadata['title'],
            'description': full_metadata['description'],
            'processed_date': datetime.utcnow().isoformat() + 'Z',
            'pub_date': pub_date.isoformat() + 'Z',
            'duration': duration,
            'file_size': file_size,
            'file_path': str(mp3_file),
            # These will be filled in by upload_to_release.py
            'release_tag': None,
            'audio_url': None,
        }

        newly_processed.append(video_info)

        print(f"Processed: {video_info['title']} ({duration}, {file_size} bytes)")

        # Add delay to avoid rate limiting (randomized to look less bot-like)
        if idx < len(new_videos):
            time.sleep(random.uniform(5, 10))

    return newly_processed


def main():
    """Main entry point for download_audio script."""
    print("=" * 60)
    print("YouTube to Podcast - Audio Download")
    print("=" * 60)

    try:
        # Process new videos
        newly_processed = process_new_videos()

        if newly_processed:
            # Load existing state
            state = load_state()
            existing_videos = state.get('videos', [])

            # Merge with newly processed videos
            all_videos = existing_videos + newly_processed

            # Save updated state
            save_state(all_videos)

            print(f"\n✓ Successfully processed {len(newly_processed)} new videos")
            print(f"✓ Total videos in state: {len(all_videos)}")
        else:
            print("\n✓ No new videos to process")

        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
