"""
extractor.py — Gemini AI-powered data extraction and research
Uses Gemini Flash with Google Search grounding for research.
Supports multiple API keys for rotation to avoid rate limits.
"""
from google import genai
from google.genai import types
import json
import re
import time
import os
import threading

_rotation_lock = threading.Lock()


class GeminiRateLimitError(RuntimeError):
    """Exception raised when all API keys for a tier are cooling down."""
    def __init__(self, cooldown_sec: float):
        super().__init__(f"All allowed Gemini keys are cooling down. Retry in {cooldown_sec:.1f}s.")
        self.cooldown_sec = cooldown_sec


# Tiers configuration
TIER_MODELS = {
    "strong": ["gemini-2.5-flash", "gemini-2.0-flash"],
    "mid": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite"],
    "cheap": ["gemini-2.5-flash-lite", "gemini-2.0-flash-lite"]
}

_clients = []
_cell_states = {}
_current_key_idx = {
    "strong": 0,
    "mid": 0,
    "cheap": 0
}


def configure(api_key: str):
    """Initialize with one or more Gemini API keys (comma-separated)."""
    global _clients, _cell_states, _current_key_idx
    _clients = []
    _cell_states = {}
    keys = [k.strip() for k in api_key.split(",") if k.strip()]
    for idx, key in enumerate(keys):
        # We create a client for each tier with its corresponding hard timeout:
        # Strong: 120s (120000ms), Mid: 60s (60000ms), Cheap: 30s (30000ms)
        _clients.append({
            "key": key,
            "strong": genai.Client(api_key=key, http_options=types.HttpOptions(timeout=120000)),
            "mid": genai.Client(api_key=key, http_options=types.HttpOptions(timeout=60000)),
            "cheap": genai.Client(api_key=key, http_options=types.HttpOptions(timeout=30000)),
        })
        for tier in ["strong", "mid", "cheap"]:
            _cell_states[(idx, tier)] = {
                "cooldown_until": 0,
                "exhausted_today": False
            }
    _current_key_idx = {
        "strong": 0,
        "mid": 0,
        "cheap": 0
    }
    if len(_clients) > 1:
        print(f"    Configured {len(_clients)} API keys for rotation across strong, mid, and cheap cells")


def add_key(api_key: str) -> int:
    """Append a single API key to the existing rotation pool. Returns the new key index (1-based)."""
    global _clients, _cell_states
    key = api_key.strip()
    if not key:
        raise ValueError("Empty API key")
    # Check for duplicate
    for c in _clients:
        if c["key"] == key:
            raise ValueError("This API key is already in the rotation pool")
    idx = len(_clients)
    _clients.append({
        "key": key,
        "strong": genai.Client(api_key=key, http_options=types.HttpOptions(timeout=120000)),
        "mid": genai.Client(api_key=key, http_options=types.HttpOptions(timeout=60000)),
        "cheap": genai.Client(api_key=key, http_options=types.HttpOptions(timeout=30000)),
    })
    for tier in ["strong", "mid", "cheap"]:
        _cell_states[(idx, tier)] = {
            "cooldown_until": 0,
            "exhausted_today": False
        }
    print(f"    Added API key #{idx + 1} — now {len(_clients)} keys in rotation pool")
    return idx + 1


def get_key_count() -> int:
    """Return the number of API keys currently in the rotation pool."""
    return len(_clients)


def _parse_cooldown_from_error(error_msg: str) -> float:
    match = re.search(r'try again in\s+(\d+)\s*s', error_msg, re.IGNORECASE)
    if match:
        return float(match.group(1))
    match_min = re.search(r'try again in\s+(\d+)\s*m\s*(\d+)?\s*s?', error_msg, re.IGNORECASE)
    if match_min:
        mins = int(match_min.group(1))
        secs = int(match_min.group(2)) if match_min.group(2) else 0
        return mins * 60.0 + secs
    return 60.0

def _get_available_cell(requested_tier: str, judgment: bool):
    """
    Finds an available cell (key_idx, tier) for the requested task type.
    Implements round-robin and the downgrade ladder.
    Returns (key_idx, client, active_tier, model_name) or raises a exception if all exhausted today.
    """
    with _rotation_lock:
        now = time.time()
        
        # Define the ladder of tiers to search
        if requested_tier == "strong":
            search_tiers = ["strong", "mid", "cheap"]
        elif requested_tier == "mid":
            search_tiers = ["mid", "cheap"]
        else: # cheap
            search_tiers = ["cheap"]
            
        for tier in search_tiers:
            num_keys = len(_clients)
            if num_keys == 0:
                raise RuntimeError("No Gemini API keys configured")
                
            start_idx = _current_key_idx.get(tier, 0)
            for i in range(num_keys):
                key_idx = (start_idx + i) % num_keys
                state = _cell_states.get((key_idx, tier))
                if state and not state["exhausted_today"] and state["cooldown_until"] <= now:
                    # Update round-robin index for next call
                    _current_key_idx[tier] = (key_idx + 1) % num_keys
                    
                    # Pick model name
                    model_name = TIER_MODELS[tier][0] # use primary model
                    client = _clients[key_idx][tier]
                    return key_idx, client, tier, model_name
                    
        # If we get here, no cell is currently available (all are cooling down or exhausted)
        # Let's check if any are cooling down (so we can sleep until the earliest cooldown is over)
        earliest_cooldown = float('inf')
        for tier in search_tiers:
            for key_idx in range(len(_clients)):
                state = _cell_states.get((key_idx, tier))
                if state and not state["exhausted_today"] and state["cooldown_until"] > now:
                    if state["cooldown_until"] < earliest_cooldown:
                        earliest_cooldown = state["cooldown_until"]
                        
        if earliest_cooldown != float('inf'):
            sleep_duration = earliest_cooldown - now + 0.5 # add a small buffer
            raise GeminiRateLimitError(sleep_duration)
            
        raise RuntimeError("All Gemini API keys are completely exhausted for today.")



def _call_gemini(contents: str, config=None, tier: str = "cheap", judgment: bool = False, max_retries: int = 3):
    """
    Call Gemini with cell-level rotation, timeouts, model tiers, and the downgrade ladder.
    Supports model fallback within the tier on 503/Unavailable/Overloaded errors.
    """
    last_error = None
    actual_retries = max(max_retries, len(_clients) * 3)
    
    for attempt in range(actual_retries):
        try:
            key_idx, client, active_tier, primary_model = _get_available_cell(tier, judgment)
        except GeminiRateLimitError as rate_err:
            raise rate_err
        except Exception as cell_err:
            raise cell_err
            
        models_to_try = TIER_MODELS[active_tier]
        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config
                )
                return response
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                is_rate_limit = any(x in error_str for x in ["429", "resource_exhausted", "quota", "503", "unavailable"])
                
                if is_rate_limit:
                    is_hard_quota = any(x in error_str for x in ["limit: 0", "exceeded your current quota", "quota exceeded", "daily limit"])
                    if is_hard_quota:
                        print(f"    [!] Hard quota limit hit for cell ({key_idx + 1}, {active_tier}) using {model_name}. Marking all tiers for Key #{key_idx + 1} as exhausted.")
                        with _rotation_lock:
                            for t in ["strong", "mid", "cheap"]:
                                _cell_states[(key_idx, t)]["exhausted_today"] = True
                        break  # Break model loop to try the next key/cell
                    else:
                        cooldown_sec = _parse_cooldown_from_error(error_str)
                        is_model_overloaded = any(x in error_str for x in ["503", "unavailable", "demand", "spike"])
                        if is_model_overloaded:
                            print(f"    [!] Model {model_name} on cell ({key_idx + 1}, {active_tier}) overloaded/unavailable. Trying next model in tier...")
                            continue  # Try the next model for the same key
                        else:
                            print(f"    [!] Cell ({key_idx + 1}, {active_tier}) rate limited using {model_name}. Cooling down all tiers of Key #{key_idx + 1} for {cooldown_sec}s.")
                            with _rotation_lock:
                                for t in ["strong", "mid", "cheap"]:
                                    _cell_states[(key_idx, t)]["cooldown_until"] = time.time() + cooldown_sec
                            break  # Break model loop to try the next key/cell
                else:
                    print(f"    Gemini error on cell ({key_idx + 1}, {active_tier}) using {model_name}: {e}")
                    # Skip invalid keys on 400 Bad Request / Invalid API Key errors
                    is_invalid_key = any(x in error_str for x in ["api_key_invalid", "api key not valid", "invalid key", "apikey is invalid", "invalid api key"])
                    if is_invalid_key:
                        print(f"    [!] Invalid API key hit for Key #{key_idx + 1}. Disabling this key.")
                        with _rotation_lock:
                            for t in ["strong", "mid", "cheap"]:
                                if (key_idx, t) in _cell_states:
                                    _cell_states[(key_idx, t)]["exhausted_today"] = True
                        break  # Break model loop to try the next key/cell
                    # Try next model in tier
                    continue
                    
    raise last_error


def research(query: str, instruction: str = "") -> dict:
    """
    Use Gemini with Google Search grounding to research a topic — Perplexity-style.
    This searches the web via Google and synthesizes answers with sources.
    
    Args:
        query: The research question / what to look for
        instruction: Additional extraction instructions
    
    Returns:
        dict with: data, summary, sources, raw_response, success, error
    """
    if not _clients:
        return {"data": None, "success": False, "error": "Gemini not configured."}
    
    full_prompt = f"""{query}

{instruction}

IMPORTANT: Return your findings as valid JSON with this structure:
{{
    "summary": "brief text summary of findings",
    "data": [array of objects with the extracted data points],
    "sources": ["list of source URLs you found the data from"],
    "confidence": "high/medium/low",
    "notes": "any caveats or limitations"
}}

Be thorough. Include ALL data points you can find. Use consistent units and formats appropriate to the subject matter.
Return ONLY the JSON, no other text or markdown fences."""

    try:
        try:
            response = _call_gemini(
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.2,
                ),
                tier="strong",
                judgment=True
            )
        except Exception as search_err:
            error_str = str(search_err).lower()
            # If the search tool hits quota limits or is forbidden, try calling without it
            if any(x in error_str for x in ["429", "quota", "limit", "resource_exhausted", "permission", "forbidden", "tool"]):
                print("    [!] Google Search grounding tool failed/exhausted. Falling back to model parametric knowledge...")
                response = _call_gemini(
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                    ),
                    tier="strong",
                    judgment=True
                )
            else:
                raise search_err
        
        raw_text = response.text
        
        # Extract grounding sources from the response metadata
        grounding_sources = []
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                gm = candidate.grounding_metadata
                if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                    for chunk in gm.grounding_chunks:
                        if hasattr(chunk, 'web') and chunk.web:
                            grounding_sources.append({
                                "title": getattr(chunk.web, 'title', ''),
                                "url": getattr(chunk.web, 'uri', ''),
                            })
        
        # Parse the JSON response
        parsed = _parse_json_response(raw_text)
        
        if parsed:
            # Add grounding sources if the model didn't include them
            if grounding_sources and not (parsed.get("sources") or []):
                parsed["sources"] = [s["url"] for s in grounding_sources if s.get("url")]
            
            return {
                "data": parsed.get("data", parsed),
                "summary": parsed.get("summary", ""),
                "sources": parsed.get("sources") or [s["url"] for s in grounding_sources],
                "grounding_sources": grounding_sources,
                "confidence": parsed.get("confidence", "medium"),
                "notes": parsed.get("notes", ""),
                "raw_response": raw_text,
                "success": True,
                "error": None
            }
        else:
            # Even if JSON parsing failed, return the raw text as useful info
            return {
                "data": None,
                "summary": raw_text[:2000],
                "sources": [s["url"] for s in grounding_sources],
                "grounding_sources": grounding_sources,
                "raw_response": raw_text,
                "success": True,  # The AI responded, just not in JSON
                "error": "Response was not structured JSON, but raw text is available"
            }
        
    except Exception as e:
        return {
            "data": None,
            "raw_response": "",
            "success": False,
            "error": str(e)
        }


def extract(content: str, instruction: str, schema_hint: str = None) -> dict:
    """
    Use Gemini to extract structured data from page content (no search grounding).
    
    Args:
        content: Markdown text from a scraped page
        instruction: What the user wants extracted
        schema_hint: Optional JSON schema hint for output format
    
    Returns:
        dict with keys: data, raw_response, success, error
    """
    if not _clients:
        return {"data": None, "raw_response": "", "success": False, "error": "Gemini not configured."}
    
    max_chars = 80000
    if len(content) > max_chars:
        content = content[:max_chars] + "\n\n[... content truncated ...]"
    
    prompt = _build_prompt(instruction, content, schema_hint)
    
    try:
        response = _call_gemini(
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1),
            tier="mid",
            judgment=False
        )
        raw_text = response.text
        parsed = _parse_json_response(raw_text)
        
        return {
            "data": parsed,
            "raw_response": raw_text,
            "success": parsed is not None,
            "error": None if parsed is not None else "Could not parse JSON from AI response"
        }
        
    except Exception as e:
        return {"data": None, "raw_response": "", "success": False, "error": str(e)}


def analyze_sources(query: str, search_results: list[dict]) -> list[dict]:
    """Use Gemini to rank and evaluate search results for relevance."""
    if not _clients:
        return search_results
    
    results_text = "\n".join([
        f"{i+1}. Title: {r.get('title', 'N/A')}\n   URL: {r.get('url', 'N/A')}\n   Snippet: {r.get('snippet', 'N/A')}"
        for i, r in enumerate(search_results)
    ])
    
    prompt = f"""You are a research analyst. The user needs: "{query}"

Score each result from 0-100 on how likely it contains actual DATA relevant to the query. 
Prefer: official documentation, specification pages, detailed reviews, comparison tools, data tables.
Deprioritize: news articles, blogs without data, forums, social media.

Search Results:
{results_text}

Return ONLY a JSON array: [{{"index": 1, "score": 85, "reasoning": "..."}}]"""
    
    try:
        response = _call_gemini(
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1),
            tier="strong",
            judgment=True
        )
        scores = _parse_json_response(response.text)
        
        if scores and isinstance(scores, list):
            for score_item in scores:
                idx = score_item.get("index", 0) - 1
                if 0 <= idx < len(search_results):
                    search_results[idx]["relevance_score"] = score_item.get("score", 50)
                    search_results[idx]["reasoning"] = score_item.get("reasoning", "")
            search_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    except Exception:
        pass
    
    return search_results


def merge_extractions(extractions: list[dict], instruction: str) -> dict:
    """Use Gemini to merge data extracted from multiple sources into a unified table."""
    if not _clients:
        return {"data": None, "summary": "AI not configured", "conflicts": []}
    
    sources_text = ""
    for i, ext in enumerate(extractions):
        sources_text += f"\n--- Source {i+1}: {ext.get('source_url', 'Unknown')} ---\n"
        sources_text += json.dumps(ext.get("data", {}), indent=2, default=str)
        sources_text += "\n"
    
    prompt = f"""Merge the following data from multiple sources into one unified dataset.

Goal: {instruction}

Data:
{sources_text}

Return JSON: {{"merged_data": [...], "summary": "...", "conflicts": [...], "sources_used": N}}
Return ONLY valid JSON."""
    
    try:
        response = _call_gemini(
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1),
            tier="mid",
            judgment=False
        )
        result = _parse_json_response(response.text)
        if result:
            return result
    except Exception as e:
        return {"data": None, "summary": f"Merge failed: {e}", "conflicts": []}
    
    return {"data": None, "summary": "Could not merge data", "conflicts": []}


def _build_prompt(instruction: str, content: str, schema_hint: str = None) -> str:
    schema_part = f"\n\nDesired output schema:\n{schema_hint}" if schema_hint else ""
    
    return f"""You are a precise data extraction AI. Extract structured data from the following web page content.

TASK: {instruction}
{schema_part}

RULES:
1. Return ONLY valid JSON, no explanations, no markdown code fences
2. If data is not found, return: {{"found": false, "reason": "explanation"}}
3. Include ALL relevant data points
4. Use consistent units and formats appropriate to the subject matter

PAGE CONTENT:
{content}"""


def _parse_json_response(text: str):
    """Extract and parse JSON from an AI response."""
    if not text:
        return None
    
    # Try direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    
    # Try to find JSON in code fences or embedded in text
    patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
        r'(\{[\s\S]*\})',
        r'(\[[\s\S]*\])',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except (json.JSONDecodeError, TypeError):
                continue
    
    return None


def synthesize_research(vectors_data: list[dict], original_query: str, format_hint: str = '', chunk_callback=None, required_deliverables: list = None) -> dict:
    """
    Takes all extracted data from all research vectors and creates a unified synthesis.
    Uses Gemini to:
    - Organize findings by theme/topic
    - Identify key insights, trends, comparisons
    - Generate an executive summary (2-3 paragraphs)
    - Suggest appropriate visualization types (table, chart, flowchart) for each section
    - Structure output for document generation
    """
    if not _clients:
        return {"success": False, "error": "Gemini not configured."}
    
    # Structure the inputs
    vectors_text = json.dumps(vectors_data, indent=2, default=str)
    
    deliverables_text = ""
    if required_deliverables:
        deliverables_text = "\nCRITICAL USER REQUIREMENTS (MUST BE FULLY SATISFIED AND COMPLETED):\n" + "\n".join([f"- {item}" for item in required_deliverables])
        
    prompt = f"""You are a senior market research analyst. Synthesize the following raw research findings collected across multiple vectors into a professional, cohesive research report.
 
Original User Query: "{original_query}"
Format Hint / Output preference: "{format_hint}"
{deliverables_text}
 
Raw Vector Findings:
{vectors_text}
 
Analyze and combine these findings. Resolve conflicts where possible.
CRITICAL REQUIREMENTS FOR SYNTHESIS:
1. You MUST ensure that every single item listed in the CRITICAL USER REQUIREMENTS (such as specific comparisons, lists, tables, timelines, roadmaps, or questions) is explicitly and fully addressed, structured, and completed in the report sections or section data tables.
2. Run a strict self-critique check: if any requested deliverable is omitted, left incomplete, or left as a placeholder, you must retrieve the facts from the raw vector findings and populate the missing details before finalizing the report. Do NOT use placeholder text or generic summaries for required deliverables.
 
Present the final synthesis in structured JSON matching this exact schema:
{{
    "title": "A compelling, professional title for the research report",
    "summary": "An executive summary (2-3 paragraphs, summarizing key trends, findings, and implications)",
    "sections": [
        {{
            "title": "Section Title (e.g., Market Overview, Competitor Pricing, Feature Analysis)",
            "content": "Detailed narrative text for this section (multiple paragraphs, professional tone). Include data and details.",
            "data": [
                {{"column1": "val1", "column2": "val2"}}
            ], // Optional: Tabular structured data if this section contains comparison metrics, pricing, features, etc. Set to null if no tabular data.
            "key_findings": ["Bullet point 1", "Bullet point 2"],
            "visualization_hint": "table|chart|flowchart|bullets" // Choose the most appropriate visualization type for this section's data
        }}
    ],
    "key_takeaways": ["Strategic takeaway 1", "Strategic takeaway 2", "Strategic takeaway 3"],
    "sources": [
        {{"url": "source_url", "title": "Source Title", "quality_score": 95, "tier_label": "Tier 1"}}
    ] // Combine and deduplicate sources from the vectors_data. Provide URL, title, quality_score, and tier_label.
}}
 
Return ONLY valid JSON. Do not include markdown code blocks or explanations."""

    try:
        # Use Google Search grounding to enrich the synthesis and check current facts
        key_idx, client, active_tier, model_name = _get_available_cell("strong", judgment=True)
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.3,
            response_mime_type="application/json"
        )
        
        response = client.models.generate_content_stream(
            model=model_name,
            contents=prompt,
            config=config
        )
        
        chunks = []
        for chunk in response:
            text = chunk.text or ""
            if text:
                chunks.append(text)
                if chunk_callback:
                    chunk_callback(text)
                    
        raw_text = "".join(chunks)
        parsed = _parse_json_response(raw_text)
        if parsed and isinstance(parsed, dict) and "sections" in parsed:
            # Deduplicate sources at code level too just in case
            all_sources = []
            seen_urls = set()
            
            # Combine sources from vectors
            for v in vectors_data:
                for s in (v.get("sources") or []):
                    url = s.get("url") or s.get("link")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_sources.append({
                            "url": url,
                            "title": s.get("title") or url,
                            "quality_score": s.get("quality_score", 50),
                            "tier_label": s.get("tier_label") or s.get("tier", "Tier 6")
                        })
            
            # Combine sources from AI response if provided
            ai_sources = parsed.get("sources") or []
            for s in (ai_sources or []):
                url = s.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_sources.append(s)
            
            # Sort sources by quality score descending
            all_sources = sorted(all_sources, key=lambda x: x.get("quality_score", 50), reverse=True)
            
            parsed["sources"] = all_sources
            parsed["success"] = True
            parsed["error"] = None
            return parsed
        else:
            return {
                "success": False,
                "error": "Failed to parse structured JSON from synthesis response",
                "raw_response": raw_text
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def synthesize_research_stream(vectors_data: list[dict], original_query: str, format_hint: str = '', output_folder: str = '', vectors: list[dict] = None, instruction: str = '', required_deliverables: list = None):
    """
    Generator version of synthesize_research. Yields chunks of generated text (str).
    After the generation completes, yields a dict representing the parsed JSON result.
    Synthesizes section-by-section based on blueprint sections and their content types.
    """
    if not _clients:
        yield {"success": False, "error": "Gemini not configured."}
        return
        
    # Load blueprint
    blueprint = {}
    if output_folder:
        blueprint_path = os.path.join(output_folder, "blueprint.json")
        if os.path.exists(blueprint_path):
            try:
                with open(blueprint_path, "r", encoding="utf-8") as f:
                    blueprint = json.load(f)
            except Exception:
                pass
                
    if not blueprint or not blueprint.get("sections"):
        yield {"success": False, "error": "Blueprint is missing. Cannot synthesize report."}
        return

    # Load draft heading payloads from drafts/ directory
    drafts_dir = os.path.join(output_folder, "drafts") if output_folder else None
    draft_payloads = {}
    if drafts_dir and os.path.exists(drafts_dir):
        for f_name in os.listdir(drafts_dir):
            if f_name.endswith(".json"):
                h_id = f_name[:-5]
                path = os.path.join(drafts_dir, f_name)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        draft_payloads[h_id] = json.load(f)
                except Exception:
                    pass

    # Resolve required deliverables
    if not required_deliverables:
        required_deliverables = blueprint.get("required_deliverables") or []

    # Clean/format report title programmatically
    def clean_report_title(t: str) -> str:
        t = t.strip()
        cleaned = t
        if cleaned.lower().startswith("research report:"):
            cleaned = cleaned[16:].strip()
        elif cleaned.lower().startswith("research report (mechanically assembled):"):
            cleaned = cleaned[40:].strip()
        elif cleaned.lower().startswith("partial report:"):
            cleaned = cleaned[15:].strip()
        elif cleaned.lower().startswith("research report on "):
            cleaned = cleaned[19:].strip()
        
        # Conversational prefixes
        cleaned = re.sub(
            r"^(give\s+me|tell\s+me|show\s+me|write\s+a|compare|detailed\s+guide\s+for|guide\s+for|search\s+for|find\s+out|everything\s+about|detailed\s+plan\s+for|road\s+map\s+for)\s+",
            "",
            cleaned,
            flags=re.IGNORECASE
        )
        cleaned = re.sub(
            r",?\s*(provide\s+me|relevaent|also\s+include|which\s+includes|etc\s+have|to\s+be\s+considered).*$",
            "",
            cleaned,
            flags=re.IGNORECASE
        )
        cleaned = cleaned.strip()
        words = cleaned.split()
        if len(words) > 8:
            title_str = " ".join(words[:8]) + "..."
        else:
            title_str = " ".join(words)
            
        typos = {
            "wnats": "wants",
            "detailes": "detailed",
            "relevaent": "relevant",
            "maerker=t": "market",
            "leetcoide": "LeetCode",
            "begineer": "beginner",
            "proividers": "providers",
            "ai ml": "AI/ML",
        }
        for typo, correction in typos.items():
            title_str = re.sub(r"\b" + re.escape(typo) + r"\b", correction, title_str, flags=re.IGNORECASE)
            
        title_str = title_str.title()
        title_str = re.sub(r"\bAi\b", "AI", title_str)
        title_str = re.sub(r"\bMl\b", "ML", title_str)
        title_str = re.sub(r"\bDsa\b", "DSA", title_str)
        
        if not title_str.lower().startswith("research report"):
            return f"Research Report on {title_str}"
        return title_str

    deliverables_text = ""
    if required_deliverables:
        deliverables_text = "\nCRITICAL USER REQUIREMENTS (MUST BE FULLY SATISFIED AND COMPLETED):\n" + "\n".join([f"- {item}" for item in required_deliverables])
        
    # Generate the Title, Summary, and Takeaways
    header_prompt = f"""You are a senior research coordinator compiling a market research report.
Original User Query: "{original_query}"
Master Guidelines/Blueprint: "{instruction}"
Format/Output Preference: "{format_hint}"
{deliverables_text}
 
Blueprint Sections:
{json.dumps([{"id": s["id"], "heading": s["heading"]} for s in blueprint.get("sections", [])], indent=2)}
 
Generate:
1. A compelling, professional, and formal title for the research report.
   CRITICAL: The title must NOT be a copy of the user's query, and must NOT contain spelling mistakes, typos, or conversational language (like "give me", "show me", "tell me").
   Make it sound like a publication-grade research paper or market study (e.g. "Comprehensive Learning Path and Career Guide for AI/ML and Coding").
2. A high-level Executive Summary (2-3 paragraphs, summarizing key trends, findings, and implications).
   CRITICAL: The executive summary must explicitly highlight the resolution of all CRITICAL USER REQUIREMENTS and how those deliverables are addressed in this report.
3. A list of 3-5 strategic Key Takeaways.
 
Return your response in this exact JSON structure:
{{
  "title": "...",
  "summary": "...",
  "key_takeaways": ["Takeaway 1", "Takeaway 2", ...]
}}
Return ONLY valid JSON. No markdown code blocks, no other text."""

    title = clean_report_title(original_query)
    summary = "No summary available."
    key_takeaways = []
    
    try:
        response = _call_gemini(
            contents=header_prompt,
            tier="mid",
            judgment=False,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        parsed = _parse_json_response(response.text)
        if parsed and isinstance(parsed, dict):
            raw_gen_title = parsed.get("title")
            if raw_gen_title and len(raw_gen_title.strip()) > 3:
                title = clean_report_title(raw_gen_title)
            summary = parsed.get("summary", summary)
            key_takeaways = parsed.get("key_takeaways", [])
    except Exception as e:
        print(f"Failed to generate report header: {e}")
        
    header_md = f"# {title}\n\n## Executive Summary\n{summary}\n\n## Key Strategic Takeaways\n"
    for item in key_takeaways:
        header_md += f"- {item}\n"
    header_md += "\n"
    yield header_md
    
    sections = []
    all_sources = []
    seen_urls = set()
    
    # Collect all sources first
    for h_id, payload in draft_payloads.items():
        for s in (payload.get("sources") or []):
            url = s.get("url") or s.get("link")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_sources.append({
                    "url": url,
                    "title": s.get("title") or url,
                    "quality_score": s.get("quality_score", s.get("score", 50)),
                    "tier_label": s.get("tier_label") or s.get("tier", s.get("label", "Tier 6"))
                })

    previous_sections_context = []

    for idx, sec in enumerate(blueprint.get("sections", []), 1):
        sid = sec["id"]
        heading = sec["heading"]
        content_type = sec.get("content_type", "narrative")
        instructions = sec.get("instructions", "")
        
        payload = draft_payloads.get(sid)
        if not payload or not payload.get("success") or not payload.get("data"):
            section_content = "*Insufficient data captured for this section.*"
            section_obj = {
                "title": heading,
                "content": section_content,
                "data": None,
                "key_findings": [],
                "visualization_hint": "bullets"
            }
            sections.append(section_obj)
            sec_md = f"## {idx}. {heading}\n\n{section_content}\n\n"
            yield sec_md
            continue
            
        draft_data = payload["data"]
        
        # Scraped images
        scraped_imgs = []
        for src in payload.get("sources", []):
            if isinstance(src, dict) and "images" in src:
                scraped_imgs.extend(src["images"])
                
        images_context = ""
        if scraped_imgs:
            images_context = f"\nScraped webpage images that you can embed in your section using standard markdown `![alt](url)`:\n" + json.dumps(scraped_imgs, indent=2)

        # Build prompt based on content type
        content_type_prompt = ""
        if content_type == "flowchart":
            content_type_prompt = """The content of this section MUST primarily consist of a detailed Mermaid flowchart showing the process flow, payment workflow, or logic triggers.
            Format the flowchart inside a markdown mermaid block:
            ```mermaid
            graph TD
                A[Start] --> B[Step 1]
            ```
            Explain the flowchart steps briefly (1-2 sentences per step)."""
        elif content_type == "narrative_with_flowchart":
            content_type_prompt = """This section needs both a detailed narrative analysis (2-3 paragraphs) AND a Mermaid flowchart block showing the associated process/payment flow.
            Format the flowchart inside a markdown mermaid block:
            ```mermaid
            graph TD
                A[Start] --> B[Step 1]
            ```"""
        elif content_type == "comparison_table":
            content_type_prompt = """The content of this section MUST contain a detailed markdown comparison table comparing the platforms/competitors/features.
            Format the table in markdown:
            | Parameter | Platform A | Platform B |
            |---|---|---|"""
        elif content_type == "timeline":
            content_type_prompt = """The content of this section MUST contain a chronological timeline or rollout milestones roadmap.
            Use a Mermaid timeline or gantt chart block if appropriate, or a detailed numbered list with milestones.
            Format the timeline inside a markdown mermaid block if using mermaid:
            ```mermaid
            gantt
                title Integration Roadmap
            ```"""
        elif content_type == "data_matrix":
            content_type_prompt = """This section must include a detailed data parameter matrix (a structured comparison table showing specific pricing rates, commissions, API limits, or compliance limits)."""
        else:
            content_type_prompt = """Write a rich, detailed, professional narrative analysis (3-5 paragraphs) supported by bulleted details."""

        # Enforce Anti-Repetition
        anti_repetition_context = ""
        if previous_sections_context:
            anti_repetition_context = "\nALREADY COVERED in previous sections (DO NOT REPEAT or duplicate these points):\n" + "\n".join([f"- {item['title']}: {item['summary']}" for item in previous_sections_context])

        section_prompt = f"""You are a master market analyst writing a specific section of a market research report.
Original User Query: "{original_query}"
Report Section Title: "{heading}"
Expected Format/Content Type: "{content_type}"
Section instructions: "{instructions}"
{deliverables_text}
{content_type_prompt}
{anti_repetition_context}

Master Expanded Research Prompt & Verbatim Answers Transcript (CRITICAL INSTRUCTIONS & CONSTRAINTS):
{instruction}

Extracted Factual Data from Sources:
{json.dumps(draft_data, indent=2)}

Sources used:
{json.dumps(payload.get("sources"), indent=2)}
{images_context}

RULES:
1. Write a professional, comprehensive, and highly detailed section following the format guidelines. Use all available factual rates, parameters, and workflows.
2. Under "content", provide the complete markdown content. If the content type requests a Mermaid chart or a comparison table, you MUST write the full Mermaid code block or markdown table directly inside the "content" string. Do not leave placeholders.
3. If images are provided, embed the most relevant 1-2 images in the markdown content using standard markdown `![alt text](url)`.
4. Output your response as a valid JSON object matching this schema:
{{
  "title": "Title of the section (e.g. '{heading}')",
  "content": "Detailed markdown content for the section. Include narrative paragraphs, bullet lists, markdown tables, or Mermaid code blocks as requested.",
  "data": [
    {{"column1": "val1", "column2": "val2"}}
  ], // Optional: structured tabular data. Set to null if no tabular data.
  "key_findings": ["Key finding bullet 1", "Key finding bullet 2"],
  "summary": "A 1-sentence summary of this section's core findings for anti-repetition context.",
  "visualization_hint": "table|chart|flowchart|timeline|bullets"
}}
Return ONLY the valid JSON object. No explanations, no markdown fences outside the JSON."""

        try:
            response = _call_gemini(
                contents=section_prompt,
                tier="strong",
                judgment=True,
                config=types.GenerateContentConfig(
                    temperature=0.15,
                    response_mime_type="application/json"
                )
            )
            parsed = _parse_json_response(response.text)
            if parsed and isinstance(parsed, dict):
                section_title = parsed.get("title", heading)
                section_content = parsed.get("content", "")
                section_data = parsed.get("data")
                key_findings = parsed.get("key_findings", [])
                viz_hint = parsed.get("visualization_hint", "bullets")
                
                section_obj = {
                    "title": section_title,
                    "content": section_content,
                    "data": section_data,
                    "key_findings": key_findings,
                    "visualization_hint": viz_hint
                }
                sections.append(section_obj)
                
                # Keep summary for anti-repetition context
                previous_sections_context.append({
                    "title": section_title,
                    "summary": parsed.get("summary", heading)
                })
                
                # Format section to markdown and stream
                sec_md = f"## {idx}. {section_title}\n\n{section_content}\n\n"
                if key_findings:
                    sec_md += "### Key Findings\n"
                    for kf in key_findings:
                        sec_md += f"- {kf}\n"
                    sec_md += "\n"
                yield sec_md
            else:
                raise ValueError("Parsed result was not a dictionary")
        except Exception as e:
            print(f"Failed to synthesize section for {heading}: {e}")
            section_content = "*AI synthesis failed for this section. Direct extraction output shown.*"
            section_obj = {
                "title": heading,
                "content": section_content,
                "data": draft_data,
                "key_findings": [],
                "visualization_hint": "table",
            }
            sections.append(section_obj)
            yield f"## {idx}. {heading}\n\n{section_content}\n\n"

    # Yield sources list at the end
    sources_md = "## Sources & References\n"
    if all_sources:
        for s_idx, s in enumerate(all_sources, 1):
            sources_md += f"- [{s.get('title') or s.get('url')}]({s.get('url')}) ({s.get('tier_label')} | Quality Score: {s.get('quality_score')}/100)\n"
    else:
        sources_md += "No sources recorded.\n"
    yield sources_md

    final_report = {
        "title": title,
        "summary": summary,
        "sections": sections,
        "key_takeaways": key_takeaways,
        "sources": all_sources,
        "success": True
    }
    yield final_report


def extract_from_transcript(transcript_text: str, query: str, data_points: list[str] = None) -> dict:
    """
    Specialized extraction for YouTube video transcripts. Handles the conversational/spoken nature of transcripts.
    Return `{data, key_points: [], timestamps: [], success, error}`
    """
    if not _clients:
        return {"success": False, "error": "Gemini not configured."}
        
    dp_text = f"Extract information related to: {', '.join(data_points)}" if data_points else "Extract key research information."
    
    prompt = f"""You are a precise research assistant. Extract key information from the following video transcript.
    
Target Query/Topic: "{query}"
Data Points to look for: {dp_text}

Transcript text:
{transcript_text}

Provide your findings in this structured JSON format:
{{
    "data": {{
        // Key extracted facts/metrics as key-value pairs
    }},
    "key_points": [
        "Major insight or fact extracted"
    ],
    "timestamps": [
        {{"topic": "Brief topic name", "timestamp": "MM:SS or HH:MM:SS if available, or approximate section name", "description": "What was discussed here"}}
    ]
}}

Return ONLY valid JSON. No markdown code blocks, no explanations."""

    try:
        response = _call_gemini(
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2),
            tier="mid",
            judgment=False
        )
        raw_text = response.text
        parsed = _parse_json_response(raw_text)
        if parsed and isinstance(parsed, dict):
            return {
                "success": True,
                "data": parsed.get("data", {}),
                "key_points": parsed.get("key_points", []),
                "timestamps": parsed.get("timestamps", []),
                "error": None
            }
        else:
            return {
                "success": False,
                "error": "Failed to parse JSON response from transcript extraction",
                "raw_response": raw_text
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def refine_synthesis(existing_synthesis: dict, refinement_instruction: str, original_query: str = "", refined_prompt: str = "") -> dict:
    """
    Refines the existing synthesized research findings based on user feedback/refinement instruction.
    Uses Gemini to modify the JSON structure without re-scraping or re-researching.
    """
    if not _clients:
        return {"success": False, "error": "Gemini not configured."}

    prompt = f"""You are a senior market research analyst.
You have previously synthesized a research report into a structured JSON format.
The user now has some feedback or wants to make changes/improvements to this report.

Original User Query: "{original_query}"
Master Guidelines/Blueprint: "{refined_prompt}"
Refinement Feedback/Instruction: "{refinement_instruction}"

Existing Report JSON:
{json.dumps(existing_synthesis, indent=2, default=str)}

Your task:
Modify the Existing Report JSON according to the user's Refinement Feedback/Instruction.
Maintain the exact same JSON schema:
{{
    "title": "A compelling, professional title for the research report",
    "summary": "An executive summary (2-3 paragraphs, summarizing key trends, findings, and implications)",
    "sections": [
        {{
            "title": "Section Title (e.g., Market Overview, Competitor Pricing, Feature Analysis)",
            "content": "Detailed analysis narrative text for this section (multiple paragraphs, professional tone). Include data and details.",
            "data": [
                {{"column1": "val1", "column2": "val2"}}
            ], // Tabular structured data if applicable, otherwise null.
            "key_findings": ["Bullet point 1", "Bullet point 2"],
            "visualization_hint": "table|chart|flowchart|bullets"
        }}
    ],
    "key_takeaways": ["Strategic takeaway 1", "Strategic takeaway 2", "Strategic takeaway 3"],
    "sources": [
        {{"url": "source_url", "title": "Source Title", "quality_score": 95, "tier_label": "Tier 1"}}
    ]
}}

Rules:
1. Make the requested modifications precisely.
2. If the user asks to add or change details, recalculate or reformat the existing text/table values appropriately.
3. If they ask to focus more on a certain aspect, rewrite the summary/narrative content accordingly.
4. Keep all other sections/data intact if they are not affected by the request.
5. Return ONLY the new valid JSON. Do not include markdown code blocks or explanations."""

    try:
        response = _call_gemini(
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2),
            tier="strong",
            judgment=True
        )
        raw_text = response.text
        parsed = _parse_json_response(raw_text)
        if parsed and isinstance(parsed, dict) and "sections" in parsed:
            parsed["success"] = True
            parsed["error"] = None
            return parsed
        else:
            return {
                "success": False,
                "error": "Failed to parse structured JSON from refinement response",
                "raw_response": raw_text
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
