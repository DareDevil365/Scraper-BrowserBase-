import csv, os
FURNITURE_DIR = r'c:\Users\yasha\Desktop\My Projects\scout\Furniture'
with open(os.path.join(FURNITURE_DIR, "00_PRICING_MASTER_BENCHMARK.csv"), "r", encoding="utf-8") as f:
    csv_rows = list(csv.DictReader(f))

for r in csv_rows:
    raw = r['Target_Customer_Segment']
    # Let's write the parsing logic for tier_main and tier_criteria
    tier_main = raw
    tier_criteria = ""
    if '(' in raw:
        parts = raw.split('(', 1)
        tier_main = parts[0].strip()
        tier_criteria = parts[1].rstrip(')').strip()
    
    # Classify tier
    t = tier_main.lower()
    if 'ultra' in t:
        badge_cls = 'badge-ultra'
        badge_label = 'Ultra-HNI'
    elif 'rich' in t or 'luxury' in t or 'hni' in t or 'architect' in t:
        badge_cls = 'badge-rich'
        badge_label = 'Luxury HNI'
    elif 'upper' in t:
        badge_cls = 'badge-upper-mid'
        badge_label = 'Upper Middle'
    elif 'middle' in t or 'first-time' in t:
        badge_cls = 'badge-mid'
        badge_label = 'Middle Class'
    else:
        badge_cls = 'badge-budget'
        badge_label = 'Budget / Value'
        
    print(f"{r['Company_Name']:25} -> [{badge_cls}] {badge_label} | Criteria: {tier_criteria}")
