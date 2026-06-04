import os
import sys
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import extractor

def load_keys():
    keys = []
    # 1. Load from api_keys.txt if it exists
    keys_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api_keys.txt")
    if os.path.exists(keys_file):
        with open(keys_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    keys.extend([k.strip() for k in line.split(",") if k.strip()])
    return ",".join(keys)

def research_company(company_name: str) -> str:
    print(f"\n[*] Researching {company_name}...")
    
    query = f"""Research the escrow model, payment release, disputes, and seller/merchant/provider protections for the platform '{company_name}'.
Specifically, we need to know:
1. ESCROW MODEL:
   - Does it use escrow? (Yes / No / Escrow-like)
   - Who holds the funds?
   - When are funds collected? (Before work / At order / On delivery)
2. RELEASE TRIGGERS:
   - What triggers the escrow release?
3. AUTO-RELEASE:
   - Is there an auto-release? (Yes / No)
   - If yes, how many days after delivery?
4. DISPUTE HANDLING:
   - Who decides disputes?
   - What is the resolution timeline?
   - What evidence does the buyer/seller need to submit?
5. PROVIDER PROTECTION:
   - Does the platform protect providers from chargebacks? (Yes / No / Partial)
   - Any coverage cap on orders (e.g. max ₹X covered)?
   - What happens to the provider if the buyer disputes unfairly?
   - Make sure to cover other exhaustive scenarios (like shipment delays, return shipping costs, order cancellations, items damaged in transit).
6. KEY INSIGHT FOR SILAAI:
   - What is the single most useful thing Silaai (a custom clothing marketplace in India) should borrow or avoid from this model? Explain why, focusing on custom tailoring and seller risk.
"""

    instruction = f"""Generate a detailed report for the company '{company_name}' in exactly the following structure. Do NOT include markdown blocks around the text, output it directly as plain text matching this template:

ESCROW MODEL
Does it use escrow? (Yes / No / Escrow-like): [Answer here]
Who holds the funds?: [Answer here]
When are funds collected? (Before work / At order / On delivery): [Answer here]
[Provide a short paragraph describing the overall payment flow and mechanism]

RELEASE TRIGGERS
What triggers the escrow release?
- [List specific trigger conditions, events, and API checkpoints]

AUTO-RELEASE
Is there an auto-release? (Yes / No): [Answer here]
If yes, how many days after delivery?: [Answer here]
[Provide any additional details or nuances about the auto-release policy]

DISPUTE HANDLING
Who decides disputes?: [Answer here]
What is the resolution timeline?: [Answer here]
What evidence does the buyer/seller need to submit?: [Answer here]
[Provide details on the step-by-step dispute resolution process]

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): [Answer here]
Any coverage cap on orders (e.g. max ₹X covered)?: [Answer here]
What happens to the provider if the buyer disputes unfairly?: [Answer here]
[Exhaustively cover scenarios such as shipment delays, return shipping costs, order cancellations, and items damaged in transit]

KEY INSIGHT FOR SILAAI
What is the single most useful thing Silaai should borrow or avoid from this model?
- [Detailed insight 1]
- [Detailed insight 2]

SOURCES USED
- [List URLs and references used for the research]
"""

    # Call Gemini research grounding engine (uses google search grounding tools)
    # We call extractor._call_gemini directly to get raw text structured according to the prompt
    prompt = f"{query}\n\n{instruction}"
    
    # We use a custom call with the strong tier to ensure high-quality research with search tools enabled
    try:
        response = extractor._call_gemini(
            contents=prompt,
            config=extractor.types.GenerateContentConfig(
                tools=[extractor.types.Tool(google_search=extractor.types.GoogleSearch())],
                temperature=0.2,
            ),
            tier="strong",
            judgment=True
        )
        report_text = ""
        if response and hasattr(response, 'text') and response.text:
            report_text = response.text.strip()
        elif response and hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts') and candidate.content.parts:
                report_text = "".join([part.text for part in candidate.content.parts if hasattr(part, 'text') and part.text]).strip()
        
        if not report_text:
            raise ValueError(f"Gemini response did not contain text.")

        
        # Append references to sources if present in grounding metadata
        sources = []
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                gm = candidate.grounding_metadata
                if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                    for chunk in gm.grounding_chunks:
                        if hasattr(chunk, 'web') and chunk.web:
                            url = chunk.web.uri
                            if url and url not in sources:
                                sources.append(url)
                                
        if sources:
            source_lines = "\n".join([f"- {url}" for url in sources])
            # Replace placeholder or append to SOURCES USED section
            if "SOURCES USED" in report_text:
                parts = report_text.split("SOURCES USED")
                body = parts[0].strip()
                report_text = f"{body}\n\nSOURCES USED\n{source_lines}"
            else:
                report_text += f"\n\nSOURCES USED\n{source_lines}"
                
        return report_text
    except Exception as e:
        print(f"    [!] Error researching {company_name}: {e}")
        return f"ERROR: Failed to research {company_name} due to: {e}"

def main():
    print("=== STARTING COMPETITOR ESCROW RESEARCH ===")
    api_key = load_keys()
    if not api_key:
        print("[!] Error: No Gemini API keys found in api_keys.txt")
        sys.exit(1)
        
    extractor.configure(api_key)
    print(f"[*] Configured {extractor.get_key_count()} Gemini keys.")
    
    companies = [
        "Etsy",
        "Craftsvilla",
        "Jaypore",
        "Glowroad",
        "Grailed",
        "StockX",
        "Vinted",
        "Depop",
        "Okhai",
        "Meesho"
    ]
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "competitor_research")
    os.makedirs(output_dir, exist_ok=True)
    print(f"[*] Output directory: {output_dir}")
    
    success_count = 0
    for idx, company in enumerate(companies, 1):
        print(f"\n--- Platform {idx}/{len(companies)}: {company} ---")
        report_path = os.path.join(output_dir, f"{company}.txt")
        
        # Check if already exists to prevent duplicate research calls
        if os.path.exists(report_path) and os.path.getsize(report_path) > 200:
            print(f"[*] Report for {company} already exists. Skipping research.")
            success_count += 1
            continue
            
        report_content = research_company(company)
        
        # Write to file
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        print(f"[+] Saved report to {report_path}")
        if not report_content.startswith("ERROR"):
            success_count += 1
            
        # Small cooldown between calls to prevent rate limiting
        time.sleep(2)
        
    print(f"\n=== Research Completed: {success_count}/{len(companies)} reports generated successfully. ===")

if __name__ == "__main__":
    main()
