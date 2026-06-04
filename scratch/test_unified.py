import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from engine.scraper import fetch_page, close_browser

async def test_scraper():
    # Test URLs
    test_url_simple = "https://example.com"
    test_url_dynamic = "https://quotes.toscrape.com/js/"
    
    print("=== Testing Standard Mode ===")
    res_std = await fetch_page(test_url_simple, method="standard")
    print(f"Standard Success: {res_std['success']}")
    print(f"Standard Title: {res_std['title']}")
    print(f"Scraped By: {res_std['scraped_by']}")
    print(f"Markdown Content Length: {len(res_std['markdown'])}")
    
    print("\n=== Testing Stealth Mode ===")
    res_stealth = await fetch_page(test_url_dynamic, method="stealth")
    print(f"Stealth Success: {res_stealth['success']}")
    print(f"Stealth Title: {res_stealth['title']}")
    print(f"Scraped By: {res_stealth['scraped_by']}")
    print(f"Markdown Content Length: {len(res_stealth['markdown'])}")

    print("\n=== Testing Auto Mode ===")
    res_auto = await fetch_page(test_url_simple, method="auto")
    print(f"Auto Success: {res_auto['success']}")
    print(f"Auto Title: {res_auto['title']}")
    print(f"Scraped By: {res_auto['scraped_by']}")
    print(f"Markdown Content Length: {len(res_auto['markdown'])}")

    # Close browser when done
    await close_browser()

if __name__ == "__main__":
    asyncio.run(test_scraper())
