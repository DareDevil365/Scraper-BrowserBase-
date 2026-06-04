import sys
import os
import re
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Unset YouTube API Key to force the keyless fallback path
if "YOUTUBE_API_KEY" in os.environ:
    del os.environ["YOUTUBE_API_KEY"]

from engine.deep_extractor import discover_youtube_sources, fetch_youtube_transcript

def test_integration():
    print("=== YouTube Keyless Integration Verification ===")
    
    # 1. Test video search via browser fallback
    query = "kubernetes tutorial"
    print(f"\n1. Testing YouTube search for '{query}'...")
    results = discover_youtube_sources(query, max_results=3)
    
    print(f"Found {len(results)} videos:")
    for idx, r in enumerate(results):
        print(f"  {idx+1}. Title: {r.get('title')}")
        print(f"     URL: {r.get('url')}")
        print(f"     Channel: {r.get('channel')}")
        print(f"     Views: {r.get('view_count')}")
        print(f"     ID: {r.get('id')}")
        
    if not results:
        print("[-] Search returned no results.")
        return False
        
    # 2. Test transcript retrieval for the first result
    first_video = results[0]
    print(f"\n2. Fetching transcript for: '{first_video['title']}' ({first_video['url']})...")
    transcript = fetch_youtube_transcript(first_video['url'])
    
    if transcript and not transcript.startswith("Failed"):
        print("[+] Transcript fetched successfully!")
        print("\nTranscript Snippet (First 300 chars):")
        print("-" * 50)
        print(transcript[:300])
        print("-" * 50)
        return True
    else:
        print(f"[-] Transcript fetch failed: {transcript}")
        return False

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    
    success = test_integration()
    if success:
        print("\n[SUCCESS] Keyless YouTube integration is fully operational!")
        sys.exit(0)
    else:
        print("\n[FAILURE] Integration tests failed.")
        sys.exit(1)
