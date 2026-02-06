"""Generate podcast RSS feed from processed videos."""

import sys
from datetime import datetime
from pathlib import Path

import yaml
from feedgen.feed import FeedGenerator

from scripts.utils import format_rfc2822_date, load_state


def load_podcast_config() -> dict:
    """
    Load podcast configuration from YAML file.

    Returns:
        Dictionary containing podcast metadata
    """
    config_file = Path(__file__).parent.parent / "config" / "podcast_config.yaml"

    if not config_file.exists():
        raise FileNotFoundError(
            f"Podcast config file not found: {config_file}\n"
            "Please create config/podcast_config.yaml with your podcast metadata."
        )

    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Validate required fields
    required_fields = ['title', 'description', 'author', 'language', 'link']
    missing_fields = [field for field in required_fields if field not in config]

    if missing_fields:
        raise ValueError(f"Missing required config fields: {', '.join(missing_fields)}")

    return config


def create_feed_generator(config: dict) -> FeedGenerator:
    """
    Create and configure a FeedGenerator with podcast settings.

    Args:
        config: Podcast configuration dictionary

    Returns:
        Configured FeedGenerator object
    """
    fg = FeedGenerator()

    # Load podcast extension
    fg.load_extension('podcast')

    # Set channel metadata
    fg.title(config['title'])
    fg.description(config['description'])
    fg.link(href=config['link'], rel='alternate')
    fg.language(config['language'])

    # Set podcast-specific metadata
    fg.podcast.itunes_author(config.get('author', 'Unknown'))
    fg.podcast.itunes_category(config.get('category', 'Technology'))

    # Add author email if provided
    if config.get('email'):
        fg.author({'name': config['author'], 'email': config['email']})

    # Add podcast image if provided
    if config.get('image_url'):
        fg.podcast.itunes_image(config['image_url'])
        fg.image(url=config['image_url'], title=config['title'], link=config['link'])

    # Set explicit flag (feedgen expects 'yes', 'no', or 'clean' as strings)
    explicit_value = config.get('explicit', False)
    if isinstance(explicit_value, bool):
        explicit_value = 'yes' if explicit_value else 'no'
    fg.podcast.itunes_explicit(explicit_value)

    # Set owner info if provided
    if config.get('email'):
        fg.podcast.itunes_owner(name=config['author'], email=config['email'])

    return fg


def add_episode_to_feed(fg: FeedGenerator, video: dict) -> None:
    """
    Add a single episode to the feed.

    Args:
        fg: FeedGenerator object
        video: Video metadata dictionary
    """
    # Skip videos without audio URLs (not uploaded yet)
    if not video.get('audio_url'):
        return

    fe = fg.add_entry()

    # Set basic episode info
    fe.id(video['video_id'])
    fe.title(video['title'])

    # Set description (use first 500 chars if too long)
    description = video.get('description', '')
    if len(description) > 500:
        description = description[:497] + '...'
    fe.description(description)

    # Set enclosure (audio file)
    fe.enclosure(
        url=video['audio_url'],
        length=str(video['file_size']),
        type='audio/mpeg'
    )

    # Set publication date
    try:
        pub_date = datetime.fromisoformat(video['pub_date'].replace('Z', '+00:00'))
        fe.pubDate(format_rfc2822_date(pub_date))
    except (ValueError, KeyError):
        # Fallback to processed date
        processed_date = datetime.fromisoformat(video['processed_date'].replace('Z', '+00:00'))
        fe.pubDate(format_rfc2822_date(processed_date))

    # Set iTunes-specific metadata
    fe.podcast.itunes_duration(video['duration'])
    fe.podcast.itunes_explicit('no')

    # Use video title as summary
    fe.podcast.itunes_summary(video['title'])


def generate_rss_feed() -> None:
    """
    Generate RSS feed from processed videos and save to feed/podcast.xml.
    """
    # Load podcast config
    print("Loading podcast configuration...")
    config = load_podcast_config()

    # Load state with processed videos
    print("Loading processed videos...")
    state = load_state()
    videos = state.get('videos', [])

    if not videos:
        print("Warning: No videos found in state")

    # Filter videos that have been uploaded
    uploaded_videos = [v for v in videos if v.get('audio_url')]
    print(f"Found {len(uploaded_videos)} uploaded videos")

    # Sort by publication date (newest first)
    uploaded_videos.sort(
        key=lambda v: v.get('pub_date', v.get('processed_date', '')),
        reverse=True
    )

    # Create feed generator
    print("Creating RSS feed...")
    fg = create_feed_generator(config)

    # Add episodes to feed
    for video in uploaded_videos:
        add_episode_to_feed(fg, video)

    # Ensure feed directory exists
    feed_dir = Path(__file__).parent.parent / "feed"
    feed_dir.mkdir(parents=True, exist_ok=True)

    # Write RSS feed
    feed_file = feed_dir / "podcast.xml"
    fg.rss_file(str(feed_file), pretty=True)

    print(f"✓ RSS feed generated: {feed_file}")
    print(f"✓ Total episodes in feed: {len(uploaded_videos)}")


def main():
    """Main entry point for generate_rss script."""
    print("=" * 60)
    print("YouTube to Podcast - RSS Feed Generation")
    print("=" * 60)

    try:
        generate_rss_feed()
        print("\n✓ RSS feed generation completed")
        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
