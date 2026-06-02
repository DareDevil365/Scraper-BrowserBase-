import json
from engine import extractor
from engine.discoverer import refine_research_prompt
from engine.deep_extractor import discover_sources_for_session, deep_research_company
from engine.sources_db import COMPANY_SOURCES

from app import _load_api_keys
keys = _load_api_keys()
if not keys:
    print("Warning: No api keys loaded from api_keys.txt. Please verify your keys.")
extractor.configure(keys)

print("--- 1. Testing Discoverer Plan Refinement ---")
query = "I need pricing data for Delhivery, Xpressbees, Leopards Courier, and FedEx India."
answers = [
    {"question_id": "q1", "answer": "0-500 shipments"},
    {"question_id": "research_depth", "answer": "Surface Level"}
]

plan = refine_research_prompt(query, answers)
print("Plan Success:", plan.get("success"))
if plan.get("success"):
    vectors = plan.get("vectors", [])
    print(f"Generated {len(vectors)} vectors.")
    for v in vectors[:2]:
        print(f"Vector '{v.get('topic')}':")
        print(f"  Data Points: {v.get('data_points')}")
        print(f"  Search Hints: {v.get('search_hints')}")
else:
    print("Plan Error:", plan.get("error"))
    exit(1)

print("\n--- 2. Testing Curated Source Injection ---")
# Test discovery for the first vector
vector = vectors[0]
session_id = "test_sess"
refined_prompt = plan.get("refined_prompt", "")
discovered = discover_sources_for_session(
    session_id=session_id,
    vectors=[vector],
    refined_prompt=refined_prompt,
    original_query=query,
    depth="surface"
)
print(f"Discovered {len(discovered)} total sources.")
curated_urls = [s for s in discovered if s.get("source_type") == "curated"]
print(f"Curated sources injected: {len(curated_urls)}")
for c in curated_urls[:5]:
    print(f"  - {c.get('url')} (Score: {c.get('score')})")

print("\n--- 3. Testing Non-Operational Carrier Skip ---")
# Verify skipping Leopards Courier and FedEx India
for carrier in ["Leopards Courier", "FedEx India"]:
    result = deep_research_company(
        company=carrier,
        data_points=["base_price", "cod_charges"],
        instruction="Focus on domestic Indian shipping",
        max_scrape=1,
        progress_cb=lambda msg: print(f"    Progress: {msg}")
    )
    print(f"Carrier: {carrier}")
    print(f"  Success: {result.get('success')}")
    print(f"  Reason/Skip: {result.get('data', {}).get('reason')}")
    print(f"  Non-Operational Flag: {result.get('data', {}).get('non_operational')}")
