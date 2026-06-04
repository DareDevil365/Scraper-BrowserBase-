import os
import re
import json
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

CACHE_FILE = r"c:\Users\yasha\Desktop\scout\scratch\resolved_urls_cache.json"
DIR_PATH = r"c:\Users\yasha\Desktop\scout\outputs\competitor_research"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"[CACHE] Loaded {len(data)} entries.")
                return data
        except Exception as e:
            print(f"[CACHE] Error loading cache: {e}")
            return {}
    print("[CACHE] Cache file not found. Starting fresh.")
    return {}

def save_cache(cache):
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
        print(f"[CACHE] Successfully saved {len(cache)} entries to {CACHE_FILE}")
        print(f"[CACHE] File exists now: {os.path.exists(CACHE_FILE)}")
    except Exception as e:
        print(f"[CACHE] Failed to save cache: {e}")

def resolve_single_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    for attempt in range(4):
        try:
            # Using GET because HEAD is sometimes blocked or not supported on redirects
            r = requests.get(url, headers=headers, allow_redirects=True, timeout=8)
            if r.status_code == 200:
                # If it didn't change (e.g. redirected to login or same page)
                if r.url == url or "vertexaisearch" in r.url:
                    # Let's try to see if there is any redirect in history
                    if r.history:
                        for hist in r.history:
                            if "vertexaisearch" not in hist.url:
                                return url, hist.url
                return url, r.url
            print(f"[RESOLVE] Non-200 status {r.status_code} for {url}. Retrying...")
        except Exception as e:
            print(f"[RESOLVE] Attempt {attempt+1} failed for {url}: {e}")
            time.sleep(1.5 * (attempt + 1))
            
    print(f"[RESOLVE] Failed to resolve {url} after 4 attempts.")
    return url, url

def main():
    cache = load_cache()
    
    # 1. Scan files for vertexaisearch URLs
    all_urls = set()
    file_contents = {}
    
    if not os.path.exists(DIR_PATH):
        print(f"[ERROR] Directory {DIR_PATH} does not exist!")
        return
        
    for fn in os.listdir(DIR_PATH):
        if fn.endswith(".txt"):
            path = os.path.join(DIR_PATH, fn)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                file_contents[path] = content
                # Make sure the regex captures the entire token including trailing equal signs
                found = re.findall(r"https://vertexaisearch\.cloud\.google\.com/grounding-api-redirect/[a-zA-Z0-9_\-=\+]+", content)
                all_urls.update(found)
                
    # Filter URLs that are not in cache (or failed in cache)
    urls_to_resolve = [url for url in all_urls if url not in cache or cache[url] == url]
    print(f"Found {len(all_urls)} total unique redirect URLs. {len(urls_to_resolve)} need resolution.")
    
    # 2. Resolve missing URLs concurrently but with moderate workers to prevent IP rate-limiting
    resolved_count = 0
    if urls_to_resolve:
        print(f"Resolving {len(urls_to_resolve)} URLs concurrently with 5 workers...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(resolve_single_url, url): url for url in urls_to_resolve}
            for future in as_completed(futures):
                orig_url, final_url = future.result()
                if final_url != orig_url:
                    cache[orig_url] = final_url
                else:
                    # Don't cache failed ones permanently, or cache them as same to not retry this run
                    cache[orig_url] = final_url
                resolved_count += 1
                if resolved_count % 10 == 0:
                    print(f"Resolved {resolved_count}/{len(urls_to_resolve)}...")
                    # Intermediary saves
                    save_cache(cache)
                    
        save_cache(cache)
        
    # 3. Replace in files
    for path, content in file_contents.items():
        new_content = content
        replaced_in_file = 0
        found = re.findall(r"https://vertexaisearch\.cloud\.google\.com/grounding-api-redirect/[a-zA-Z0-9_\-=\+]+", content)
        for url in found:
            resolved_url = cache.get(url, url)
            if resolved_url != url:
                new_content = new_content.replace(url, resolved_url)
                replaced_in_file += 1
                
        if replaced_in_file > 0:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Updated {os.path.basename(path)}: replaced {replaced_in_file} URLs.")
            
    print("Done resolving all URLs.")

if __name__ == "__main__":
    main()
