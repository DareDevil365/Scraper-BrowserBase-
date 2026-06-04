import os
import sys
import json
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import discoverer
from engine import deep_extractor
from engine import extractor
from engine.scraper import _run_async

def test_youtube_flow():
    print("=== Testing end-to-end keyless YouTube research vector flow ===")
    
    # Configure API Keys
    api_key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api_keys.txt")
    if os.path.exists(api_key_path):
        keys_list = []
        with open(api_key_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    keys_list.extend([k.strip() for k in line.split(",") if k.strip()])
        extractor.configure(",".join(keys_list))
        print(f"[*] Configured {extractor.get_key_count()} Gemini keys.")
        
    vector = {
        "id": "v_docker_basics",
        "topic": "Docker Basics",
        "description": "Docker tutorial for absolute beginners, including container lifecycle and setup.",
        "search_hints": ["docker tutorial", "container basics"],
        "data_points": ["container lifecycle", "docker install steps"]
    }
    
    print("\nExecuting deep_research_vector for topic 'Docker Basics'...")
    # Run with max_scrape=3 so we reserve 1 slot for YouTube and 2 for web
    res = deep_extractor.deep_research_vector(
        vector=vector,
        research_context="Docker vs Kubernetes learning guide for beginners",
        instruction="Compare Docker container setup with Kubernetes pod concepts",
        max_scrape=3,
        progress_cb=lambda msg: print(f"  [Progress] {msg}"),
        output_folder="",
        depth="surface"
    )
    
    print("\n=== Result ===")
    print(f"Success: {res.get('success')}")
    print(f"Unique sources extracted: {len(res.get('sources', []))}")
    for idx, s in enumerate(res.get("sources", [])):
        print(f"  Source {idx+1}: {s.get('url')} | Type: {s.get('source_type')} | Score: {s.get('score')} | Status: {s.get('status')}")
        
    # Check that at least one youtube video was resolved and scraped
    yt_scraped = [s for s in res.get("sources", []) if s.get("source_type") == "youtube" and s.get("status") == "SUCCESS"]
    print(f"\nYouTube videos successfully scraped: {len(yt_scraped)}")
    assert len(yt_scraped) > 0, "No YouTube videos were successfully scraped!"
    print("\n[SUCCESS] End-to-end YouTube flow test passed successfully!")

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    test_youtube_flow()
