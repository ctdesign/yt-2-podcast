# YouTube to Podcast Converter

Automatically convert YouTube playlist videos to audio files and serve them as a podcast RSS feed - completely free using GitHub infrastructure.

## Features

- ✅ **Fully Automated** - Runs daily via GitHub Actions
- ✅ **Completely Free** - Uses GitHub's free tier (Actions, Releases, Pages)
- ✅ **Smart Tracking** - Avoids re-downloading already processed videos
- ✅ **Podcast Compatible** - Works with Apple Podcasts, Overcast, Pocket Casts, and more
- ✅ **High Quality** - MP3 128kbps audio files
- ✅ **No API Keys** - Uses yt-dlp (no YouTube API quota limits)

## How It Works

1. **GitHub Actions** runs daily at 6 AM UTC (configurable)
2. Downloads new videos from your YouTube playlist as audio using **yt-dlp**
3. Converts audio to **MP3 128kbps** with FFmpeg
4. Uploads audio files to **GitHub Releases** (free hosting, 2GB per release)
5. Generates podcast **RSS feed** with episode metadata
6. Serves feed via **GitHub Pages** at `https://yourusername.github.io/yt-2-podcast/podcast.xml`

## Setup Instructions

### Prerequisites

- GitHub account
- YouTube playlist URL (must be public)
- Podcast cover art image (1400x1400px minimum)

### 1. Clone or Download This Repository

```bash
git clone https://github.com/yourusername/yt-2-podcast.git
cd yt-2-podcast
```

### 2. Run Setup Script

```bash
python setup.py
```

This creates the necessary directories and initializes the state file.

### 3. Configure Your Podcast

Edit `config/podcast_config.yaml` with your podcast details:

```yaml
title: "My YouTube Podcast"
description: "Audio from my favorite YouTube playlist"
author: "Your Name"
email: "your.email@example.com"
link: "https://yourusername.github.io/yt-2-podcast/"
language: "en-us"
category: "Technology"
image_url: "https://example.com/cover-art.jpg"  # 1400x1400px min
explicit: false
```

**Important**: Upload your cover art to a public location (GitHub, Imgur, etc.) and add the URL to the config.

### 4. Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `yt-2-podcast`
3. Visibility: **Public** (required for GitHub Pages free tier)
4. **DO NOT** initialize with README (this directory already has files)

### 5. Push Code to GitHub

```bash
git init
git add .
git commit -m "Initial YouTube to Podcast setup"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/yt-2-podcast.git
git push -u origin main
```

### 6. Add GitHub Secret (Playlist URL)

1. Go to your repository on GitHub
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `PLAYLIST_URL`
5. Value: `https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID`
6. Click **Add secret**

### 7. Enable GitHub Pages

1. Go to: **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: **main**
4. Folder: **/feed**
5. Click **Save**

### 8. Run First Workflow

1. Go to the **Actions** tab
2. Click **Update Podcast Feed** workflow
3. Click **Run workflow** button (top right)
4. Select **main** branch
5. Click **Run workflow**

Wait for the workflow to complete (may take 10-20 minutes for the first run, depending on playlist size).

### 9. Get Your Podcast Feed URL

Your RSS feed will be available at:

```
https://YOUR_USERNAME.github.io/yt-2-podcast/podcast.xml
```

Add this URL to your favorite podcast app!

## Testing Your Feed

### Validate RSS Feed

Visit https://castfeedvalidator.com/ and paste your feed URL to check for any issues.

### Test in Podcast Apps

- **Apple Podcasts**: Podcasts → Library → Add a Show by URL
- **Overcast**: Add URL → Paste feed URL
- **Pocket Casts**: Settings → Import → RSS Feed

## Local Testing (Optional)

To test the scripts locally before pushing to GitHub:

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Make sure FFmpeg is installed:
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
- **Windows**: Download from https://ffmpeg.org/

### 2. Set Environment Variables

```bash
export PLAYLIST_URL="https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID"
```

### 3. Test Download Script

```bash
python -m scripts.download_audio
```

Check the `downloads/` directory for MP3 files.

### 4. Test RSS Generation

```bash
python -m scripts.generate_rss
```

Check `feed/podcast.xml` for the generated RSS feed.

**Note**: The upload script requires `GITHUB_TOKEN` and `GITHUB_REPOSITORY` environment variables, which are automatically provided in GitHub Actions.

## Customization

### Change Update Frequency

Edit `.github/workflows/update-podcast.yml`:

```yaml
schedule:
  - cron: '0 6 * * *'  # Daily at 6 AM UTC
```

Cron examples:
- Every 6 hours: `'0 */6 * * *'`
- Twice daily (6 AM and 6 PM): `'0 6,18 * * *'`
- Weekly on Monday: `'0 6 * * 1'`

### Change Audio Quality

Edit `scripts/download_audio.py`:

```python
'preferredquality': '128',  # Change to '192' or '256' for higher quality
```

**Note**: Higher quality = larger files, which may fill up GitHub Releases faster.

### Change Playlist

Update the `PLAYLIST_URL` secret in your repository settings with a new playlist URL.

To process all videos from scratch, delete `state/processed_videos.json` and commit the change.

## Maintenance

### Automatic Updates

The workflow runs automatically daily. No manual intervention needed!

### Monitor Workflow

Check the **Actions** tab for workflow run status:
- Green checkmark = Success
- Red X = Failed (check logs for details)

### GitHub Notifications

Enable notifications for workflow failures:
1. Go to: **Settings** → **Notifications**
2. Enable: **Actions** → **Failed workflows**

### Check Storage Usage

- **Releases**: Each release can hold ~2GB of audio files
- **Actions**: 2,000 minutes/month free tier (typically uses ~60 min/month)
- **Pages**: 100GB bandwidth/month

## Troubleshooting

### Workflow Fails

1. Check the **Actions** tab for error logs
2. Common issues:
   - Invalid `PLAYLIST_URL` secret
   - Playlist is private (must be public)
   - FFmpeg not installed (should be automatic in workflow)
   - Invalid `podcast_config.yaml` format

### No New Episodes

- Verify the playlist has new videos
- Check if videos are public
- Review workflow logs for download errors

### RSS Feed Not Updating

- Ensure GitHub Pages is enabled
- Wait a few minutes for Pages to deploy
- Clear your podcast app cache

### "File Not Found" Errors

Make sure all required files exist:
```bash
ls -la config/podcast_config.yaml
ls -la state/processed_videos.json
```

### Rate Limiting

If you have a very large playlist (100+ videos), the first run might take a while or hit rate limits. The script includes 2-second delays between downloads to mitigate this.

## Cost Breakdown

| Service | Free Tier | Estimated Usage | Cost |
|---------|-----------|-----------------|------|
| GitHub Actions | 2,000 min/month | ~60 min/month | $0 |
| GitHub Releases | 2GB per release | Varies by playlist | $0 |
| GitHub Pages | 100GB bandwidth/month | <1GB/month | $0 |

**Total**: $0/month 🎉

## Architecture

```
┌─────────────────────┐
│  YouTube Playlist   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  GitHub Actions     │
│  - Daily cron       │
│  - download_audio   │
│  - upload_release   │
│  - generate_rss     │
└──────────┬──────────┘
           │
           ├──────────────────────┐
           ▼                      ▼
┌─────────────────────┐  ┌──────────────────┐
│  GitHub Releases    │  │  GitHub Pages    │
│  (Audio Files)      │  │  (RSS Feed)      │
└─────────────────────┘  └──────────────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  Podcast Apps    │
                         └──────────────────┘
```

## Project Structure

```
yt-2-podcast/
├── .github/workflows/
│   └── update-podcast.yml      # GitHub Actions workflow
├── scripts/
│   ├── download_audio.py       # Download & convert videos to MP3
│   ├── upload_to_release.py    # Upload to GitHub Releases
│   ├── generate_rss.py         # Create podcast RSS feed
│   └── utils.py                # Shared utilities
├── config/
│   └── podcast_config.yaml     # Podcast metadata
├── state/
│   └── processed_videos.json   # Tracks processed videos
├── feed/
│   └── podcast.xml             # Generated RSS feed
├── requirements.txt            # Python dependencies
├── setup.py                    # Setup script
└── README.md                   # This file
```

## FAQ

### Can I use a private playlist?

No, the playlist must be public for yt-dlp to access it.

### Can I have multiple playlists?

Not out of the box, but you can create separate repositories for each playlist.

### What if a video is deleted from YouTube?

Already processed videos remain in your feed. The episode audio is stored in GitHub Releases, so it remains accessible even if the YouTube video is deleted.

### Can I customize the RSS feed format?

Yes, edit `scripts/generate_rss.py` to modify the feed structure or add additional metadata.

### How do I delete old episodes?

Edit `state/processed_videos.json` to remove entries, then commit and push. The next workflow run will regenerate the feed without those episodes.

### Can I use this commercially?

Check YouTube's Terms of Service regarding content downloading and redistribution. This tool is intended for personal use and archiving your own content or content you have permission to redistribute.

## Contributing

Feel free to open issues or submit pull requests for improvements!

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloading
- [feedgen](https://github.com/lkiesow/python-feedgen) - RSS feed generation
- [PyGithub](https://github.com/PyGithub/PyGithub) - GitHub API client
- [FFmpeg](https://ffmpeg.org/) - Audio conversion

---

**Enjoy your YouTube playlist as a podcast!** 🎧
