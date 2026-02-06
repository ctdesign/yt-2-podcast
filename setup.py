#!/usr/bin/env python3
"""Setup script for YouTube to Podcast converter."""

import json
from pathlib import Path


def create_directories():
    """Create necessary project directories."""
    directories = [
        '.github/workflows',
        'scripts',
        'config',
        'state',
        'feed',
        'downloads'
    ]

    base_dir = Path(__file__).parent

    print("Creating project directories...")
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}/")


def initialize_state_file():
    """Create initial empty state file."""
    state_file = Path(__file__).parent / "state" / "processed_videos.json"

    if state_file.exists():
        print("\n✓ State file already exists, skipping initialization")
        return

    initial_state = {
        "last_updated": None,
        "videos": []
    }

    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(initial_state, f, indent=2)

    print("\n✓ Initialized state/processed_videos.json")


def check_config_file():
    """Check if podcast config file exists."""
    config_file = Path(__file__).parent / "config" / "podcast_config.yaml"

    if config_file.exists():
        print("\n✓ Podcast config file exists at config/podcast_config.yaml")
        print("  ⚠️  Please edit it with your podcast details before pushing to GitHub")
    else:
        print("\n✗ Podcast config file not found!")
        print("  Please create config/podcast_config.yaml")


def display_next_steps():
    """Display setup instructions for the user."""
    print("\n" + "=" * 70)
    print("Setup Complete! Next Steps:")
    print("=" * 70)

    print("""
1. Edit Podcast Configuration:
   → Open config/podcast_config.yaml
   → Update with your podcast details (title, author, image URL, etc.)

2. Prepare Cover Art:
   → Create a 1400x1400px (minimum) image for your podcast
   → Upload to a public location (GitHub, Imgur, etc.)
   → Add the URL to podcast_config.yaml

3. Create GitHub Repository:
   → Go to https://github.com/new
   → Repository name: yt-2-podcast
   → Visibility: Public (required for GitHub Pages)
   → DO NOT initialize with README (this directory already has files)

4. Push Code to GitHub:
   git init
   git add .
   git commit -m "Initial YouTube to Podcast setup"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/yt-2-podcast.git
   git push -u origin main

5. Add GitHub Secret:
   → Go to: Settings → Secrets and variables → Actions
   → Click "New repository secret"
   → Name: PLAYLIST_URL
   → Value: https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID
   → Click "Add secret"

6. Enable GitHub Pages:
   → Go to: Settings → Pages
   → Source: Deploy from a branch
   → Branch: main
   → Folder: /feed
   → Click "Save"

7. Run First Workflow:
   → Go to: Actions tab
   → Click "Update Podcast Feed"
   → Click "Run workflow" button
   → Wait for completion (may take 10-20 minutes)

8. Get Your Podcast Feed URL:
   → Your feed will be at:
     https://YOUR_USERNAME.github.io/yt-2-podcast/podcast.xml
   → Add this URL to your favorite podcast app!

Need Help?
→ Check README.md for detailed instructions
→ See GitHub Actions logs if workflow fails
""")

    print("=" * 70)


def main():
    """Main setup function."""
    print("=" * 70)
    print("YouTube to Podcast - Project Setup")
    print("=" * 70)

    # Create directories
    create_directories()

    # Initialize state file
    initialize_state_file()

    # Check config file
    check_config_file()

    # Display next steps
    display_next_steps()


if __name__ == '__main__':
    main()
