import asyncio
import os
import shutil
import time
from engine.scraper import fetch_page, _get_cache_dir, _get_cache_file_path, close_browser

async def test_caching():
    test_url = "https://example.com"
    cache_dir = _get_cache_dir()
    cache_file = _get_cache_file_path(test_url)
    
    print(f"Cache directory resolved to: {cache_dir}")
    print(f"Cache file for URL '{test_url}' resolved to: {cache_file}")
    
    # 1. Clear cache for test URL to ensure clean start
    if os.path.exists(cache_file):
        os.remove(cache_file)
        print("Removed existing cache file for a clean start.")
    
    # 2. First fetch (Cache Miss)
    print("\n--- Phase 1: Fetching page (Cache Miss expected) ---")
    start_time = time.time()
    res1 = await fetch_page(test_url, method="standard", bypass_cache=False)
    duration1 = time.time() - start_time
    
    print(f"Scraped By: {res1.get('scraped_by')}")
    print(f"Success: {res1.get('success')}")
    print(f"Title: {res1.get('title')}")
    print(f"Duration: {duration1:.2f} seconds")
    
    assert res1.get("success"), "First fetch should be successful"
    assert "cached" not in res1.get("scraped_by", ""), "First fetch should not be from cache"
    assert os.path.exists(cache_file), "Cache file should have been created after successful fetch"
    
    # 3. Second fetch (Cache Hit)
    print("\n--- Phase 2: Fetching page again (Cache Hit expected) ---")
    start_time = time.time()
    res2 = await fetch_page(test_url, method="standard", bypass_cache=False)
    duration2 = time.time() - start_time
    
    print(f"Scraped By: {res2.get('scraped_by')}")
    print(f"Success: {res2.get('success')}")
    print(f"Duration: {duration2:.4f} seconds")
    
    assert res2.get("success"), "Second fetch should be successful"
    assert "cached" in res2.get("scraped_by", ""), "Second fetch should be from cache"
    assert duration2 < 0.1, f"Second fetch should be almost instantaneous, but took {duration2:.4f}s"
    
    # 4. Third fetch (Bypass Cache)
    print("\n--- Phase 3: Fetching page with bypass_cache=True (Cache Bypass expected) ---")
    start_time = time.time()
    res3 = await fetch_page(test_url, method="standard", bypass_cache=True)
    duration3 = time.time() - start_time
    
    print(f"Scraped By: {res3.get('scraped_by')}")
    print(f"Success: {res3.get('success')}")
    print(f"Duration: {duration3:.2f} seconds")
    
    assert res3.get("success"), "Bypassed fetch should be successful"
    assert "cached" not in res3.get("scraped_by", ""), "Bypassed fetch should not be from cache"
    
    # 5. Fourth fetch (Stale Cache TTL)
    print("\n--- Phase 4: Fetching page with cache_ttl=-1 (Stale Cache Miss expected) ---")
    start_time = time.time()
    res4 = await fetch_page(test_url, method="standard", bypass_cache=False, cache_ttl=-1)
    duration4 = time.time() - start_time
    
    print(f"Scraped By: {res4.get('scraped_by')}")
    print(f"Success: {res4.get('success')}")
    print(f"Duration: {duration4:.2f} seconds")
    
    assert res4.get("success"), "Stale cache fetch should be successful"
    assert "cached" not in res4.get("scraped_by", ""), "Stale cache fetch should not be from cache"
    
    print("\n[SUCCESS] All cache verification tests passed successfully!")
    await close_browser()

if __name__ == "__main__":
    asyncio.run(test_caching())
