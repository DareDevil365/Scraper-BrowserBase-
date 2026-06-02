"""
deep_extractor.py — Quality-first Universal AI Research Agent.
Discovers sources, ranks them by authority tiers, extracts details,
and integrates YouTube transcript analysis.
"""
import json
import re
import time
import os
import requests
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*duckduckgo_search.*")
from engine import extractor, session_output
from .scraper import fetch_page, _run_async

PERPLEXITY_API_KEY = ""
PERPLEXITY_MODEL = "sonar"

# ── Authority/Quality Tiers ──────────────────────────────────────────

SOURCE_QUALITY_TIERS = {
    "TIER_1": {
        "score_range": (90, 100),
        "name": "Tier 1: Consultancies, Research Firms & Academia",
        "domains": [
            "mckinsey.com", "bcg.com", "bain.com", "deloitte.com", "pwc.com", "ey.com", "kpmg.com",
            "accenture.com", "oliverwyman.com", "rolandberger.com", "gartner.com", "forrester.com",
            "idc.com", "frost.com", "grandviewresearch.com", "mordorintelligence.com",
            "marketsandmarkets.com", "scholar.google.com", "arxiv.org", "pubmed.ncbi.nlm.nih.gov",
            "nature.com", "sciencedirect.com", "springer.com", "ieee.org", "acm.org", "brookings.edu",
            "rand.org", "nber.org", "weforum.org", "hbr.org"
        ],
        "tld_patterns": [".edu", ".ac.uk", ".ac.in"]
    },
    "TIER_2": {
        "score_range": (80, 89),
        "name": "Tier 2: Government, Sector Bodies & Company-Own Sources",
        "domains": [
            "data.gov", "census.gov", "bls.gov", "sec.gov", "rbi.org.in", "sebi.gov.in", "worldbank.org",
            "imf.org", "who.int", "oecd.org", "nasscom.in", "iso.org", "nist.gov"
        ],
        "tld_patterns": [".gov", ".gov.in", ".gov.uk", ".mil"]
    },
    "TIER_3": {
        "score_range": (70, 79),
        "name": "Tier 3: Secondary Research & Data Aggregation",
        "domains": [
            "statista.com", "ourworldindata.org", "tradingeconomics.com", "worldometers.info",
            "g2.com", "trustradius.com", "capterra.com", "crunchbase.com", "pitchbook.com",
            "finance.yahoo.com", "bloomberg.com", "reuters.com", "morningstar.com",
            "stackshare.io", "db-engines.com", "builtwith.com", "similarweb.com"
        ]
    },
    "TIER_4": {
        "score_range": (60, 69),
        "name": "Tier 4: Research Libraries & Repositories",
        "domains": [
            "scribd.com", "academia.edu", "researchgate.net", "ssrn.com", "core.ac.uk",
            "slideshare.net", "issuu.com", "patents.google.com", "kaggle.com", "data.world",
            "w3.org", "rfc-editor.org"
        ]
    },
    "TIER_5": {
        "score_range": (45, 59),
        "name": "Tier 5: Quality Journalism & Expert Content",
        "domains": [
            "techcrunch.com", "arstechnica.com", "theverge.com", "wired.com", "ft.com",
            "economist.com", "wsj.com", "nytimes.com", "bbc.com", "cnbc.com"
        ]
    },
    "TIER_6": {
        "score_range": (10, 44),
        "name": "Tier 6: General Web & Forums",
        "domains": [
            "medium.com", "substack.com", "quora.com", "reddit.com", "twitter.com", "x.com",
            "instagram.com", "facebook.com", "linkedin.com"
        ]
    }
}

BLOCKED_DOMAINS = [
    "pinterest.com", "tiktok.com", "naukri.com", "indeed.com", "ambitionbox.com"
]

JUNK_SOURCE_TERMS = [
    "dictionary", "meaning", "merriam-webster", "cambridge",
    "thefreedictionary", "privacy policy", "account_deletion",
    "login to continue", "travel union", "civitpermit",
]


def source_obviously_junk(src):
    text = f"{src.get('title', '')} {src.get('url', '')} {src.get('snippet', '')}".lower()
    return any(term in text for term in JUNK_SOURCE_TERMS)

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "]+",
    flags=re.UNICODE,
)


def _safe_progress(cb, msg: str):
    """Send progress without allowing console encoding issues to crash research."""
    if not cb:
        return
    try:
        cb(msg)
    except UnicodeEncodeError:
        try:
            cb(_EMOJI_RE.sub("", msg).strip())
        except Exception:
            pass
    except Exception:
        pass


def _sanitize_search_query(query: str) -> str:
    """Keep DuckDuckGo queries simple even if inputs contain search operators."""
    query = re.sub(r'site:\S+', ' ', query)
    query = re.sub(r'\b\w+:\S+', ' ', query)
    query = re.sub(r'\b(?:OR|AND)\b', ' ', query, flags=re.IGNORECASE)
    query = re.sub(r'\d{4}\.\.\d{4}', ' ', query)
    query = re.sub(r'[()"\'`]', ' ', query)
    query = re.sub(r'\s+', ' ', query).strip()
    if len(query) > 150:
        query = query[:150].rsplit(' ', 1)[0]
    return query

def configure_perplexity(api_key: str):
    """Configure Perplexity API key for source discovery."""
    global PERPLEXITY_API_KEY
    PERPLEXITY_API_KEY = api_key
    print(f"    Perplexity API key configured in deep_extractor")

def _build_extraction_prompt(company: str, data_points: list[str], content: str) -> str:
    """Build a dynamic, domain-agnostic prompt to extract custom parameters from scraped page text."""
    dp_list_str = "\n".join([f"- {dp}" for dp in data_points])
    return f"""You are a precise data extraction AI. Extract the requested data points for "{company}" from the web page content below.

DATA POINTS TO EXTRACT:
{dp_list_str}

RULES:
1. Extract exact values, specifications, or descriptions. Use numerical values or precise facts where possible.
2. Return ONLY a valid JSON object where keys are the requested data points (or clean lowercase versions of them) and values are the extracted details.
3. If a data point is not found in the content, set its value to null.
4. If NO requested data is found, return: {{"found": false, "reason": "No relevant data found on this page"}}

PAGE CONTENT:
{content}

Return ONLY valid JSON. No markdown code fences, no explanations."""

def _build_merge_prompt(company: str, data_points: list[str], instruction: str, sources_data: str) -> str:
    """Build a dynamic prompt to merge multiple extracted sources into a single schema-conforming object."""
    dp_list_str = "\n".join([f"- {dp}" for dp in data_points])
    keys_example = ", ".join([f'"{dp.lower().replace(" ", "_")}": ...' for dp in data_points])
    return f"""Merge the research data for "{company}" from multiple sources into ONE unified JSON object.

The final object MUST contain the following data points:
{dp_list_str}

Additional instructions/constraints:
{instruction}

RULES:
- When sources conflict, prefer the most specific, detailed, and recent data.
- Include a "data_confidence" field: "high", "medium", or "low" based on how reliable the sources are.
- The output must be a flat or clean JSON object representing the data points, with "company" set to "{company}".
- Example structure:
  {{
    "company": "{company}",
    {keys_example},
    "data_confidence": "high",
    "data_sources": [...]
  }}

Source data:
{sources_data}

Return ONLY valid JSON. No markdown fences, no explanations."""

# ── Quality Scoring & subject Boost ──────────────────────────────────

def _detect_subject_owned_source(url: str, research_subject: str) -> bool:
    """Returns True if the URL belongs to the entity being researched."""
    if not research_subject:
        return False
    
    url_lower = url.lower()
    subject_clean = re.sub(r'[^a-zA-Z0-9]', '', research_subject.lower())
    if not subject_clean:
        return False
        
    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url_lower)
    if not domain_match:
        return False
    domain = domain_match.group(1)
    
    if subject_clean in domain:
        return True
        
    path_match = re.search(r'https?://(?:www\.)?(?:youtube\.com|x\.com|twitter\.com|instagram\.com|facebook\.com|linkedin\.com)/(?:@)?([^/]+)', url_lower)
    if path_match:
        handle = path_match.group(1)
        if subject_clean in handle.replace("_", "").replace("-", ""):
            return True
            
    return False

def score_source_quality(url: str, title: str, snippet: str, research_subject: str = "", intent: str = "general") -> dict:
    """Scores a URL 0-100 based on domain authority, TLDs, and keyword relevance."""
    url_lower = url.lower()
    title_lower = title.lower() if title else ""
    snippet_lower = snippet.lower() if snippet else ""
    
    for blocked in BLOCKED_DOMAINS:
        if blocked in url_lower:
            return {"score": 0, "tier": "Blocked", "label": "Blocked"}
            
    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url_lower)
    domain = domain_match.group(1) if domain_match else url_lower
    
    base_score = 30
    detected_tier = "TIER_6"
    found_tier = False
    
    for tier_key, tier_info in SOURCE_QUALITY_TIERS.items():
        for d in tier_info.get("domains", []):
            if d in domain or domain.endswith("." + d):
                base_score = (tier_info["score_range"][0] + tier_info["score_range"][1]) // 2
                detected_tier = tier_key
                found_tier = True
                break
        if found_tier:
            break
            
        for pattern in tier_info.get("tld_patterns", []):
            if domain.endswith(pattern):
                base_score = (tier_info["score_range"][0] + tier_info["score_range"][1]) // 2
                detected_tier = tier_key
                found_tier = True
                break
        if found_tier:
            break
            
    if research_subject and _detect_subject_owned_source(url, research_subject):
        base_score = max(base_score, 85)
        detected_tier = "TIER_2"
        
    # Promote social/forums (P4) if intent is sentiment
    if intent == "sentiment":
        if any(forum in url_lower for forum in ["reddit.com", "quora.com", "brainly.", "forum"]):
            base_score = max(base_score, 95)
            detected_tier = "TIER_1"
            
    boost = 0
    for pos_kw in ["report", "whitepaper", "data", "statistics", "analysis", "research", "study", "documentation", "guide", "pricing"]:
        if pos_kw in title_lower or pos_kw in snippet_lower:
            boost += 5
            
    penalty = 0
    for neg_kw in ["opinion", "listicle", "top 10", "top 5", "clickbait", "deals", "discount"]:
        if neg_kw in title_lower or neg_kw in snippet_lower:
            penalty += 10
            
    final_score = min(max(base_score + boost - penalty, 0), 100)
    
    label = "Tier 6: General Web"
    for tier_key, tier_info in SOURCE_QUALITY_TIERS.items():
        min_s, max_s = tier_info["score_range"]
        if min_s <= final_score <= max_s:
            label = tier_info["name"]
            break
            
    return {
        "score": final_score,
        "tier": detected_tier,
        "label": label
    }

# ── YouTube Integration ──────────────────────────────────────────────

def discover_youtube_sources(query: str, max_results: int = 5) -> list[dict]:
    """Use YouTube Data API v3 to search videos if API key is configured."""
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        return []
    
    try:
        from googleapiclient.discovery import build
        youtube = build("youtube", "v3", developerKey=api_key)
        
        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results
        )
        response = request.execute()
        
        video_ids = []
        videos = []
        for item in response.get("items", []):
            vid_id = item.get("id", {}).get("videoId")
            if vid_id:
                video_ids.append(vid_id)
                snippet = item.get("snippet", {})
                videos.append({
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "title": snippet.get("title", ""),
                    "channel": snippet.get("channelTitle", ""),
                    "description": snippet.get("description", ""),
                    "view_count": 0,
                    "id": vid_id
                })
                
        if video_ids:
            stats_request = youtube.videos().list(
                id=",".join(video_ids),
                part="statistics"
            )
            stats_response = stats_request.execute()
            stats_dict = {item["id"]: item.get("statistics", {}).get("viewCount", 0) for item in stats_response.get("items", [])}
            for v in videos:
                v["view_count"] = int(stats_dict.get(v["id"], 0))
                
        return videos
    except Exception as e:
        print(f"    YouTube search failed: {e}")
        return []

def fetch_youtube_transcript(video_url_or_id: str) -> str:
    """Fetch video transcript text using youtube-transcript-api."""
    video_id = video_url_or_id
    if "youtube.com" in video_url_or_id or "youtu.be" in video_url_or_id:
        match = re.search(r'(?:v=|\/)([a-zA-Z0-9_-]{11})', video_url_or_id)
        if match:
            video_id = match.group(1)
            
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item["text"] for item in transcript_list])
    except Exception as e:
        print(f"    Failed to fetch transcript for {video_id}: {e}")
        return ""

# ── Discovery Functions ──────────────────────────────────────────────

def discover_sources_perplexity(company: str, data_points: list[str]) -> list[dict]:
    """Use Perplexity API to find web pages containing data for specific parameters."""
    if not PERPLEXITY_API_KEY:
        return []

    dp_text = ", ".join(data_points) if data_points else "details, features, specifications"
    prompt = f"""Find URLs of web pages that contain specific, detailed data, parameters, or specifications for "{company}".
I need pages showing concrete information for: {dp_text}
Return as a JSON array of objects: [{{"url": "...", "title": "...", "data_available": "..."}}]
Return ONLY the JSON array, no other text or markdown code fences."""

    try:
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": PERPLEXITY_MODEL,
            "messages": [
                {"role": "system", "content": "You find web pages with specific details and specifications. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
        }
        resp = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            parsed = extractor._parse_json_response(content)
            if isinstance(parsed, list):
                return [s for s in parsed if isinstance(s, dict) and s.get("url")]
            citations = resp.json().get("citations", [])
            if citations:
                return [{"url": c, "title": c, "data_available": "Perplexity citation"} for c in citations]
        else:
            print(f"    Perplexity API error: {resp.status_code}")
    except Exception as e:
        print(f"    Perplexity discovery failed: {e}")
    return []

def discover_sources_duckduckgo(company: str, data_points: list[str]) -> list[dict]:
    """Use DuckDuckGo to find relevant pages and rank them by quality score."""
    try:
        from ddgs import DDGS
    except ImportError:
        return []

    dp_queries = []
    if data_points:
        for i in range(0, len(data_points), 2):
            chunk = " ".join(data_points[i:i+2])
            dp_queries.append(f"{company} {chunk}")
    
    queries = [f"{company} details information", f"{company} official site"]
    if dp_queries:
        queries = dp_queries + queries

    results = []
    seen_urls = set()

    with DDGS() as ddgs:
        for q in queries[:4]:
            q = _sanitize_search_query(q)
            if not q:
                continue
            try:
                hits = list(ddgs.text(q, max_results=5))
                for hit in hits:
                    url = hit.get("href", "")
                    if url and url not in seen_urls:
                        url_lower = url.lower()
                        if any(blocked in url_lower for blocked in BLOCKED_DOMAINS):
                            continue
                        seen_urls.add(url)
                        q_info = score_source_quality(url, hit.get("title", ""), hit.get("body", ""), company)
                        results.append({
                            "url": url,
                            "title": hit.get("title", ""),
                            "data_available": hit.get("body", "")[:200],
                            "score": q_info["score"],
                            "tier": q_info["tier"],
                            "label": q_info["label"]
                        })
            except Exception as e:
                print(f"    DuckDuckGo search failed for '{q}': {e}")
                continue

    return sorted(results, key=lambda x: x.get("score", 0), reverse=True)[:10]

# ── Core Vector Research Workflows ───────────────────────────────────

def classify_intent(query: str, context: str = "") -> str:
    """Classifies query intent to determine tier weights. Returns 'market', 'policy', 'sentiment', or 'general'."""
    prompt = f"""Classify the research intent of this query: "{query}" (Context: "{context}").
Choose exactly one category:
- "market": Market sizing, forecasts, industry statistics, corporate pricing.
- "policy": Policy, law, regulation, government guidelines.
- "sentiment": User opinions, reviews, lived experience, customer satisfaction, forum discussions.
- "general": Broad general information or technology comparison.
Return ONLY the category name."""
    try:
        res = extractor._call_gemini(
            contents=prompt,
            tier="cheap",
            judgment=False,
            config=extractor.types.GenerateContentConfig(temperature=0.1)
        )
        category = res.text.strip().lower()
        if category in ["market", "policy", "sentiment", "general"]:
            return category
    except Exception:
        pass
    return "general"


def _check_relevance_overlap(src: dict, query: str) -> bool:
    """Quick keyword overlap check: is this source at least topically related to the query?"""
    query_words = set(w.lower() for w in re.findall(r'\b\w{4,}\b', query)
                      if w.lower() not in {'what', 'with', 'that', 'this', 'from', 'their',
                                           'about', 'everything', 'there', 'between', 'which',
                                           'have', 'been', 'will', 'does', 'more', 'than',
                                           'also', 'into', 'some', 'very', 'each', 'when'})
    if not query_words:
        return True  # can't check, let it through
    src_text = f"{src.get('title', '')} {src.get('snippet', '')} {src.get('url', '')}".lower()
    matches = sum(1 for w in query_words if w in src_text)
    # Require at least 1 query keyword present in title/snippet/url
    return matches >= 1


def _is_predefined_domain(url: str) -> bool:
    """Check if a URL belongs to a predefined authority domain or .gov/.edu TLD."""
    url_lower = url.lower()
    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url_lower)
    domain = domain_match.group(1) if domain_match else url_lower
    for tier_info in SOURCE_QUALITY_TIERS.values():
        for d in tier_info.get("domains", []):
            if d in domain or domain.endswith("." + d):
                return True
        for p in tier_info.get("tld_patterns", []):
            if domain.endswith(p):
                return True
    return False


def score_ambiguous_sources_batched(sources: list[dict], query: str) -> list[dict]:
    """Uses a batched cheap-tier call to evaluate/score the ambiguous middle-band sources.
    Caps LLM scores for non-predefined domains so random sites can never reach Tier 1/2."""
    if not sources:
        return sources
    
    # Layer 1: Pre-filter — remove sources with zero keyword overlap to the query
    filtered_sources = []
    for src in sources:
        if _check_relevance_overlap(src, query):
            filtered_sources.append(src)
        else:
            # No overlap at all → clearly irrelevant, score 0
            src["score"] = 0
            src["tier"] = "Blocked"
            src["label"] = "Blocked (no relevance to query)"
            print(f"      [Pre-filter blocked: {src.get('title', '')[:50]}]")
    
    if not filtered_sources:
        return sources
        
    # Score in batches of 10
    batch_size = 10
    for i in range(0, len(filtered_sources), batch_size):
        batch = filtered_sources[i:i+batch_size]
        
        batch_text = ""
        for idx, src in enumerate(batch):
            batch_text += f"\n{idx+1}. URL: {src['url']}\n   Title: {src.get('title', 'N/A')}\n   Snippet: {src.get('snippet', 'N/A')}\n"
            
        prompt = f"""You are a strict research relevance analyst. The user is researching: "{query}"

Score each search result from 0-100 on how likely it contains actual DATA, facts, or analysis RELEVANT to the research query above.

CRITICAL SCORING RULES:
- Score 0 if the page topic is UNRELATED to the research query (e.g. a product page about faucets/furniture for an escrow research query).
- Score 0-20 for generic pages, dictionaries, login walls, or off-topic content.
- Score 20-50 for tangentially related pages with little specific data.
- Score 50-75 for pages likely containing relevant data, tables, specs, or analysis.
- NEVER score above 75 — the tier system handles authority separately from content relevance.

Results:
{batch_text}

Return ONLY a JSON array:
[
  {{"url": "...", "score": 55, "rationale": "..."}}
]
Return ONLY JSON."""

        try:
            response = extractor._call_gemini(
                contents=prompt,
                tier="cheap",
                judgment=False,
                config=extractor.types.GenerateContentConfig(temperature=0.1)
            )
            parsed = extractor._parse_json_response(response.text)
            if parsed and isinstance(parsed, list):
                score_map = {item.get("url"): (item.get("score"), item.get("rationale")) for item in parsed if item.get("url")}
                for src in batch:
                    url = src["url"]
                    if url in score_map:
                        score, rationale = score_map[url]
                        raw_score = min(max(int(score), 0), 100)
                        # Layer 2: Cap LLM scores for non-predefined domains
                        # Only known authority domains can score above 75
                        if not _is_predefined_domain(url):
                            raw_score = min(raw_score, 75)
                        src["score"] = raw_score
                        src["label"] = _score_to_label(src["score"])
                        src["tier"] = _score_to_tier(src["score"])
        except Exception as e:
            print(f"    [Batch scoring failed for subset: {e}]")
            
    return sources


def _score_to_label(score: int) -> str:
    for tier_key, tier_info in SOURCE_QUALITY_TIERS.items():
        min_s, max_s = tier_info["score_range"]
        if min_s <= score <= max_s:
            return tier_info["name"]
    return "Tier 6: General Web"


def _score_to_tier(score: int) -> str:
    for tier_key, tier_info in SOURCE_QUALITY_TIERS.items():
        min_s, max_s = tier_info["score_range"]
        if min_s <= score <= max_s:
            return tier_key
    return "TIER_6"


def adjust_source_tier_by_content(src: dict, content: str, extraction: dict, topic: str):
    """
    Adjusts the source's score, tier, and label based on the actual scraped content and extraction.
    - If the extraction was highly successful (many non-null parameters extracted), we boost the score.
    - If the content has high keyword overlap/density related to the topic, we boost the score.
    - If the extraction has no actual data points or very low relevance, we penalize the score.
    """
    if not content:
        return
    
    # Calculate extraction richness
    extracted_count = 0
    total_dp = 0
    if isinstance(extraction, dict):
        # Filter out metadata keys
        meta_keys = {"found", "reason", "no_data", "data_confidence", "data_sources", "_source_url"}
        for k, v in extraction.items():
            if k not in meta_keys:
                total_dp += 1
                if v is not None and v != "" and str(v).lower() != "null" and str(v).lower() != "n/a":
                    extracted_count += 1
                    
    # Calculate density of topic keywords in content
    topic_words = set(w.lower() for w in re.findall(r'\b\w{4,}\b', topic)
                      if w.lower() not in {'what', 'with', 'that', 'this', 'from', 'their',
                                           'about', 'everything', 'there', 'between', 'which',
                                           'have', 'been', 'will', 'does', 'more', 'than',
                                           'also', 'into', 'some', 'very', 'each', 'when'})
    
    content_lower = content.lower()
    matches = sum(1 for w in topic_words if w in content_lower) if topic_words else 0
    
    # Base adjustments
    boost = 0
    penalty = 0
    
    # 1. Extraction richness boost/penalty
    if total_dp > 0:
        fill_ratio = extracted_count / total_dp
        if fill_ratio >= 0.75:
            boost += 15  # Found almost all requested data points
        elif fill_ratio >= 0.5:
            boost += 10  # Found half of the data points
        elif fill_ratio == 0:
            penalty += 15  # Found absolutely no requested data points
    
    # 2. Topic keyword matches boost
    if len(topic_words) > 0:
        match_ratio = matches / len(topic_words)
        if match_ratio >= 0.8:
            boost += 10
        elif match_ratio < 0.2:
            penalty += 10
            
    # Apply adjustments
    old_score = src.get("score", 50)
    new_score = old_score + boost - penalty
    
    # Clamp score
    # Note: Only known authority domains (predefined/subject-owned) can exceed 75. 
    is_auth = False
    url = src.get("url", "")
    if _is_predefined_domain(url) or _detect_subject_owned_source(url, topic):
        is_auth = True
        
    max_cap = 100 if is_auth else 75
    new_score = min(max(new_score, 10), max_cap)
    
    # Update score, tier, and label
    src["score"] = new_score
    src["tier"] = _score_to_tier(new_score)
    src["label"] = _score_to_label(new_score)
    
    print(f"      [Content-aware tiering] {src.get('url')[:40]}: score {old_score} -> {new_score} ({src['tier']})")


def apply_diversity_and_anti_echo_chamber(sources: list[dict], domain_cap: int = 5, research_subject: str = "") -> list[dict]:
    """Applies domain caps to limit the number of pages from a single domain.
    Tier 1/2 domains and subject-owned sources get a higher cap."""
    domain_counts = {}
    filtered_sources = []
    for src in sources:
        url = src.get("url", "")
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url.lower())
        domain = domain_match.group(1) if domain_match else url
        
        # Higher cap for authority and subject-owned sources
        tier = src.get("tier", "TIER_6")
        effective_cap = domain_cap
        if tier in ("TIER_1", "TIER_2") or _detect_subject_owned_source(url, research_subject):
            effective_cap = domain_cap + 3  # e.g. 8 for default cap=5
        
        count = domain_counts.get(domain, 0)
        if count < effective_cap:
            domain_counts[domain] = count + 1
            filtered_sources.append(src)
            
    return filtered_sources


def discover_sources_for_session(
    session_id: str,
    vectors: list[dict],
    refined_prompt: str,
    original_query: str,
    depth: str = "standard",
    output_folder: str = "",
    progress_cb=None
):
    """
    Stage 2 Source Discovery & Prioritization.
    """
    if progress_cb:
        progress_cb("Classifying research intent...")
        
    intent = classify_intent(original_query, refined_prompt)
    print(f"    Detected intent: {intent}")
    
    all_discovered = []
    seen_urls = set()
    
    for idx, vector in enumerate(vectors):
        topic = vector.get("topic", "")
        desc = vector.get("description", "")
        hints = vector.get("search_hints", [])
        vector_id = vector.get("id") or f"v_{idx+1}"
        
        if progress_cb:
            progress_cb(f"Discovering sources for vector '{topic}'...")
            
        # Scale search queries by depth
        from engine import discoverer
        queries = discoverer.generate_search_queries(vector, refined_prompt, depth)
        
        queries_to_run = queries
        vector_sources = []
        
        # Inject curated carrier URLs if matched
        try:
            from engine.sources_db import COMPANY_SOURCES, get_tiered_urls
            matched_carriers = []
            text_to_check = f"{topic} {desc} {original_query}".lower()
            for c_key, c_data in COMPANY_SOURCES.items():
                c_name = c_data["name"].lower()
                if re.search(r'\b' + re.escape(c_key) + r'\b', text_to_check) or re.search(r'\b' + re.escape(c_name) + r'\b', text_to_check):
                    matched_carriers.append(c_key)

            for c_key in matched_carriers:
                tiered_urls = get_tiered_urls(c_key)
                # Tier 2 consultancy (richest in compiled rates)
                for url in tiered_urls.get("tier_2", []):
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        vector_sources.append({
                            "url": url,
                            "title": f"Curated Blog: {c_key.title()}",
                            "snippet": f"Curated high-value carrier rates compiled article for {c_key.title()}.",
                            "source_type": "curated",
                            "vector_id": vector_id,
                            "score": 95,
                            "tier": "TIER_2",
                            "label": f"Curated Blog: {c_key.title()}"
                        })
                # Tier 1 official
                for url in tiered_urls.get("tier_1", []):
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        vector_sources.append({
                            "url": url,
                            "title": f"Curated Official: {c_key.title()}",
                            "snippet": f"Curated official website portal/page for {c_key.title()}.",
                            "source_type": "curated",
                            "vector_id": vector_id,
                            "score": 92,
                            "tier": "TIER_2",
                            "label": f"Curated Official: {c_key.title()}"
                        })
                # Tier 3 sector
                for url in tiered_urls.get("tier_3", []):
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        vector_sources.append({
                            "url": url,
                            "title": f"Curated Sector Report: {c_key.title()}",
                            "snippet": f"Curated sector intelligence report or PDF for {c_key.title()}.",
                            "source_type": "curated",
                            "vector_id": vector_id,
                            "score": 80,
                            "tier": "TIER_3",
                            "label": f"Curated Sector: {c_key.title()}"
                        })
                # Tier 4 library
                for url in tiered_urls.get("tier_4", []):
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        vector_sources.append({
                            "url": url,
                            "title": f"Curated Calculator: {c_key.title()}",
                            "snippet": f"Curated comparison/calculator tool link for {c_key.title()}.",
                            "source_type": "curated",
                            "vector_id": vector_id,
                            "score": 75,
                            "tier": "TIER_4",
                            "label": f"Curated Library: {c_key.title()}"
                        })
        except Exception as e:
            print(f"      Curated source injection failed for {topic}: {e}")

        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                for q in queries_to_run:
                    q = _sanitize_search_query(q)
                    if not q:
                        continue
                    try:
                        ddg_max = 5 if depth == "surface" else (10 if depth == "standard" else 12)
                        hits = list(ddgs.text(q, max_results=ddg_max))
                        for hit in hits:
                            url = hit.get("href", "")
                            if url and url not in seen_urls:
                                if any(blocked in url.lower() for blocked in BLOCKED_DOMAINS):
                                    continue
                                seen_urls.add(url)
                                vector_sources.append({
                                    "url": url,
                                    "title": hit.get("title", ""),
                                    "snippet": hit.get("body", ""),
                                    "source_type": "web",
                                    "vector_id": vector_id
                                })
                    except Exception as e:
                        print(f"      Search failed for '{q}': {e}")
        except Exception as e:
            print(f"    DDG search module failure: {e}")
            
        # YouTube
        yt_query = f"{topic} " + " ".join(hints[:2])
        yt_results = discover_youtube_sources(yt_query, max_results=3)
        for yt in yt_results:
            url = yt["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                vector_sources.append({
                    "url": url,
                    "title": yt["title"],
                    "snippet": yt["description"],
                    "source_type": "youtube",
                    "channel": yt["channel"],
                    "view_count": yt["view_count"],
                    "vector_id": vector_id
                })
                
        # Perplexity
        if PERPLEXITY_API_KEY:
            try:
                perp_res = discover_sources_perplexity(topic, hints)
                for ps in perp_res:
                    url = ps.get("url")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        vector_sources.append({
                            "url": url,
                            "title": ps.get("title", ""),
                            "snippet": ps.get("data_available", ""),
                            "source_type": "perplexity",
                            "vector_id": vector_id
                        })
            except Exception as e:
                print(f"    Perplexity discovery error: {e}")
                
        all_discovered.extend(vector_sources)

    if progress_cb:
        progress_cb("Scoring and filtering discovered sources...")
        
    clear_cut_sources = []
    ambiguous_sources = []
    
    all_predefined_domains = []
    for tier_info in SOURCE_QUALITY_TIERS.values():
        all_predefined_domains.extend(tier_info.get("domains", []))
        
    for src in all_discovered:
        url_lower = src["url"].lower()
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url_lower)
        domain = domain_match.group(1) if domain_match else url_lower
        
        q_info = score_source_quality(src["url"], src.get("title"), src.get("snippet"), original_query, intent)
        src.update(q_info)
        score = src.get("score", 0)
        
        is_predefined = any(d in domain or domain.endswith("." + d) for d in all_predefined_domains)
        is_gov_edu = any(domain.endswith(p) for p in [".gov", ".edu", ".mil", ".gov.uk", ".gov.in"])
        
        if is_predefined or is_gov_edu or _detect_subject_owned_source(src["url"], original_query):
            clear_cut_sources.append(src)
        elif score < 40 or score == 0:
            clear_cut_sources.append(src)
        else:
            ambiguous_sources.append(src)
            
    if ambiguous_sources:
        ambiguous_sources = sorted(ambiguous_sources, key=lambda x: x.get("score", 0), reverse=True)
        sources_to_llm_score = ambiguous_sources[:15]
        remaining_ambiguous = ambiguous_sources[15:]
        
        if progress_cb:
            progress_cb(f"Evaluating {len(sources_to_llm_score)} ambiguous sources via AI...")
        scored_ambiguous = score_ambiguous_sources_batched(sources_to_llm_score, original_query)
        all_scored = clear_cut_sources + scored_ambiguous + remaining_ambiguous
    else:
        all_scored = clear_cut_sources
        
    all_scored = [s for s in all_scored if s.get("score", 0) > 0]
    all_scored = apply_diversity_and_anti_echo_chamber(all_scored, domain_cap=5, research_subject=original_query)
    all_scored = sorted(all_scored, key=lambda x: x.get("score", 0), reverse=True)
    
    if output_folder:
        queue_path = os.path.join(output_folder, "scrape_queue.json")
        try:
            with open(queue_path, "w", encoding="utf-8") as f:
                json.dump(all_scored, f, indent=2, default=str)
            print(f"    Wrote ranked scrape queue to {queue_path}")
        except Exception as e:
            print(f"    Failed to write scrape queue to file: {e}")
            
    return all_scored


def validate_page_entity(title: str, url: str, content: str, subject: str) -> dict:
    """
    Performs pre-scrape entity and soft-404 validation.
    """
    url_lower = url.lower()
    title_lower = title.lower() if title else ""
    content_lower = content.lower() if content else ""
    
    # Soft-404 check
    soft_404_keywords = [
        "page not found", "404 - file or directory not found", 
        "404 error", "404 not found", "error 404"
    ]
    if any(kw in title_lower or kw in content_lower[:1000] for kw in soft_404_keywords):
        return {"valid": False, "reason": "SOFT_404"}
        
    # Mismatch validation (drift guard) using Gemini (Strong/Mid judgment)
    if subject:
        # Pre-filter using high-performance local keyword rules
        subject_words = [w for w in re.findall(r'\b\w+\b', subject.lower()) if len(w) > 3 and w not in {"with", "that", "this", "from", "their", "about", "everything", "there", "what"}]
        content_sample = (title_lower + " " + url_lower + " " + content_lower[:2500]).lower()
        
        if subject_words:
            matches = sum(1 for w in subject_words if w in content_sample)
            min_matches = min(2, len(subject_words))
            if matches >= min_matches:
                # Strong keyword match, approve instantly to conserve API quota
                return {"valid": True, "reason": "SUCCESS"}
            if matches == 0:
                # Zero matching keywords, reject instantly
                return {"valid": False, "reason": "NOT_APPLICABLE (local keyword mismatch)"}
                
        # Check key pool status. If all cells are exhausted or cooling down, bypass the LLM gatekeeper
        import time
        from engine import extractor
        has_active_cell = False
        for state in extractor._cell_states.values():
            if not state.get("exhausted_today", False) and state.get("cooldown_until", 0) <= time.time():
                has_active_cell = True
                break
                
        if not has_active_cell:
            # Bypass LLM when keys are rate-limited or exhausted
            return {"valid": True, "reason": "SUCCESS"}

        if not extractor._clients:
            subject_clean = re.sub(r'[^a-zA-Z0-9]', '', subject.lower())
            if "recruit" in url_lower or "recruit" in title_lower:
                if "recruit" not in subject_clean:
                    return {"valid": False, "reason": "NOT_APPLICABLE"}
            return {"valid": True, "reason": "SUCCESS"}
            
        snippet = content_lower[:3000]
        prompt = f"""You are a research gatekeeper checking if a web page matches the target entity and scope.
        
Target Entity/Scope being researched: "{subject}"

Web Page Details:
URL: {url}
Title: {title}
Snippet of content:
{snippet}

Evaluate if this web page:
1. Belongs to a different entity (e.g., same name but completely different company/product, or generic top-level search portal, dictionary/translation page).
2. Is completely out of scope or irrelevant to the target research (e.g., wrong geography, wrong business model).
3. Is a generic login page, placeholder, or empty shell.

Return a JSON object matching this schema:
{{
  "valid": true/false,
  "reason": "SUCCESS" or "NOT_APPLICABLE (entity mismatch/drift: explanation)" or "SOFT_404"
}}
Return ONLY valid JSON. Do not include markdown blocks or other wrapper text."""

        try:
            response = extractor._call_gemini(
                contents=prompt,
                tier="cheap",
                judgment=False,
                config=extractor.types.GenerateContentConfig(temperature=0.1)
            )
            parsed = extractor._parse_json_response(response.text)
            if parsed and isinstance(parsed, dict):
                return {
                    "valid": parsed.get("valid", True),
                    "reason": parsed.get("reason", "SUCCESS")
                }
        except Exception as e:
            print(f"      Entity validation LLM call failed: {e}")
            
    return {"valid": True, "reason": "SUCCESS"}


def _compute_tf(text: str) -> dict:
    words = re.findall(r'\b\w+\b', text.lower())
    tf = {}
    for w in words:
        if len(w) > 2:  # skip tiny stop words
            tf[w] = tf.get(w, 0) + 1
    return tf


def check_saturation(new_content: str, corpus_so_far: list[str]) -> float:
    """
    Estimates the rate of new information added by new_content compared to the corpus_so_far.
    Uses a high-performance local term-frequency cosine similarity heuristic to conserve Gemini API quota.
    Returns a score from 0.0 (completely redundant/already covered) to 1.0 (contains completely new facts/aspects).
    """
    if not corpus_so_far:
        return 1.0
        
    # Build term frequencies for the new content (up to 3000 chars)
    new_tf = _compute_tf(new_content[:3000])
    if not new_tf:
        return 0.0
        
    # Aggregate term frequencies for the corpus (last 4 documents)
    corpus_tf = {}
    for doc in corpus_so_far[-4:]:
        doc_tf = _compute_tf(doc[:3000])
        for w, count in doc_tf.items():
            corpus_tf[w] = corpus_tf.get(w, 0) + count
            
    # Calculate cosine similarity between new_tf and corpus_tf vectors
    intersection = set(new_tf.keys()) & set(corpus_tf.keys())
    
    dot_product = sum(new_tf[w] * corpus_tf[w] for w in intersection)
    
    magnitude_new = sum(val ** 2 for val in new_tf.values()) ** 0.5
    magnitude_corpus = sum(val ** 2 for val in corpus_tf.values()) ** 0.5
    
    if magnitude_new == 0 or magnitude_corpus == 0:
        return 1.0
        
    similarity = dot_product / (magnitude_new * magnitude_corpus)
    
    # Information novelty is inversely proportional to similarity
    novelty = 1.0 - similarity
    
    return max(0.0, min(1.0, novelty))


def deep_research_vector(
    vector: dict,
    research_context: str = "",
    instruction: str = "",
    max_scrape: int = 3,
    progress_cb=None,
    output_folder: str = "",
    depth: str = "standard"
) -> dict:
    """Researches a single sub-topic/vector, scraping the best sources and extracting details."""
    topic = vector.get("topic", "")
    desc = vector.get("description", "")
    hints = vector.get("search_hints", [])
    v_data_points = vector.get("data_points") or hints
    vector_id = vector.get("id") or topic
    vector_scope = f"{topic}. {desc}. Overall task: {research_context}"
    
    _safe_progress(progress_cb, f"🚀 Researching vector: '{topic}'")
    
    scrape_urls = []
    if output_folder:
        queue_path = os.path.join(output_folder, "scrape_queue.json")
        if os.path.exists(queue_path):
            try:
                with open(queue_path, "r", encoding="utf-8") as f:
                    all_sources = json.load(f)
                scrape_urls = [
                    s for s in all_sources
                    if s.get("vector_id") == vector_id and not source_obviously_junk(s)
                ]
            except Exception as e:
                print(f"    Failed to read scrape queue: {e}")
                
    if not scrape_urls:
        _safe_progress(progress_cb, f"    [Queue empty, falling back to discovery for '{topic}']")
        from engine import discoverer
        queries = discoverer.generate_search_queries(vector, research_context, depth)
        all_discovered = []
        seen_urls = set()
        
        queries_to_run = queries
        ddg_max = 10
        if depth == "surface":
            queries_to_run = queries[:2]
            ddg_max = 5
        elif depth == "deep":
            ddg_max = 12
            
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                for q in queries_to_run:
                    q = _sanitize_search_query(q)
                    if not q:
                        continue
                    try:
                        hits = list(ddgs.text(q, max_results=ddg_max))
                        for hit in hits:
                            url = hit.get("href", "")
                            if url and url not in seen_urls:
                                if any(blocked in url.lower() for blocked in BLOCKED_DOMAINS):
                                    continue
                                seen_urls.add(url)
                                all_discovered.append({
                                    "url": url,
                                    "title": hit.get("title", ""),
                                    "snippet": hit.get("body", ""),
                                    "source_type": "web",
                                    "vector_id": vector_id
                                })
                    except Exception as e:
                        print(f"      Search failed for '{q}': {e}")
        except Exception as e:
            print(f"    DDG search module failure: {e}")
            
        yt_query = f"{topic} " + " ".join(hints[:2])
        yt_sources = discover_youtube_sources(yt_query, max_results=3)
        for yt in yt_sources:
            url = yt["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                all_discovered.append({
                    "url": url,
                    "title": yt["title"],
                    "snippet": yt["description"],
                    "source_type": "youtube",
                    "channel": yt["channel"],
                    "view_count": yt["view_count"],
                    "vector_id": vector_id
                })
                
        for src in all_discovered:
            q_info = score_source_quality(src["url"], src["title"], src["snippet"], research_context)
            src.update(q_info)
            
        all_discovered = [s for s in all_discovered if s.get("score", 0) > 0]
        scrape_urls = sorted(all_discovered, key=lambda x: x.get("score", 0), reverse=True)[:max_scrape]
        scrape_urls = [s for s in scrape_urls if not source_obviously_junk(s)]

    scrape_urls = scrape_urls[:max_scrape]
    page_extractions = []
    sources_used = []
    scraped_texts = []
    
    consecutive_low_info_count = 0
    if depth == "surface":
        saturation_limit_k = 2
        saturation_threshold = 0.20
    elif depth == "standard":
        saturation_limit_k = 4
        saturation_threshold = 0.12
    else: # deep
        saturation_limit_k = 6
        saturation_threshold = 0.08
    
    for src in scrape_urls:
        url = src["url"]
        
        if src.get("source_type") == "youtube" or "youtube.com" in url or "youtu.be" in url:
            transcript = fetch_youtube_transcript(url)
            if transcript:
                _safe_progress(progress_cb, f"📺 Extracting from YouTube transcript: {_shorten_url(url)}")
                val = validate_page_entity(src.get("title", ""), url, transcript, vector_scope)
                if not val["valid"]:
                    _safe_progress(progress_cb, f"    [Skipped source: {val['reason']}]")
                    src["had_data"] = False
                    src["status"] = val["reason"]
                    sources_used.append(src)
                    session_output.update_sources_ledger_entry(output_folder, url, val["reason"], False, src)
                    session_output.append_failure(output_folder, url, src.get("tier", "TIER_6"), val["reason"], "Skipped due to validation")
                    continue
                    
                res = extractor.extract_from_transcript(transcript, topic, v_data_points)
                if res.get("success"):
                    page_extractions.append({
                        "data": res.get("data", {}),
                        "key_findings": res.get("key_points", []),
                        "_source_url": url
                    })
                    info_rate = check_saturation(transcript, scraped_texts)
                    scraped_texts.append(transcript)
                    print(f"      Information rate for {url}: {info_rate:.2f}")
                    
                    # Content-aware tiering adjustment
                    adjust_source_tier_by_content(src, transcript, res.get("data", {}), topic)
                    
                    src["had_data"] = True
                    src["status"] = "SUCCESS"
                    sources_used.append(src)
                    session_output.update_sources_ledger_entry(output_folder, url, "SUCCESS", True, src)
                    session_output.append_raw_research(output_folder, url, src.get("tier", "TIER_6"), src.get("label", "YouTube Transcript"), transcript)
                    
                    if info_rate < saturation_threshold:
                        consecutive_low_info_count += 1
                    else:
                        consecutive_low_info_count = 0
                        
                    if consecutive_low_info_count >= saturation_limit_k:
                        _safe_progress(progress_cb, "🛑 Saturation detected (no new information). Stopping vector scraping.")
                        break
                else:
                    src["had_data"] = False
                    src["status"] = "NO_PUBLIC_DATA"
                    sources_used.append(src)
                    session_output.update_sources_ledger_entry(output_folder, url, "NO_PUBLIC_DATA", False, src)
            else:
                src["had_data"] = False
                src["status"] = "FAILED"
                sources_used.append(src)
                session_output.update_sources_ledger_entry(output_folder, url, "FAILED", False, src)
                session_output.append_failure(output_folder, url, src.get("tier", "TIER_6"), "Transcript fetch returned empty", "Marked as FAILED")
            continue
                
        try:
            _safe_progress(progress_cb, f"📄 Scraping ({src.get('score', 50)} pts): {_shorten_url(url)}")
            page = _run_async(fetch_page(url, timeout=20000))
            if page["success"] and page["markdown"] and len(page["markdown"]) > 100:
                markdown_content = page["markdown"]
                
                val = validate_page_entity(page.get("title", ""), url, markdown_content, vector_scope)
                if not val["valid"]:
                    _safe_progress(progress_cb, f"    [Skipped source: {val['reason']}]")
                    src["had_data"] = False
                    src["status"] = val["reason"]
                    sources_used.append(src)
                    session_output.update_sources_ledger_entry(output_folder, url, val["reason"], False, src)
                    session_output.append_failure(output_folder, url, src.get("tier", "TIER_6"), val["reason"], "Skipped due to validation")
                    continue
                    
                extraction = _extract_prices_from_page(markdown_content, topic, v_data_points, instruction)
                if extraction and not extraction.get("no_data") and not (isinstance(extraction, dict) and extraction.get("found") is False):
                    extraction["_source_url"] = url
                    page_extractions.append(extraction)
                    info_rate = check_saturation(markdown_content, scraped_texts)
                    scraped_texts.append(markdown_content)
                    print(f"      Information rate for {url}: {info_rate:.2f}")
                    
                    # Content-aware tiering adjustment
                    adjust_source_tier_by_content(src, markdown_content, extraction, topic)
                    
                    src["had_data"] = True
                    src["status"] = "SUCCESS"
                    sources_used.append(src)
                    session_output.update_sources_ledger_entry(output_folder, url, "SUCCESS", True, src)
                    session_output.append_raw_research(output_folder, url, src.get("tier", "TIER_6"), src.get("label", "Web Page Scraped"), markdown_content)
                    
                    if info_rate < saturation_threshold:
                        consecutive_low_info_count += 1
                    else:
                        consecutive_low_info_count = 0
                        
                    if consecutive_low_info_count >= saturation_limit_k:
                        _safe_progress(progress_cb, "🛑 Saturation detected (no new information). Stopping vector scraping.")
                        break
                else:
                    src["had_data"] = False
                    src["status"] = "NO_PUBLIC_DATA"
                    sources_used.append(src)
                    session_output.update_sources_ledger_entry(output_folder, url, "NO_PUBLIC_DATA", False, src)
            else:
                src["had_data"] = False
                src["status"] = "FAILED"
                sources_used.append(src)
                err_msg = page.get("error") or "No content or too short"
                session_output.update_sources_ledger_entry(output_folder, url, "FAILED", False, src)
                session_output.append_failure(output_folder, url, src.get("tier", "TIER_6"), err_msg, "Marked as FAILED")
        except Exception as e:
            print(f"      Scrape failed for {url}: {e}")
            src["had_data"] = False
            src["status"] = "FAILED"
            sources_used.append(src)
            session_output.update_sources_ledger_entry(output_folder, url, "FAILED", False, src)
            session_output.append_failure(output_folder, url, src.get("tier", "TIER_6"), str(e), "Marked as FAILED due to exception")
            
    # Scale grounded research skip threshold by depth
    skip_grounded = False
    if depth == "surface" and len(page_extractions) >= 4:
        skip_grounded = True
    elif depth == "standard" and len(page_extractions) >= 6:
        skip_grounded = True
        
    if skip_grounded:
        _safe_progress(progress_cb, f"\u2705 Sufficient data from scraping ({len(page_extractions)} sources). Skipping grounded research.")
        ai_research = {"data": None, "grounding_sources": []}
    else:
        _safe_progress(progress_cb, f"\U0001F310 Running AI grounding research on '{topic}'...")
        ai_research = _gemini_grounded_research(topic, v_data_points, instruction)
    ai_data = ai_research.get("data")
    ai_sources = ai_research.get("grounding_sources", [])
    
    for asrc in ai_sources:
        url = asrc.get("url") or asrc.get("uri")
        if url:
            q_info = score_source_quality(url, asrc.get("title", ""), "", research_context)
            src_entry = {
                "url": url,
                "title": asrc.get("title") or url,
                "score": q_info["score"],
                "tier": q_info["tier"],
                "label": q_info["label"],
                "status": "SUCCESS",
                "had_data": True,
                "vector_id": vector_id
            }
            sources_used.append(src_entry)
            session_output.update_sources_ledger_entry(output_folder, url, "SUCCESS", True, src_entry)
            snippet_text = asrc.get("snippet", "") or asrc.get("title", "")
            session_output.append_raw_research(output_folder, url, q_info["tier"], q_info["label"], snippet_text)
            
    _safe_progress(progress_cb, f"\U0001F9E0 Synthesizing findings for '{topic}'...")
    merged_findings = _merge_company_data(topic, ai_data, page_extractions, v_data_points, instruction)
    
    unique_sources = []
    seen_used_urls = set()
    for s in sources_used:
        if s["url"] not in seen_used_urls:
            seen_used_urls.add(s["url"])
            unique_sources.append(s)
            
    res_payload = {
        "vector": vector,
        "data": merged_findings,
        "sources": unique_sources,
        "pages_scraped": len(scrape_urls),
        "success": merged_findings is not None,
        "error": None if merged_findings else f"No data found for vector: {topic}"
    }

    if output_folder:
        try:
            session_output.save_extracted_vector(output_folder, vector_id, res_payload)
            session_output.write_sources_log_csv(output_folder, unique_sources, research_context)
        except Exception as e:
            print(f"    Failed to save extracted vector: {e}")
            
    return res_payload

def deep_research_company(
    company: str,
    data_points: list[str],
    instruction: str = "",
    max_scrape: int = 8,
    progress_cb=None
) -> dict:
    """Legacy company-focused research with tier scoring."""
    # Check if company is non-operational or not applicable in India
    try:
        from engine.sources_db import NON_OPERATIONAL_REASONS
        company_clean = company.lower().strip()
        matched_reason = None
        for k, reason in NON_OPERATIONAL_REASONS.items():
            if k == company_clean or k in company_clean or company_clean in k:
                matched_reason = reason
                break
                
        if matched_reason:
            _safe_progress(progress_cb, f"ℹ Skipping research for {company}: {matched_reason}")
            return {
                "company": company,
                "data": {
                    "pricing_rate_card": matched_reason,
                    "cod_charges": "N/A",
                    "volume_discounts": "N/A",
                    "other_charges": "N/A",
                    "eta_delivery_time": "N/A",
                    "non_operational": True,
                    "reason": matched_reason
                },
                "sources": [],
                "sources_tried": [],
                "pages_scraped": 0,
                "pages_with_data": 0,
                "perplexity_sources": 0,
                "success": True,
                "error": None
            }
    except Exception as e:
        print(f"    Non-operational check failed for {company}: {e}")

    all_urls = []
    discovered_sources = []
    sources_tried = []

    _safe_progress(progress_cb, f"🔍 Discovering sources for {company}...")
    ddg_sources = discover_sources_duckduckgo(company, data_points)
    discovered_sources.extend(ddg_sources)

    perp_sources = discover_sources_perplexity(company, data_points)
    discovered_sources.extend(perp_sources)

    for s in discovered_sources:
        url = s.get("url", "")
        if url and url not in all_urls:
            all_urls.append(url)

    gemini_result = _gemini_grounded_research(company, data_points, instruction)
    gemini_data = gemini_result.get("data")
    gemini_sources = gemini_result.get("grounding_sources", [])

    for s in gemini_sources:
        url = s.get("url", s.get("uri", ""))
        if url and url not in all_urls:
            all_urls.append(url)

    scrape_urls = _prioritize_urls(all_urls, max_scrape)
    page_extractions = []
    scrape_results = []

    for url in scrape_urls:
        source_record = {"url": url, "success": False, "error": None, "had_data": False}
        try:
            page = _run_async(fetch_page(url, timeout=20000))
            if page["success"] and page["markdown"] and len(page["markdown"]) > 100:
                source_record["success"] = True
                source_record["title"] = page.get("title", "")
                source_record["content_length"] = len(page["markdown"])

                extraction = _extract_prices_from_page(page["markdown"], company, data_points, instruction)
                if extraction and not extraction.get("no_data") and not (isinstance(extraction, dict) and extraction.get("found") is False):
                    extraction["_source_url"] = url
                    page_extractions.append(extraction)
                    source_record["had_data"] = True
            else:
                source_record["error"] = page.get("error", "No content")
        except Exception as e:
            source_record["error"] = str(e)

        sources_tried.append(source_record)
        scrape_results.append(source_record)

    final_data = _merge_company_data(company, gemini_data, page_extractions, data_points, instruction)

    all_source_info = []
    seen_urls = set()
    
    for s in gemini_sources:
        url = s.get("url") or s.get("uri")
        if url and url not in seen_urls:
            seen_urls.add(url)
            q_info = score_source_quality(url, s.get("title", ""), "", company)
            all_source_info.append({
                "url": url,
                "title": s.get("title") or url,
                "score": q_info["score"],
                "tier": q_info["tier"],
                "label": q_info["label"]
            })
            
    for s in discovered_sources:
        url = s.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            q_info = score_source_quality(url, s.get("title", ""), s.get("data_available", ""), company)
            all_source_info.append({
                "url": url,
                "title": s.get("title") or url,
                "score": q_info["score"],
                "tier": q_info["tier"],
                "label": q_info["label"]
            })
            
    for sr in scrape_results:
        url = sr["url"]
        if sr.get("success") and url not in seen_urls:
            seen_urls.add(url)
            q_info = score_source_quality(url, sr.get("title", ""), "", company)
            all_source_info.append({
                "url": url,
                "title": sr.get("title") or url,
                "score": q_info["score"],
                "tier": q_info["tier"],
                "label": q_info["label"]
            })
            
    all_source_info = sorted(all_source_info, key=lambda x: x.get("score", 0), reverse=True)

    return {
        "company": company,
        "data": final_data,
        "sources": all_source_info,
        "sources_tried": sources_tried,
        "pages_scraped": len([s for s in scrape_results if s.get("success")]),
        "pages_with_data": len(page_extractions),
        "perplexity_sources": len([s for s in discovered_sources if "perplexity" in s.get("data_available", "").lower() or "perplexity" in s.get("url", "").lower()]),
        "success": final_data is not None and not (isinstance(final_data, dict) and final_data.get("no_data")),
        "error": None if final_data else "No relevant data could be extracted from any source"
    }

# ── Internal Helpers ─────────────────────────────────────────────────

def _gemini_grounded_research(company: str, data_points: list[str], instruction: str) -> dict:
    """Use Gemini with Google Search grounding for initial research."""
    dp_text = ", ".join(data_points)
    query = f"""Research and retrieve detailed specifications, facts, or data points for "{company}".
Specifically, I need information for the following:
{dp_text}
Additional instructions or constraints:
{instruction}
IMPORTANT: Return your findings as valid JSON with this structure:
{{
    "summary": "brief summary of findings for {company}",
    "data": {{
        // key-value pairs representing the requested data points
    }},
    "confidence": "high/medium/low",
    "notes": "any caveats or limitations"
}}
Return ONLY valid JSON, no explanations, no markdown fences."""

    try:
        return extractor.research(query)
    except Exception as e:
        print(f"    Gemini research failed for {company}: {e}")
        return {"data": None, "grounding_sources": []}

def _extract_prices_from_page(content: str, company: str, data_points: list[str], instruction: str) -> dict:
    """Extract specific parameter data from scraped page content."""
    if len(content) > 50000:
        content = content[:50000]
    prompt = _build_extraction_prompt(company, data_points, content)
    try:
        result = extractor._call_gemini(
            contents=prompt,
            config=extractor.types.GenerateContentConfig(temperature=0.1)
        )
        parsed = extractor._parse_json_response(result.text)
        if parsed and not (isinstance(parsed, dict) and parsed.get("no_data")):
            return parsed
    except Exception as e:
        print(f"    Parameter extraction failed for {company}: {e}")
    return None

def _merge_company_data(company: str, gemini_data, page_extractions: list, data_points: list[str], instruction: str) -> dict:
    """Merge data from Gemini research and scraped page extractions."""
    if not gemini_data and not page_extractions:
        return None

    if not page_extractions:
        if isinstance(gemini_data, list) and len(gemini_data) > 0:
            data = gemini_data[0] if isinstance(gemini_data[0], dict) else {"raw": gemini_data}
        elif isinstance(gemini_data, dict):
            data = gemini_data
        else:
            data = {"raw_data": str(gemini_data)}
        data["company"] = company
        return data

    if not gemini_data and len(page_extractions) == 1:
        data = page_extractions[0]
        data.pop("_source_url", None)
        data["company"] = company
        return data

    sources_data = ""
    if gemini_data:
        sources_data += f"\n--- AI Research (Google Search grounding) ---\n{json.dumps(gemini_data, indent=2, default=str)}\n"

    for i, ext in enumerate(page_extractions):
        source = ext.pop("_source_url", f"Page {i+1}")
        sources_data += f"\n--- Scraped from: {source} ---\n{json.dumps(ext, indent=2, default=str)}\n"

    prompt = _build_merge_prompt(company, data_points, instruction, sources_data)

    try:
        result = extractor._call_gemini(
            contents=prompt,
            config=extractor.types.GenerateContentConfig(temperature=0.1)
        )
        parsed = extractor._parse_json_response(result.text)
        if parsed:
            if isinstance(parsed, dict):
                parsed["company"] = company
            return parsed
    except Exception as e:
        print(f"    Merge failed for {company}: {e}")

    if page_extractions:
        combined = {"company": company}
        for ext in page_extractions:
            ext.pop("_source_url", None)
            combined.update(ext)
        return combined
    if gemini_data:
        if isinstance(gemini_data, dict):
            gemini_data["company"] = company
            return gemini_data
        return {"company": company, "raw_data": gemini_data}
    return None

def _prioritize_urls(urls: list[str], max_count: int) -> list[str]:
    """Prioritize URLs for scraping — official docs and pricing first."""
    high_priority = []
    medium_priority = []
    low_priority = []

    for url in urls:
        url_lower = url.lower()
        if any(d in url_lower for d in [
            "docs", "documentation", "wiki", "features", "specifications", "specs",
            "faq", "compare", "comparison", "vs", "review", "details",
            "overview", "guide", "reference", "data", "report"
        ]):
            high_priority.append(url)
        elif any(d in url_lower for d in [
            "linkedin.com", "facebook.com", "twitter.com", "youtube.com",
            "instagram.com", "glassdoor.", "careers", "jobs", "contact"
        ]):
            low_priority.append(url)
        else:
            medium_priority.append(url)

    prioritized = high_priority + medium_priority + low_priority
    seen = set()
    deduped = []
    for url in prioritized:
        if url not in seen:
            seen.add(url)
            deduped.append(url)

    return deduped[:max_count]

def _shorten_url(url: str, max_len: int = 60) -> str:
    url = url.replace("https://", "").replace("http://", "").replace("www.", "")
    return url[:max_len] + "..." if len(url) > max_len else url
