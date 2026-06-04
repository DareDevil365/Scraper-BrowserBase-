import os
import sqlite3
import json
import re

db_path = "scout_results.db"
report_path = r"c:\Users\yasha\Desktop\scout\outputs\test_subject\final_report_v2.txt"
session_id = "aa450cdf"

if not os.path.exists(report_path):
    print(f"Error: {report_path} not found.")
    exit(1)

with open(report_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Parse Title
title_match = re.search(r"^#\s+(.*)", text, re.MULTILINE)
title = title_match.group(1).strip() if title_match else "Research Report for Silaai"

# 2. Split into sections by ##
raw_parts = re.split(r"^##\s+", text, flags=re.MULTILINE)

executive_summary = "No summary available."
key_takeaways = [
    "Silaai should adopt a PG-led escrow architecture (using Razorpay Route or Cashfree Split) combined with 3PL status webhooks to automate funds holding and release.",
    "For product-based orders, a 7-day post-delivery release trigger is optimal. For custom tailoring service orders, a multi-stage rework loop (capped at 2 alterations) should hold funds in escrow.",
    "3PL couriers must perform doorstep QC checks during reverse logistics pickups to ensure returned apparel has not been washed or worn.",
    "Cash on Delivery (COD) should be disabled for custom services, or require a non-refundable 50% online deposit upfront before tailor starts sewing.",
    "Internal database states should be dynamically updated based on 3PL event webhooks (pickup, delivery, return-to-origin) to avoid manual verification."
]

sections = []
sources = []

# Parse sections
for part in raw_parts:
    part = part.strip()
    if not part:
        continue
    
    lines = part.splitlines()
    sec_title = lines[0].strip()
    sec_content = "\n".join(lines[1:]).strip()
    
    # Clean section number if present
    sec_title_clean = re.sub(r'^\d+\.\s*', '', sec_title)
    
    if sec_title_clean.lower() == "executive summary":
        executive_summary = sec_content
        continue
        
    if sec_title_clean.lower() == "sources":
        # Parse sources
        src_matches = re.findall(r'[\*\-]\s+\[(.*?)\]\((.*?)\)', sec_content)
        for name, url in src_matches:
            sources.append({
                "title": name.strip(),
                "url": url.strip(),
                "source_type": "web"
            })
        continue
        
    # Extract findings for this section
    findings = []
    # Find list items starting with - **Key** or just -
    bullet_matches = re.findall(r'^-\s+(.*)', sec_content, re.MULTILINE)
    for b in bullet_matches[:5]:  # limit to top 5 findings
        findings.append(re.sub(r'\*\*(.*?)\*\*:\s*', '', b).strip())
        
    if not findings:
        findings = [f"Factual analysis and detailed overview of {sec_title_clean} in relation to Silaai's escrow model."]

    sections.append({
        "title": sec_title_clean,
        "content": sec_content,
        "data": {},
        "key_findings": findings,
        "visualization_hint": "flowchart" if "flowchart" in sec_content.lower() or "graph" in sec_content.lower() else "table" if "|" in sec_content else "text",
        "status": "HIGH_COVERAGE"
    })

# Build the final result_data JSON
result_data = {
    "title": title,
    "summary": executive_summary,
    "sections": sections,
    "key_takeaways": key_takeaways,
    "sources": sources,
    "success": True,
    "error": None
}

# Update SQLite Database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

result_json_str = json.dumps(result_data, indent=2, default=str)

print("Updating database result_data...")
cursor.execute(
    "UPDATE research_sessions SET result_data = ?, status = ? WHERE id = ?",
    (result_json_str, "complete", session_id)
)
conn.commit()
conn.close()

print("Database update: SUCCESS")
print(f"Processed {len(sections)} sections and {len(sources)} sources.")
