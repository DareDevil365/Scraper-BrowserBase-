import os
import re
import json

url_pattern = re.compile(r'https?://[^\s\)\"\'\>]+')
all_urls = {}

for root, dirs, files in os.walk('Furniture'):
    for f in files:
        if f.endswith('.md') or f.endswith('.html'):
            filepath = os.path.join(root, f)
            try:
                with open(filepath, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                    matches = url_pattern.findall(content)
                    for m in matches:
                        clean_m = m.rstrip('.,;:)[]')
                        all_urls.setdefault(clean_m, []).append(filepath)
            except Exception as e:
                pass

print(f"Total unique URLs found: {len(all_urls)}")
with open('scratch/all_scanned_urls.json', 'w', encoding='utf-8') as out:
    json.dump(all_urls, out, indent=2)
