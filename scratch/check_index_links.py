import re, requests
from concurrent.futures import ThreadPoolExecutor

with open(r'c:\Users\yasha\Desktop\My Projects\scout\Furniture\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Match href in HTML and in JSON-escaped HTML
urls = set()
for m in re.finditer(r'href=\\?"(https?://[^\\"]+)\\?"', text):
    u = m.group(1)
    if 'fonts.g' not in u:
        urls.add(u)

urls = sorted(list(urls))
print(f'Total company / document links in index.html: {len(urls)}')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def check(url):
    try:
        r = requests.head(url, headers=headers, timeout=8, allow_redirects=True)
        code = r.status_code
        if code in (403, 404, 405, 500):
            r = requests.get(url, headers=headers, timeout=8, stream=True)
            code = r.status_code
        return url, code, None
    except Exception as e:
        return url, None, str(e)

with ThreadPoolExecutor(max_workers=10) as ex:
    results = list(ex.map(check, urls))

broken = []
for url, code, err in results:
    if err or (code and code >= 400 and code != 403): # Some sites block automated HEAD/GET with 403 bot protection (like Justdial, Cloudflare)
        broken.append((url, code, err))
    else:
        status_str = f"OK {code}" if code else "ERR"
        print(f'[{status_str}] {url}')

print(f'\nTotal Analyzed: {len(urls)}')
print(f'Total Broken (404/Dead): {len(broken)}')
for u, c, e in broken:
    print(f'  [FAIL {c}] {u} (Error: {e})')
