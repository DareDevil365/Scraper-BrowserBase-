import os
import re
import json
import requests
import concurrent.futures

url_pattern = re.compile(r'https?://[^\s\)\"\'\>\\]+')

all_urls = set()
for root, dirs, files in os.walk('Furniture'):
    for f in files:
        if f.endswith('.md') or f.endswith('.html'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fp:
                c = fp.read()
                matches = url_pattern.findall(c)
                for m in matches:
                    clean = m.rstrip('.,;:)[]\'"\\')
                    if clean.startswith('http') and not 'fonts.g' in clean:
                        all_urls.add(clean)

print(f"Total unique URLs to audit across all Furniture files & index.html: {len(all_urls)}")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def check(u):
    try:
        r = requests.get(u, headers=headers, timeout=8, stream=True)
        return u, r.status_code
    except Exception as e:
        return u, f"ERR_{type(e).__name__}"

results = {}
with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
    futures = {executor.submit(check, u): u for u in all_urls}
    for f in concurrent.futures.as_completed(futures):
        u, status = f.result()
        results[u] = status
        print(f"[{status}] {u}")

failed = {u: s for u, s in results.items() if str(s).startswith("ERR") or (isinstance(s, int) and s in (404, 500, 502, 503))}
print(f"\n==========================================")
print(f"TOTAL AUDITED: {len(results)}")
print(f"FAILED (404/500/ERR): {len(failed)}")
print(f"==========================================")
for u, s in sorted(failed.items()):
    print(f"  [{s}] {u}")

with open('scratch/final_link_verification.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)
