"""
Test script for local Stealth Scraper
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from engine.scraper_stealth import scrape_sync

def test_run():
    print("=== Local Stealth Scraper Test ===")
    
    test_url = "https://news.ycombinator.com/"
    print(f"Scraping locally using anti-detection masking: {test_url} ...")
    
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
