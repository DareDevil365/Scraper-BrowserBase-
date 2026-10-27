import re
import requests

with open('Furniture/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

hrefs = re.findall(r'href=["\'](https?://[^"\']+)["\']', c)
print(f"Total hrefs in index.html: {len(hrefs)}")

unique_hrefs = list(dict.fromkeys(hrefs))
print(f"Unique hrefs: {len(unique_hrefs)}")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print("\n--- Testing each unique link ---")
bad = []
for h in unique_hrefs:
    try:
        r = requests.get(h, headers=headers, timeout=6, stream=True)
        if r.status_code >= 400:
            print(f"[{r.status_code}] {h}")
            bad.append((h, r.status_code))
        else:
            print(f"[OK {r.status_code}] {h}")
    except Exception as e:
        print(f"[ERR {type(e).__name__}] {h}")
        bad.append((h, str(type(e).__name__)))

print(f"\nTotal broken/problematic links: {len(bad)}")
for b in bad:
    print(b)
