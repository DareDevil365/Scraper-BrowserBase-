from engine.text_filter import prune_boilerplate_chunks

def test_text_filter():
    # Long text constructed of 4 segments:
    # Segment 1 (idx 0): Header/intro block (must be kept via summary preservation)
    # Segment 2 (idx 1): Relevant topic block (talking about career features, COD and rates)
    # Segment 3 (idx 2): Out of topic block (some terms of service filler text)
    # Segment 4 (idx 3): A pricing rate block containing discovery keywords (surcharge, COD, base rate)
    
    seg1 = "Introduction to Shiprocket Logistics platform. Here we discuss general features of courier services."
    seg2 = "Carrier selection and shipping features. The user query is specifically about carriers and shipping."
    seg3 = "Terms of service and privacy policy website layout columns login details search bars cookies site parameters."
    seg4 = "Pricing details: COD charges are Rs 20, base rate starts at Rs 25, and there is a fuel surcharge."

    # Pad segments to exceed chunk_size (800 chars) if needed, or set chunk_size small to test
    # Let's call prune_boilerplate_chunks with a small chunk size of 100 to force multiple chunks
    full_text = "\n\n".join([seg1, seg2, seg3, seg4])
    
    # Query keywords: carrier, shipping
    keywords = ["carrier", "shipping"]
    
    # Let's prune and allow max 3 chunks
    pruned = prune_boilerplate_chunks(full_text, keywords=keywords, max_chunks=3, chunk_size=120, overlap=20)
    
    print("Pruned Text:\n", pruned)
    
    # Assertions:
    # 1. Segment 1 (index 0 / first chunk) must be preserved
    assert "Shiprocket" in pruned, "First chunk (intro) was not preserved!"
    
    # 2. Segment 2 (relevant to query keywords) must be preserved
    assert "Carrier selection" in pruned or "shipping" in pruned, "Relevant content chunk was not preserved!"
    
    # 3. Segment 4 (contains discovery keywords: base rate, surcharge, COD) must be preserved/boosted
    assert "COD charges" in pruned or "base rate" in pruned, "Discovery boosted pricing chunk was not preserved!"
    
    # 4. Segment 3 (off-topic boilerplate) should be discarded
    assert "privacy policy" not in pruned or "search bars" not in pruned, "Off-topic boilerplate chunk was not discarded!"

    print("\n[PASS] TF-IDF Chunk Filtering and Discovery Buffer test passed successfully!")

if __name__ == "__main__":
    test_text_filter()
