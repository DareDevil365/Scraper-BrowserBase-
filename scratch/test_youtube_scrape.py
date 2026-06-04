import asyncio
import sys
import re
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def fetch_youtube_transcript(video_url_or_id: str) -> str:
    video_id = video_url_or_id
    if "youtube.com" in video_url_or_id or "youtu.be" in video_url_or_id:
        match = re.search(r'(?:v=|\/)([a-zA-Z0-9_-]{11})', video_url_or_id)
        if match:
            video_id = match.group(1)
            
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        
        # Support list-based or legacy static method based retrieval
        if hasattr(api, 'list'):
            transcript_list = api.list(video_id)
            try:
                transcript = transcript_list.find_transcript(['en'])
            except Exception:
                transcript = next(iter(transcript_list))
                if transcript.is_translatable:
                    try:
                        transcript = transcript.translate('en')
                    except Exception:
                        pass
            data = transcript.fetch()
        else:
            data = YouTubeTranscriptApi.get_transcript(video_id)
            
        # Support both dataclasses (new API) and dictionaries (old API)
        text_segments = []
        for item in data:
            if hasattr(item, 'text'):
                text_segments.append(item.text)
            elif isinstance(item, dict) and 'text' in item:
                text_segments.append(item['text'])
        return " ".join(text_segments)
    except Exception as e:
        return f"Failed to fetch transcript: {e}"

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        
    test_video_id = "exmSJpJvIPs"  # Apna College Docker Tutorial (Hindi auto-generated transcript)
    print(f"Fetching transcript for video ID: {test_video_id}...")
    transcript = fetch_youtube_transcript(test_video_id)
    print("\n--- Transcript Sample (First 500 chars) ---")
    print(transcript[:500])
    print("\n------------------------------------------")
