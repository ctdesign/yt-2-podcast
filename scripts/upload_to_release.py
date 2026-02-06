"""Upload audio files to GitHub Releases."""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from github import Github, GithubException

from scripts.utils import load_state, save_state


def get_github_token() -> str:
    """
    Get GitHub token from environment variable.

    Returns:
        GitHub token

    Raises:
        ValueError: If GITHUB_TOKEN environment variable is not set
    """
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise ValueError(
            "GITHUB_TOKEN environment variable is required. "
            "It should be automatically provided by GitHub Actions."
        )
    return token


def get_repo_info() -> tuple[str, str]:
    """
    Get repository owner and name from GITHUB_REPOSITORY environment variable.

    Returns:
        Tuple of (owner, repo_name)

    Raises:
        ValueError: If GITHUB_REPOSITORY is not set or invalid
    """
    repo_full_name = os.environ.get('GITHUB_REPOSITORY')
    if not repo_full_name:
        raise ValueError(
            "GITHUB_REPOSITORY environment variable is required. "
            "It should be automatically provided by GitHub Actions."
        )

    parts = repo_full_name.split('/')
    if len(parts) != 2:
        raise ValueError(f"Invalid GITHUB_REPOSITORY format: {repo_full_name}")

    return parts[0], parts[1]


def create_release(github_client: Github, owner: str, repo_name: str, tag_name: str) -> object:
    """
    Create a new GitHub release.

    Args:
        github_client: Authenticated GitHub client
        owner: Repository owner
        repo_name: Repository name
        tag_name: Git tag name for the release

    Returns:
        GitHub Release object
    """
    repo = github_client.get_repo(f"{owner}/{repo_name}")

    print(f"Creating release with tag: {tag_name}")

    release = repo.create_git_release(
        tag=tag_name,
        name=f"Podcast Episodes - {tag_name}",
        message=f"Audio files uploaded on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        draft=False,
        prerelease=False
    )

    print(f"✓ Release created: {release.html_url}")
    return release


def upload_file_to_release(release: object, file_path: Path) -> Optional[str]:
    """
    Upload a file to a GitHub release.

    Args:
        release: GitHub Release object
        file_path: Path to the file to upload

    Returns:
        Download URL of the uploaded asset, or None if upload failed
    """
    try:
        print(f"Uploading: {file_path.name}")

        asset = release.upload_asset(
            path=str(file_path),
            label=file_path.name,
            content_type='audio/mpeg'
        )

        print(f"✓ Uploaded: {asset.browser_download_url}")
        return asset.browser_download_url

    except GithubException as e:
        print(f"✗ GitHub error uploading {file_path.name}: {e}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error uploading {file_path.name}: {e}")
        return None


def get_or_create_release(
    github_client: Github,
    owner: str,
    repo_name: str,
    current_release: Optional[object] = None,
    current_size: int = 0
) -> tuple[object, int]:
    """
    Get existing release or create a new one if size limit is approaching.

    Args:
        github_client: Authenticated GitHub client
        owner: Repository owner
        repo_name: Repository name
        current_release: Current release object (if any)
        current_size: Cumulative size of assets in current release

    Returns:
        Tuple of (release object, cumulative size)
    """
    MAX_RELEASE_SIZE = 1.8 * 1024 * 1024 * 1024  # 1.8 GB (safety margin under 2GB limit)

    # Create new release if none exists or approaching size limit
    if current_release is None or current_size >= MAX_RELEASE_SIZE:
        tag_name = f"release-{datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')}"
        new_release = create_release(github_client, owner, repo_name, tag_name)
        return new_release, 0

    return current_release, current_size


def upload_new_videos_to_release() -> None:
    """
    Upload audio files for videos that don't have release URLs yet.
    """
    # Get GitHub credentials
    token = get_github_token()
    owner, repo_name = get_repo_info()

    # Initialize GitHub client
    github_client = Github(token)

    # Load state
    state = load_state()
    videos = state.get('videos', [])

    # Find videos without release URLs
    videos_to_upload = [v for v in videos if not v.get('audio_url')]

    if not videos_to_upload:
        print("No new videos to upload")
        return

    print(f"Found {len(videos_to_upload)} videos to upload")

    # Track current release and size
    current_release = None
    current_size = 0

    # Upload each video
    for idx, video in enumerate(videos_to_upload, 1):
        video_id = video['video_id']
        file_path = Path(video.get('file_path', f"downloads/{video_id}.mp3"))

        if not file_path.exists():
            print(f"✗ File not found: {file_path}")
            continue

        file_size = file_path.stat().st_size

        print(f"\n[{idx}/{len(videos_to_upload)}] Processing: {video['title']}")
        print(f"File size: {file_size / (1024*1024):.2f} MB")

        # Get or create release (checking size limits)
        current_release, current_size = get_or_create_release(
            github_client,
            owner,
            repo_name,
            current_release,
            current_size
        )

        # Upload file
        download_url = upload_file_to_release(current_release, file_path)

        if download_url:
            # Update video info with release details
            video['audio_url'] = download_url
            video['release_tag'] = current_release.tag_name

            # Update cumulative size
            current_size += file_size

            print(f"✓ Uploaded successfully (cumulative: {current_size / (1024*1024):.2f} MB)")
        else:
            print(f"✗ Upload failed for {video_id}")

    # Save updated state
    save_state(videos)
    print(f"\n✓ Upload complete. Updated state with release URLs.")


def main():
    """Main entry point for upload_to_release script."""
    print("=" * 60)
    print("YouTube to Podcast - GitHub Release Upload")
    print("=" * 60)

    try:
        upload_new_videos_to_release()
        print("\n✓ Upload process completed")
        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
