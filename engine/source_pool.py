"""
source_pool.py — Thread-safe shared source queue and content accumulators
Deduplicates scraped URLs globally and routes content to blueprint headings.
"""
import heapq
import threading
import json
import os

class SourcePool:
    """
    Thread-safe shared priority queue of URLs to scrape.
    URLs are tagged with ALL relevant blueprint heading IDs.
    Scraped content is accumulated per-heading.
    """
    def __init__(self, blueprint: dict, output_folder: str, vectors: list = None):
        self.queue = []            # list of (-score, url, entry_dict) for heapq
        self.scraped_cache = {}    # url -> content string
        self.extractions = {}      # url -> extraction dict
        self.heading_data = {}     # heading_id -> list of dicts: {"content": ..., "images": ..., "source": ..., "url": ...}
        self.heading_facts = {}    # heading_id -> list of extracted fact dicts
        self.seen_urls = set()
        self.lock = threading.Lock()
        self.blueprint = blueprint
        self.output_folder = output_folder
        self.vectors = vectors or []

        # Initialize heading data structures
        for sec in self.blueprint.get("sections", []):
            sid = sec["id"]
            self.heading_data[sid] = []
            self.heading_facts[sid] = []

    def add_source(self, url: str, title: str, snippet: str, score: float, 
                   source_type: str, relevant_heading_ids: list[str], vector_id: str):
        """Add a URL to the pool, tagged with which headings it serves, if not already seen."""
        with self.lock:
            if url in self.seen_urls:
                # Update headings if this URL serves additional ones
                for item in self.queue:
                    entry = item[2]
                    if entry["url"] == url:
                        for hid in relevant_heading_ids:
                            if hid not in entry["relevant_heading_ids"]:
                                entry["relevant_heading_ids"].append(hid)
                return
            
            self.seen_urls.add(url)
            entry = {
                "url": url,
                "title": title,
                "snippet": snippet,
                "score": score,
                "source_type": source_type,
                "relevant_heading_ids": list(relevant_heading_ids),
                "vector_id": vector_id,
                "scraped": False
            }
            # We push onto a min-heap, so negate the score for a max-priority queue
            heapq.heappush(self.queue, (-score, url, entry))

    def pop_next(self) -> dict or None:
        """Pop the highest-priority unscraped URL entry."""
        with self.lock:
            while self.queue:
                _, _, entry = heapq.heappop(self.queue)
                if not entry["scraped"]:
                    return entry
            return None

    def submit_scraped_content(self, url: str, content: str, images: list, source_entry: dict):
        """
        Called after a scraper finishes. Stores raw content and fans it out
        to all mapped heading accumulators.
        """
        with self.lock:
            self.scraped_cache[url] = content
            source_entry["scraped"] = True

            # Save in queue entries if we still have references to it
            for item in self.queue:
                entry = item[2]
                if entry["url"] == url:
                    entry["scraped"] = True

            for heading_id in source_entry["relevant_heading_ids"]:
                if heading_id not in self.heading_data:
                    self.heading_data[heading_id] = []
                self.heading_data[heading_id].append({
                    "content": content,
                    "images": images,
                    "source": source_entry,
                    "url": url
                })

    def submit_extracted_facts(self, url: str, facts: list[dict], source_entry: dict):
        """Distribute pre-extracted facts to their tagged headings."""
        with self.lock:
            for fact in facts:
                for heading_id in fact.get("heading_ids", []):
                    if heading_id not in self.heading_facts:
                        self.heading_facts[heading_id] = []
                    self.heading_facts[heading_id].append({
                        "fact": fact.get("fact", ""),
                        "data_point": fact.get("data_point"),
                        "source_url": url,
                        "source": source_entry
                    })

    def submit_extraction(self, url: str, extraction: dict):
        """Submit structures/parameters extracted from a scraped page."""
        with self.lock:
            self.extractions[url] = extraction

    def get_heading_status(self, heading_id: str) -> str:
        """Check if a heading has enough successful scraped data sources."""
        data = self.heading_data.get(heading_id, [])
        facts = self.heading_facts.get(heading_id, [])
        successful = [d for d in data if d.get("content") and len(d["content"]) > 100]
        fact_count = len(facts)
        
        # Determine satisfaction target based on vector priorities. Default = 4
        target = 4
        
        # Check blueprint sections to map heading to vector priorities
        section = next((s for s in self.blueprint.get("sections", []) if s["id"] == heading_id), None)
        if section and self.vectors:
            mapped_vector_ids = section.get("mapped_vector_ids", [])
            priorities = []
            for vid in mapped_vector_ids:
                v_obj = next((v for v in self.vectors if v.get("id") == vid), None)
                if v_obj:
                    priorities.append(str(v_obj.get("priority", "medium")).lower())
            
            if priorities:
                if "high" in priorities:
                    target = 6
                elif "medium" in priorities or "standard" in priorities:
                    target = 4
                else: # low priority
                    target = 2
                    
        if fact_count >= 8:
            return "satisfied"
        if len(successful) >= target:
            return "satisfied"
        elif len(successful) >= 1 or fact_count >= 3:
            return "partial"
        return "hungry"

    def get_hungry_headings(self) -> list[str]:
        """Return heading IDs that still need more data."""
        hungry = []
        for sec in self.blueprint.get("sections", []):
            sid = sec["id"]
            if self.get_heading_status(sid) in ("hungry", "partial"):
                hungry.append(sid)
        return hungry

    def serialize_state(self) -> dict:
        """Serialize current state of the source pool for persistence."""
        with self.lock:
            return {
                "seen_urls": list(self.seen_urls),
                "heading_data": {
                    hid: [
                        {
                            "url": item["url"],
                            "source": item["source"],
                            "content_len": len(item["content"]) if item.get("content") else 0,
                            "images": item["images"]
                        }
                        for item in items
                    ]
                    for hid, items in self.heading_data.items()
                },
                "heading_facts": self.heading_facts,
                "extractions": self.extractions
            }
