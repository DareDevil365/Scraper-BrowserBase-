import json
import concurrent.futures
import requests

with open('scratch/all_scanned_urls.json', 'r', encoding='utf-8') as f:
    all_urls = json.load(f)

print(f"Loaded {len(all_urls)} URLs to audit.")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

results = {}

def check_url(url):
    try:
        # Use HEAD or GET with stream=True
        r = requests.get(url, headers=headers, timeout=8, stream=True, allow_redirects=True)
        return url, r.status_code, str(r.url)
    except requests.exceptions.SSLError:
        try:
            r = requests.get(url, headers=headers, timeout=8, stream=True, allow_redirects=True, verify=False)
            return url, f"{r.status_code}_SSL_UNVERIFIED", str(r.url)
        except Exception as e:
            return url, f"ERR_{type(e).__name__}", ""
    except Exception as e:
        return url, f"ERR_{type(e).__name__}", ""

with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
    future_to_url = {executor.submit(check_url, u): u for u in all_urls.keys()}
    for future in concurrent.futures.as_completed(future_to_url):
        url, status, final_url = future.result()
        results[url] = {
            "status": status,
            "final_url": final_url,
            "files": all_urls[url]
        }
        print(f"[{status}] {url}")

with open('scratch/audit_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

print("\n--- SUMMARY ---")
statuses = {}
for u, data in results.items():
    s = str(data['status'])
    statuses[s] = statuses.get(s, 0) + 1

for s, cnt in sorted(statuses.items()):
    print(f"{s}: {cnt}")
