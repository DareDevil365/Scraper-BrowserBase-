import os

base = r'c:\Users\yasha\Desktop\My Projects\scout\Furniture'
expected_files = [
    'company_profile.md',
    'pricing_and_pricebook.md',
    'sources_and_evidence.md',
    'brochures_and_catalog_links.md'
]

dirs = [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
print(f'Total company directories: {len(dirs)}')

for d in sorted(dirs):
    cdir = os.path.join(base, d)
    files = os.listdir(cdir)
    missing = [f for f in expected_files if f not in files]
    sizes = {f: os.path.getsize(os.path.join(cdir, f)) for f in expected_files if f in files}
    if missing:
        print(f'{d:20} MISSING: {missing}')
    else:
        min_size = min(sizes.values())
        print(f'{d:20} OK (4 files, min size: {min_size} bytes)')
