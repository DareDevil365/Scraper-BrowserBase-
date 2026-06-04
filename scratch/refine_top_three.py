import os
import sys
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import extractor

def load_keys():
    keys = []
    keys_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api_keys.txt")
    if os.path.exists(keys_file):
        with open(keys_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    keys.extend([k.strip() for k in line.split(",") if k.strip()])
    return ",".join(keys)

def research_company_deep(company_name: str, custom_focus: str) -> str:
    print(f"\n[*] Deep Researching {company_name}...")
    
    query = f"""Perform a highly detailed, comprehensive research on the platform '{company_name}' regarding its seller policies, escrow model, payout triggers, dispute resolution, and seller protections.
Specifically, research and cover the following aspects:
{custom_focus}

You must gather precise facts, commission rates, specific timelines (e.g., number of days for returns/payouts), and logistics/RTO details.
"""

    instruction = f"""Generate a comprehensive report for '{company_name}' in exactly the following structure. Do NOT include markdown blocks around the text, output it directly as plain text matching this template:

ESCROW MODEL
Does it use escrow? (Yes / No / Escrow-like): [Answer here]
Who holds the funds?: [Answer here]
When are funds collected? (Before work / At order / On delivery): [Answer here]
[Provide a highly detailed paragraph describing the overall payment flow, transaction cycles, and cash flow mechanism. Explain the role of payment processors or gateways.]

RELEASE TRIGGERS
What triggers the escrow release?
- [List specific trigger conditions, events, and API checkpoints. Detail exactly when the merchant or reseller is paid (e.g., upon shipment tracking activation, delivery confirmation, or expiration of the return window).]

AUTO-RELEASE
Is there an auto-release? (Yes / No): [Answer here]
If yes, how many days after delivery?: [Answer here]
[Detail the auto-release window, including how delivery status via 3PL tracking automatically releases the funds if no dispute is filed. Explain any holding periods for new vs. established sellers.]

DISPUTE HANDLING
Who decides disputes?: [Answer here]
What is the resolution timeline?: [Answer here]
What evidence does the buyer/seller need to submit?: [Answer here]
[Provide a step-by-step breakdown of the dispute process. Detail the exact evidence required (e.g. unboxing videos, photos of measurements against a tape, barcodes, packaging labels) and response windows.]

PROVIDER PROTECTION
Does the platform protect providers from chargebacks? (Yes / No / Partial): [Answer here]
Any coverage cap on orders (e.g. max ₹X covered)?: [Answer here]
What happens to the provider if the buyer disputes unfairly?: [Answer here]
[Exhaustively cover the following scenarios:
- **Shipment delays:** Who is penalized for courier delays? What happens to the payout?
- **Return shipping costs:** Who pays for reverse logistics in case of (a) customer change of mind and (b) merchant error?
- **Order cancellations:** Can custom orders be cancelled after production begins? Who pays for materials?
- **Items damaged in transit:** Who bears the cost if the platform's logistics partner damages the product in transit? Is there insurance?
- **RTO (Return to Origin) for COD:** How is Cash on Delivery handled if the buyer refuses the package at the doorstep? Does the seller pay RTO shipping fees?]

KEY INSIGHT FOR SILAAI
What is the single most useful thing Silaai should borrow or avoid from this model?
- [Detailed, actionable insight 1: Focus on Silaai's custom tailoring and alteration model]
- [Detailed, actionable insight 2: Focus on seller risk mitigation and cash flow optimization for independent tailors in India]

SOURCES USED
- [List specific URLs and references used for the research]
"""

    prompt = f"{query}\n\n{instruction}"
    
    try:
        response = extractor._call_gemini(
            contents=prompt,
            config=extractor.types.GenerateContentConfig(
                tools=[extractor.types.Tool(google_search=extractor.types.GoogleSearch())],
                temperature=0.1,
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
            
        # Append references to sources if present
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
    print("=== STARTING REFINED DEEP COMPLETED RESEARCH FOR TOP THREE ===")
    api_key = load_keys()
    if not api_key:
        print("[!] Error: No Gemini API keys found in api_keys.txt")
        sys.exit(1)
        
    extractor.configure(api_key)
    
    # Craftsvilla Focus
    craftsvilla_focus = """1. Commission rates: Extract historical and actual commission rates (often 20% up to 45% based on categories).
2. Payout terms: Detail the 15-day payment cycle from sale completion.
3. Return and refund policies: Note that customer refunds are often given only as Craftsvilla wallet credits (non-refundable delivery fees), which causes heavy buyer friction.
4. Logistics & Seller protections: Detail how sellers shipped items themselves and faced issues with courier tracking disputes. Explain why high commissions and bad support led to seller migration."""

    # Jaypore Focus
    jaypore_focus = """1. Ownership & Marketplace model: Note that Jaypore is owned by Aditya Birla Fashion and Retail Limited (ABFRL).
2. Made-to-Order / Custom-sized policies: Detail how Jaypore classifies made-to-order and custom-sized garments as non-returnable and non-refundable ('Final Sale'), unless received damaged or incorrect.
3. Damage/Defect reporting window: Must be reported within 48 hours of delivery with photographic evidence showing the product barcode and shipping label.
4. Refund restrictions: COD order refunds are processed as Store Credits only, whereas prepaid orders go to original payment methods."""

    # Glowroad Focus
    glowroad_focus = """1. Commission model: 0% seller commission across categories.
2. Payout structure: Payouts are made after the customer return window (7-10 days after delivery) passes.
3. COD & RTO (Return to Origin): How shipping fees work. Glowroad does NOT charge suppliers shipping/RTO fees if the customer rejects a COD package at delivery. However, suppliers are charged reverse shipping fees for customer returns.
4. Volumetric vs. Dead weight: Shipping charges are calculated based on whichever weight is higher, with tiered benefits (Gold/Silver/Bronze tiers) that reduce shipping fees based on cancellation/return rates."""

    targets = [
        ("Craftsvilla", craftsvilla_focus),
        ("Jaypore", jaypore_focus),
        ("Glowroad", glowroad_focus)
    ]
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "competitor_research")
    os.makedirs(output_dir, exist_ok=True)
    
    for company, focus in targets:
        report_path = os.path.join(output_dir, f"{company}.txt")
        report_content = research_company_deep(company, focus)
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
            
        print(f"[+] Saved deep report to {report_path}")
        time.sleep(2)

if __name__ == "__main__":
    main()
