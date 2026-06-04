import json
from engine import extractor
from engine.discoverer import refine_research_prompt
from app import _load_api_keys

keys = _load_api_keys()
if not keys:
    print("Warning: No api keys loaded from api_keys.txt. Please verify your keys.")
extractor.configure(keys)

query = "I need pricing data for Delhivery, Xpressbees, Leopards Courier, and FedEx India."
answers = [
    {"question_id": "q1", "answer": "0-500 shipments"},
    {"question_id": "research_depth", "answer": "Surface Level"}
]

plan = refine_research_prompt(query, answers)
print("Plan Success:", plan.get("success"))
if plan.get("success"):
    print("Refined Master Prompt snippet:")
    print(plan.get("refined_prompt")[:400] + "...\n")
    print(f"Generated {len(plan.get('vectors', []))} vectors:")
    for i, v in enumerate(plan.get("vectors", [])):
        print(f"Vector {i+1}:")
        print(f"  ID: {v.get('id')}")
        print(f"  Topic: {v.get('topic')}")
        print(f"  Description: {v.get('description')}")
        print(f"  Search Hints: {v.get('search_hints')}")
        print(f"  Data Points: {v.get('data_points')}")
else:
    print("Error:", plan.get("error"))
