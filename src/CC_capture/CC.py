"""
CC.py
------
Extracts the YouTube video ID from a URL and uses yt-dlp to fetch the captions URL.
Requires a valid cookies file for authentication.
"""

import re
import yt_dlp

# Path to your cookies file (exported from your browser)
cookies_file = "src/CC_capture/cookies.txt"

def get_video_id(youtube_url: str) -> str:
    """
    Extracts and returns the video ID from a given YouTube URL.
    """
    pattern = r'(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, youtube_url)
    return match.group(1) if match else None

def fetch_captions(video_url: str) -> str:
    """
    Uses yt-dlp to fetch the captions URL (manual or auto-generated) for the given video URL.
    """
    video_id = get_video_id(video_url)
    if not video_id:
        print("Invalid YouTube URL.")
        return None

    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'writesubtitles': True,
        'subtitleslangs': ['en'],
        'writeautomaticsub': True,
        'cookiefile': cookies_file,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            subtitles = info.get('subtitles', {}).get('en') or info.get('automatic_captions', {}).get('en')
            if subtitles:
                return subtitles[0]['url']
            else:
                print("Captions not available for this video.")
                return None
    except Exception as e:
        print(f"Error fetching captions: {e}")
        return None

if __name__ == "__main__":
    url = input("Enter YouTube Video URL: ")
    caps_url = fetch_captions(url)
    if caps_url:
        print("Fetched Captions URL:")
        print(caps_url)
