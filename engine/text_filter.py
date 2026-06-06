"""
text_filter.py — Chunk-Level Relevance Filtering
Splits scraped text into chunks, ranks them via TF-IDF against query keywords,
applies a discovery boost for pricing/logistics keywords, retains the first chunk,
and returns the top-scoring chunks compiled in their original sequential order.
"""
import re
import math

DISCOVERY_KEYWORDS = {
    "rate", "charge", "surcharge", "discount", "slab", "commission", 
    "zone", "api", "limit", "insurance", "cod", "term", "pricing",
    "cost", "fee", "fees", "price", "tariff", "weight", "handling"
}

def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric words."""
    return re.findall(r'[a-z0-9]+', text.lower())

def split_into_chunks(text: str, chunk_size: int = 800, overlap: int = 200) -> list[str]:
    """Split text into overlapping character chunks."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        # Move forward by chunk_size - overlap to keep overlapping content
        start += chunk_size - overlap
    return chunks

def prune_boilerplate_chunks(
    text: str, 
    keywords: list[str], 
    max_chunks: int = 15, 
    chunk_size: int = 800,
    overlap: int = 200
) -> str:
    """
    Split text into chunks, rank them based on TF-IDF relevance to query keywords,
    apply discovery boosts, retain the first chunk, and compile them sequentially.
    """
    if not text or len(text) < chunk_size:
        return text

    chunks = split_into_chunks(text, chunk_size, overlap)
    if len(chunks) <= 1:
        return text

    # Tokenize each chunk and compute term counts
    chunk_tokens = [tokenize(c) for c in chunks]
    num_chunks = len(chunks)
    
    # Vocabulary & Document Frequency (DF)
    df = {}
    for tokens in chunk_tokens:
        seen = set(tokens)
        for token in seen:
            df[token] = df.get(token, 0) + 1

    # Tokenize query keywords
    query_tokens = []
    for kw in keywords:
        query_tokens.extend(tokenize(kw))
    # Deduplicate query tokens
    query_tokens = list(set(query_tokens))

    # Compute TF-IDF score for each chunk
    scored_chunks = []
    for idx, (chunk, tokens) in enumerate(zip(chunks, chunk_tokens)):
        # Calculate term frequency (TF) and TF-IDF
        score = 0.0
        if tokens:
            word_count = len(tokens)
            for qt in query_tokens:
                tf = tokens.count(qt) / word_count
                if tf > 0:
                    # IDF with smoothing
                    idf = math.log(1.0 + (num_chunks / (1.0 + df.get(qt, 0))))
                    score += tf * idf

        # Apply discovery buffer boost
        boost = 0.0
        seen_discovery = set()
        for token in tokens:
            if token in DISCOVERY_KEYWORDS and token not in seen_discovery:
                seen_discovery.add(token)
                boost += 0.05  # 5% boost per unique discovery word found in chunk
        
        # Max boost cap of 0.4
        boost = min(boost, 0.4)
        final_score = score + boost
        
        # Keep track of original index, chunk text, and final score
        scored_chunks.append({
            "index": idx,
            "text": chunk,
            "score": final_score
        })

    # Summary Retention: First chunk (idx 0) is always kept
    first_chunk = scored_chunks[0]
    other_chunks = scored_chunks[1:]
    
    # Sort remaining chunks by score descending
    other_chunks.sort(key=lambda x: x["score"], reverse=True)
    
    # Select top (max_chunks - 1) chunks from the remaining ones
    selected = [first_chunk] + other_chunks[:max_chunks - 1]
    
    # Sort the selected chunks by their original index to preserve document flow
    selected.sort(key=lambda x: x["index"])
    
    # Re-compile the document
    compiled_text = "\n\n... [chunk transition] ...\n\n".join([chunk["text"] for chunk in selected])
    return compiled_text
