#!/bin/bash
#
# One-time setup: export YouTube cookies from your browser and store
# them as a GitHub Actions secret. Run this locally on your machine.
#
# Prerequisites:
#   - yt-dlp installed locally (pip install yt-dlp)
#   - gh CLI installed and authenticated (gh auth login)
#   - A browser with an active YouTube session (logged in or not)
#
# Usage:
#   ./scripts/setup_cookies.sh              # defaults to chrome
#   ./scripts/setup_cookies.sh firefox      # use firefox
#   ./scripts/setup_cookies.sh brave        # use brave
#

set -e

BROWSER="${1:-chrome}"
COOKIES_TMP=$(mktemp)

echo "Extracting YouTube cookies from ${BROWSER}..."
yt-dlp --cookies-from-browser "$BROWSER" \
       --cookies "$COOKIES_TMP" \
       --skip-download \
       "https://www.youtube.com/watch?v=jNQXAC9IVRw" 2>/dev/null

if [ ! -s "$COOKIES_TMP" ]; then
    echo "Error: Failed to extract cookies. Make sure ${BROWSER} is closed and yt-dlp is installed."
    rm -f "$COOKIES_TMP"
    exit 1
fi

echo "Encoding and uploading to GitHub..."

# base64 encode (macOS and Linux compatible)
if command -v base64 &>/dev/null; then
    YT_COOKIES_B64=$(base64 -w0 "$COOKIES_TMP" 2>/dev/null || base64 -i "$COOKIES_TMP")
else
    echo "Error: base64 command not found"
    rm -f "$COOKIES_TMP"
    exit 1
fi

# Set the GitHub secret
echo "$YT_COOKIES_B64" | gh secret set YT_COOKIES_B64

rm -f "$COOKIES_TMP"

echo ""
echo "Done! YT_COOKIES_B64 secret has been set."
echo "You can now run the workflow from GitHub Actions."
echo ""
echo "Note: re-run this script if cookies expire (typically every few weeks)."
