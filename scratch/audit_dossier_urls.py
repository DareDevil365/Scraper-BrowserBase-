import os
import re
import json
import requests
import concurrent.futures

url_pattern = re.compile(r'https?://[^\s\)\"\'\>\\]+')

company_urls = {}
for comp in sorted(os.listdir('Furniture')):
    comp_dir = os.path.join('Furniture', comp)
    if os.path.isdir(comp_dir):
        company_urls[comp] = set()
        for f in os.listdir(comp_dir):
            if f.endswith('.md'):
                fpath = os.path.join(comp_dir, f)
                with open(fpath, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                    matches = url_pattern.findall(content)
                    for m in matches:
                        clean_m = m.rstrip('.,;:)[]\'"\\')
                        if clean_m.startswith('http'):
                            company_urls[comp].add((clean_m, f))

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

all_unique_urls = set()
for comp, url_set in company_urls.items():
    for u, f in url_set:
        all_unique_urls.add(u)

print(f"Total unique URLs across company dossiers: {len(all_unique_urls)}")

def test_url(url):
    try:
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True, stream=True)
        return url, r.status_code, str(r.url)
    except requests.exceptions.SSLError:
        try:
            r = requests.get(url, headers=headers, timeout=10, allow_redirects=True, stream=True, verify=False)
            return url, f"{r.status_code}_SSL_UNVERIFIED", str(r.url)
        except Exception as e:
            return url, f"ERR_{type(e).__name__}", ""
    except Exception as e:
        return url, f"ERR_{type(e).__name__}", ""

url_status = {}
with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
    future_to_url = {executor.submit(test_url, u): u for u in all_unique_urls}
    for future in concurrent.futures.as_completed(future_to_url):
        u, status, final_url = future.result()
        url_status[u] = (status, final_url)
        print(f"[{status}] {u}")

print("\n================ BROKEN / FAILED URLS BY COMPANY ================")
broken_count = 0
for comp in sorted(company_urls.keys()):
    broken_for_comp = []
    for u, f in company_urls[comp]:
        status, final_url = url_status.get(u, ("UNKNOWN", ""))
        # Treat anything not 200/301/302 or >= 400 or error as broken
        if str(status).startswith("ERR") or str(status).startswith("4") or str(status).startswith("5"):
            broken_for_comp.append((u, f, status))
            broken_count += 1
    if broken_for_comp:
        print(f"\n--- {comp} ---")
        for u, f, s in broken_for_comp:
            print(f"  [{s}] in {f}: {u}")

print(f"\nTotal broken URLs across all dossiers: {broken_count}")

with open('scratch/dossier_url_audit.json', 'w', encoding='utf-8') as f:
    json.dump({u: {"status": s[0], "final_url": s[1]} for u, s in url_status.items()}, f, indent=2)
