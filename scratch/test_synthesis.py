import sys
import os
import json
from google import genai
from google.genai import types

sys.path.append(os.path.abspath("."))
from engine import extractor

def load_keys():
    keys = []
    keys_file = "api_keys.txt"
    if os.path.exists(keys_file):
        with open(keys_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    keys.extend([k.strip() for k in line.split(",") if k.strip()])
    return ",".join(keys)

def main():
    keys = load_keys()
    print(f"Configuring extractor with {len(keys.split(','))} keys.")
    extractor.configure(keys)
    
    # Load escrow vector data
    v_path = r"outputs/what_exactly_is_an_escrow_account_difference_in_3pl_and_paym_20260602204305_0006da65/extracted/escrow_and_gateway_vs_3pl.json"
    with open(v_path, "r", encoding="utf-8") as f:
        payload = json.load(f)
        
    topic = payload["vector"]["topic"]
    desc = payload["vector"]["description"]
    status = payload["status"]
    data = payload["data"]
    sources = payload["sources"]
    original_query = "what exactly is an escrow account..."
    
    section_prompt = f"""You are a market analyst writing a specific section of a research report.
Original User Query: "{original_query}"
Sub-topic (Vector): "{topic}"
Description: "{desc}"
Coverage Class: "{status}"

Extracted Structured Data:
{json.dumps(data, indent=2)}

Sources used:
{json.dumps(sources[:5], indent=2)}

Your task is to write a detailed, professional section for this sub-topic.
Output your response as a valid JSON object matching this schema:
{{
  "title": "Title of the section",
  "content": "Detailed narrative text for the section.",
  "data": null,
  "key_findings": [],
  "visualization_hint": "bullets"
}}
Return ONLY the valid JSON object. No explanations, no markdown blocks."""

    print("Calling Gemini...")
    try:
        response = extractor._call_gemini(
            contents=section_prompt,
            tier="mid",
            judgment=False,
            config=types.GenerateContentConfig(
                temperature=0.15,
                response_mime_type="application/json"
            )
        )
        print("Raw Response text:")
        print(response.text)
    except Exception as e:
        print("Error calling Gemini:", e)
        print("Cell states status:")
        for k, v in extractor._cell_states.items():
            if v.get("exhausted_today") or v.get("cooldown_until") > 0:
                print(k, v)

if __name__ == "__main__":
    main()
