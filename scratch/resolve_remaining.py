import os
import re
import json
import requests
import time

CACHE_FILE = r"c:\Users\yasha\Desktop\scout\scratch\resolved_urls_cache.json"
DIR_PATH = r"c:\Users\yasha\Desktop\scout\outputs\competitor_research"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def resolve_url(url, headers):
    try:
        r = requests.get(url, headers=headers, allow_redirects=True, timeout=8)
        if r.status_code == 200:
            if r.url == url or "vertexaisearch" in r.url:
                if r.history:
                    for hist in r.history:
                        if "vertexaisearch" not in hist.url:
                            return hist.url
            return r.url
    except Exception as e:
        print(f"Error resolving {url[:50]}...: {e}")
    return url

def main():
    cache = load_cache()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Scan files for URLs
    file_urls = {}
    all_redirects = set()
    for fn in os.listdir(DIR_PATH):
        if fn.endswith(".txt"):
            path = os.path.join(DIR_PATH, fn)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            found = re.findall(r"https://vertexaisearch\.cloud\.google\.com/grounding-api-redirect/[a-zA-Z0-9_\-=\+]+", content)
            if found:
                file_urls[path] = (content, found)
                all_redirects.update(found)
                
    print(f"Found {len(all_redirects)} unique redirect URLs in files.")
    
    # Resolve sequentially
    resolved_mapping = {}
    for idx, url in enumerate(all_redirects, 1):
        if url in cache and cache[url] != url:
            resolved_mapping[url] = cache[url]
            print(f"[{idx}/{len(all_redirects)}] Cached: {cache[url][:80]}")
        else:
            print(f"[{idx}/{len(all_redirects)}] Resolving {url[:60]}...")
            final_url = resolve_url(url, headers)
            if final_url != url:
                resolved_mapping[url] = final_url
                cache[url] = final_url
                print(f"    Success -> {final_url[:80]}")
            else:
                resolved_mapping[url] = url
                cache[url] = url
                print(f"    Failed (kept original)")
            # Small rate-limiting sleep
            time.sleep(0.5)
            
    # Save the updated cache
    save_cache(cache)
    
    # Update files
    for path, (content, urls) in file_urls.items():
        new_content = content
        replaced = 0
        for url in urls:
            resolved = resolved_mapping.get(url, url)
            if resolved != url:
                new_content = new_content.replace(url, resolved)
                replaced += 1
        if replaced > 0:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Updated {os.path.basename(path)}: replaced {replaced} URLs.")
            
    print("Done!")

if __name__ == "__main__":
    main()
