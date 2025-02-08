"""
CC.py
------
This module extracts the YouTube video ID from a URL and uses yt-dlp
to fetch the captions URL (subtitles URL). It requires a cookies file for authentication.
"""

import re
import yt_dlp

# Path to your cookies file (exported from your browser)
cookies_file = "src/CC_capture/cookies.txt"

def get_video_id(youtube_url: str) -> str:
    """
    Extracts and returns the video ID from the given YouTube URL.
    
    Args:
        youtube_url (str): Full YouTube URL.
        
    Returns:
        str: The video ID if found, otherwise None.
    """
    pattern = r'(?:v=|\/|youtu\.be\/)([0-9A-Za-z_-]{11})'
    match = re.search(pattern, youtube_url)
    return match.group(1) if match else None

def fetch_captions(video_url: str) -> str:
    """
    Uses yt-dlp to fetch the captions URL (either manually uploaded or auto-generated)
    for the given YouTube video URL.
    
    Args:
        video_url (str): Full YouTube video URL.
    
    Returns:
        str: The captions URL if available; otherwise, None.
    """
    video_id = get_video_id(video_url)
    if not video_id:
        print("Invalid YouTube URL provided.")
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
            # Try to get manual subtitles first; fallback to auto-generated captions.
            subtitles = info.get('subtitles', {}).get('en') or info.get('automatic_captions', {}).get('en')
            if subtitles:
                return subtitles[0]['url']
            else:
                print("Captions not available for this video.")
                return None
    except Exception as e:
        print(f"Error fetching captions: {e}")
        return None

"""
# For testing from the command line
if __name__ == "__main__":
    url = input("Enter YouTube Video URL: ")
    caps_url = fetch_captions(url)
    if caps_url:
        print("Fetched Captions URL:")
        print(caps_url)
        
"""