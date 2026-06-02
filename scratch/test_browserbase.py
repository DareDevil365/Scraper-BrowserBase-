"""
Test script for Browserbase scraping
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from engine.scraper_browserbase import scrape_sync

def test_run():
    print("=== Browserbase Cloud Scrape Test ===")
    
    # 1. Check API Key
    api_key = os.environ.get("BROWSERBASE_API_KEY")
    if not api_key:
        print("[!] Error: BROWSERBASE_API_KEY environment variable is not set.")
        print("Please set it in your environment before running this test.")
        print("Example: $env:BROWSERBASE_API_KEY='your-key-here'")
        sys.exit(1)
        
    test_url = "https://news.ycombinator.com/"
    print(f"Scraping: {test_url} ...")
    
    # 2. Run Scraping
    res = scrape_sync(test_url)
    
    # 3. Print Results
    print("\n=== Result ===")
    print(f"Success: {res['success']}")
    if res['success']:
        print(f"Title: {res['title']}")
        print(f"Markdown character length: {len(res['markdown'])}")
        print("\nFirst 500 characters of Markdown:")
        print("-" * 50)
        print(res['markdown'][:500])
        print("-" * 50)
    else:
        print(f"Error encountered: {res['error']}")

if __name__ == "__main__":
    test_run()
