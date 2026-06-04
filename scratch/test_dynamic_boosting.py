import os
import sys
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import discoverer
from engine import deep_extractor
from engine import extractor

def test_refinement_extraction():
    print("[*] Testing refinement extraction with LLM...")
    # Load keys
    api_key_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api_keys.txt")
    if os.path.exists(api_key_path):
        keys_list = []
        with open(api_key_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    keys_list.extend([k.strip() for k in line.split(",") if k.strip()])
        extractor.configure(",".join(keys_list))
        print(f"[*] Configured {extractor.get_key_count()} keys.")
    else:
        print("[!] No keys found, skipping refinement LLM test.")
        return None

    query = "Setting up escrow payments for a clothing startup in India. Compare Razorpay Escrow, Cashfree, and RBI rules."
    answers = [
        {"question_id": "research_depth", "answer": "Medium Depth"}
    ]
    
    res = discoverer.refine_research_prompt(query, answers)
    assert res["success"] is True, "Refinement failed"
    
    print("\n--- Extracted Authority Domains ---")
    print(json.dumps(res.get("target_authority_domains"), indent=2))
    
    print("\n--- Extracted Required Deliverables ---")
    print(json.dumps(res.get("required_deliverables"), indent=2))
    
    assert len(res.get("target_authority_domains", [])) > 0, "No target domains extracted"
    assert len(res.get("required_deliverables", [])) > 0, "No deliverables checklist extracted"
    
    return res

def test_dynamic_boosting_scoring(refined_plan):
    print("\n[*] Testing dynamic boosting and scoring...")
    if not refined_plan:
        target_domains = ["rbi.org.in", "razorpay.com", "cashfree.com"]
    else:
        target_domains = refined_plan["target_authority_domains"]
        
    print(f"Using target authority domains: {target_domains}")
    
    # Test URLs
    url_target = "https://razorpay.com/blog/escrow-account-india/"
    url_predefined = "https://www.sec.gov/news/press-release"  # Static Tier 2
    url_generic = "https://medium.com/@startupbuilder/how-to-escrow"  # Tier 6
    url_unknown_blog = "https://clothingtechblog.com/payment-gateways"  # Generic blog
    
    # 1. Base quality scoring
    score_target = deep_extractor.score_source_quality(url_target, "Razorpay Escrow Integration", "How to integrate escrow", target_authority_domains=target_domains)
    score_predefined = deep_extractor.score_source_quality(url_predefined, "SEC rules", "regulatory announcements", target_authority_domains=target_domains)
    score_generic = deep_extractor.score_source_quality(url_generic, "How to escrow", "Medium blog", target_authority_domains=target_domains)
    score_unknown_blog = deep_extractor.score_source_quality(url_unknown_blog, "Clothing payments guide", "Generic article", target_authority_domains=target_domains)
    
    print(f"Razorpay (Dynamic Target) Score: {score_target['score']} | Tier: {score_target['tier']} ({score_target['label']})")
    print(f"SEC (Static Predefined T2) Score: {score_predefined['score']} | Tier: {score_predefined['tier']} ({score_predefined['label']})")
    print(f"Medium (Generic T6) Score: {score_generic['score']} | Tier: {score_generic['tier']} ({score_generic['label']})")
    print(f"Unknown Blog (tangential) Score: {score_unknown_blog['score']} | Tier: {score_unknown_blog['tier']} ({score_unknown_blog['label']})")
    
    # Dynamic target should be boosted to Tier 1 (90-100) or Tier 2 (80-89)
    assert score_target["score"] >= 80, "Dynamic target domain was not boosted"
    assert score_target["tier"] in ["TIER_1", "TIER_2"], "Dynamic target domain tier is not T1/T2"
    
    # 2. Ambiguous LLM scoring check (Predefined vs non-predefined domains capping)
    # Simulate batch LLM scoring where LLM returned 90 for all URLs
    mock_sources = [
        {"url": url_target, "title": "Razorpay Escrow", "snippet": "integration docs"},
        {"url": url_unknown_blog, "title": "Payments guide", "snippet": "some blogs"}
    ]
    
    # We mock Gemini batch output response internally or score them directly. 
    # Let's call score_ambiguous_sources_batched with a dummy list.
    # To test capping, we look at the function _is_predefined_domain directly.
    is_target_predefined = deep_extractor._is_predefined_domain(url_target, target_domains)
    is_unknown_predefined = deep_extractor._is_predefined_domain(url_unknown_blog, target_domains)
    
    print(f"Is Razorpay predefined (with target_domains)? {is_target_predefined}")
    print(f"Is Unknown Blog predefined? {is_unknown_predefined}")
    
    assert is_target_predefined is True, "Target domain should be treated as predefined"
    assert is_unknown_predefined is False, "Unknown blog should not be treated as predefined"
    
    # 3. Content aware adjustment checking
    src_target = {"url": url_target, "score": 90, "tier": "TIER_2", "label": "Tier 2"}
    src_unknown_blog = {"url": url_unknown_blog, "score": 50, "tier": "TIER_5", "label": "Tier 5"}
    
    # Successful extraction context
    mock_extraction = {"escrow_pricing": "0.5%", "settlement_cycle": "T+1"}
    
    deep_extractor.adjust_source_tier_by_content(
        src_target, 
        "Detailed Razorpay escrow api pricing document here...", 
        mock_extraction, 
        "escrow pricing",
        target_authority_domains=target_domains
    )
    
    deep_extractor.adjust_source_tier_by_content(
        src_unknown_blog, 
        "General blog talking about payments and pricing...", 
        mock_extraction, 
        "escrow pricing",
        target_authority_domains=target_domains
    )
    
    print(f"Adjusted Target Score: {src_target['score']} | Tier: {src_target['tier']}")
    print(f"Adjusted Unknown Blog Score: {src_unknown_blog['score']} | Tier: {src_unknown_blog['tier']}")
    
    # The target source (Razorpay) is predefined/auth, so it should be allowed to keep a high score (90+)
    assert src_target["score"] > 75, "Target domain was capped at 75 during content adjustment"
    # The unknown blog should be capped at 75 max
    assert src_unknown_blog["score"] <= 75, f"Unknown blog exceeded the 75 cap: {src_unknown_blog['score']}"
    
    print("[+] All scoring and boosting assertions passed successfully!")

if __name__ == "__main__":
    plan = None
    try:
        plan = test_refinement_extraction()
    except Exception as e:
        print(f"[!] Plan extraction test failed: {e}")
        
    test_dynamic_boosting_scoring(plan)
