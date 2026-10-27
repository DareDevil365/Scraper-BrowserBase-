import re
import json

with open('Furniture/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'const COMPANIES = (\{.*?\});\s*const CSV_ROWS', html, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    print(f"COMPANIES loaded: {len(data)}")
    for k, v in sorted(data.items()):
        s_links = re.findall(r'href=["\']([^"\']+)["\']', v.get('sources_html', ''))
        b_links = re.findall(r'href=["\']([^"\']+)["\']', v.get('brochures_html', ''))
        all_l = list(set(s_links + b_links))
        print(f"\n{k} ({len(all_l)} links):")
        for l in all_l:
            print(f"   {l}")
else:
    print("Could not match COMPANIES regex")
