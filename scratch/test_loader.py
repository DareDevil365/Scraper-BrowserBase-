import unicodedata, re

def norm(s):
    if not s: return ""
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
    return re.sub(r'[^a-zA-Z0-9]', '', s).lower()

import csv, os
FURNITURE_DIR = r'c:\Users\yasha\Desktop\My Projects\scout\Furniture'
with open(os.path.join(FURNITURE_DIR, "00_PRICING_MASTER_BENCHMARK.csv"), "r", encoding="utf-8") as f:
    csv_rows = list(csv.DictReader(f))

dirs = [d for d in os.listdir(FURNITURE_DIR) if os.path.isdir(os.path.join(FURNITURE_DIR, d))]

for d in sorted(dirs):
    nd = norm(d)
    match = None
    for r in csv_rows:
        nr = norm(r['Company_Name'])
        if nd in nr or nr in nd or (d == 'Arttdinox' and 'arttd' in nr) or (d == 'Sleek_AsianPaints' and 'sleek' in nr) or (d == 'Wurfel' and 'wurf' in nr):
            match = r['Company_Name']
            break
    print(f'{d:20} -> {match}')
