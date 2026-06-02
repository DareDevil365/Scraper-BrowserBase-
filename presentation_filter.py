from __future__ import annotations

import re
from urllib.parse import urlparse
from typing import Any, Dict, List, Tuple

PLACEHOLDER_PHRASES = [
    "failed to synthesize section",
    "all gemini api keys are completely exhausted",
    "insufficient data captured",
    "no data found for vector",
    "504 deadline_exceeded",
    "deadline expired",
]

PLACEHOLDER_PATTERNS = PLACEHOLDER_PHRASES

BAD_SOURCE_TERMS = [
    "privacy policy",
    "account_deletion",
    "travel union",
    "dictionary",
    "meaning - cambridge",
    "merriam-webster",
    "thefreedictionary",
]

def is_placeholder_text(x: Any) -> bool:
    if x is None:
        return True
    s = str(x).strip().lower()
    return (
        not s
        or s in {"null", "none", "{}", "[]"}
        or any(p in s for p in PLACEHOLDER_PHRASES)
    )

def has_real_values(obj: Any) -> bool:
    if obj is None:
        return False

    if isinstance(obj, str):
        return not is_placeholder_text(obj)

    if isinstance(obj, list):
        return any(has_real_values(x) for x in obj)

    if isinstance(obj, dict):
        useful = []
        for k, v in obj.items():
            if str(k).lower() in {"company", "vector_id", "data_confidence", "data_sources"}:
                continue
            useful.append(has_real_values(v))
        return any(useful)

    return True

def source_is_bad(src: Dict[str, Any]) -> bool:
    text = f"{src.get('title','')} {src.get('url','')} {src.get('status','')}".lower()

    if any(term in text for term in BAD_SOURCE_TERMS):
        return True

    if "not_applicable" in text or "soft_404" in text or "failed" in text:
        return True

    return False

def classify_vector(vector_result: Dict[str, Any]) -> str:
    body = vector_result.get("body") or vector_result.get("content") or ""
    data = vector_result.get("data") or vector_result.get("extracted_data")
    sources = vector_result.get("sources") or []

    useful_data = has_real_values(data)
    useful_body = not is_placeholder_text(body)
    useful_sources = [s for s in sources if not source_is_bad(s)]

    if useful_body or useful_data:
        return "RICH" if useful_sources else "PARTIAL"

    return "EMPTY"

def clean_domain(url: str, title: str = "") -> str:
    if title and "." in title and "grounding-api-redirect" not in title:
        return title.strip()

    if not url:
        return title or ""

    parsed = urlparse(url)
    host = parsed.netloc.lower().replace("www.", "")

    if "vertexaisearch.cloud.google.com" in host:
        return title or "grounding-source"

    return host or title or url

def source_is_renderable(src: Dict[str, Any]) -> bool:
    return not source_is_bad(src)

def dedupe_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    cleaned = []

    for src in sources or []:
        if not source_is_renderable(src):
            continue

        title = str(src.get("title", "")).strip()
        url = str(src.get("url", "")).strip()
        domain = clean_domain(url, title)

        key = (domain.lower(), src.get("vector_id"))
        if key in seen:
            continue
        seen.add(key)

        cleaned.append({
            "title": title or domain,
            "domain": domain,
            "url": url,
            "tier": src.get("tier", ""),
            "status": src.get("status", ""),
            "vector_id": src.get("vector_id", ""),
        })

    return cleaned

def _as_text(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return ", ".join(str(x) for x in v if x not in (None, ""))
    if isinstance(v, dict):
        return "; ".join(f"{k}: {val}" for k, val in v.items() if val not in (None, ""))
    return str(v)


def normalize_tool_row(obj, vector_id="", topic="", fallback_category=""):
    if not isinstance(obj, dict):
        return None

    name = obj.get("name") or obj.get("tool_name")
    if not name:
        return None

    categories = obj.get("categories")
    category = obj.get("category") or fallback_category or topic
    if isinstance(categories, list) and categories:
        category = ", ".join(categories)

    return {
        "vector_id": vector_id,
        "category": category,
        "name": _as_text(name),
        "url": _as_text(obj.get("url")),
        "purpose": _as_text(obj.get("purpose") or obj.get("description")),
        "key_features": _as_text(obj.get("key_features")),
        "use_cases": _as_text(obj.get("use_cases") or obj.get("typical_use_cases")),
        "free_limitations": _as_text(
            obj.get("free_tier_details")
            or obj.get("free_limitations")
            or obj.get("limitations")
        ),
    }


def flatten_tool_rows(data, vector_id="", topic=""):
    rows = []

    def walk(node, fallback_category=""):
        if isinstance(node, dict):
            direct = normalize_tool_row(node, vector_id, topic, fallback_category)
            if direct:
                rows.append(direct)

            for k, v in node.items():
                if str(k).lower() in {
                    "company", "vector", "sources", "data_sources",
                    "data_confidence", "timestamp", "status", "error",
                }:
                    continue
                if isinstance(v, (dict, list)):
                    walk(v, fallback_category=k)

        elif isinstance(node, list):
            for item in node:
                walk(item, fallback_category=fallback_category)

    walk(data)

    seen = set()
    clean = []
    for r in rows:
        key = (
            r.get("name", "").lower().strip(),
            r.get("url", "").lower().strip(),
            r.get("category", "").lower().strip(),
        )
        if key in seen:
            continue
        seen.add(key)
        clean.append(r)

    return clean

def section_has_useful_data(section: Dict[str, Any]) -> bool:
    body = section.get("body") or section.get("content") or section.get("text")
    if body and not is_placeholder_text(body):
        return True

    data = section.get("data") or section.get("extracted_data")
    table_data = flatten_json_to_table(data, topic=section.get("topic", ""))
    return table_data is not None


def flatten_json_to_table(data: Any, topic: str = "") -> dict | None:
    """
    Dynamically flattens any JSON structure into a table schema:
    {
        "title": topic,
        "headers": ["Col 1", "Col 2", ...],
        "rows": [["val 1", "val 2", ...], ...]
    }
    """
    if not data:
        return None

    # Helper to clean and format headers
    def format_header(key: str) -> str:
        if str(key).lower() in {"url", "cod", "gst", "eta", "rto"}:
            return str(key).upper()
        s = re.sub(r"[_\-]+", " ", str(key))
        return s.strip().title()

    # Helper to format cell values
    def format_cell(val: Any) -> str:
        if val is None:
            return ""
        if isinstance(val, list):
            if all(isinstance(x, dict) for x in val):
                return "\n".join(
                    "; ".join(f"{format_header(k)}: {format_cell(v)}" for k, v in x.items())
                    for x in val
                )
            return ", ".join(format_cell(x) for x in val if x not in (None, ""))
        if isinstance(val, dict):
            return "\n".join(f"• {format_header(k)}: {format_cell(v)}" for k, v in val.items() if v not in (None, ""))
        return str(val)

    headers = []
    rows = []

    # Case 1: List of dicts (e.g. list of objects)
    if isinstance(data, list) and all(isinstance(x, dict) for x in data):
        all_keys = []
        ignored_keys = {"vector_id", "timestamp", "status", "error", "confidence", "data_confidence", "data_sources"}
        for item in data:
            for k in item.keys():
                if k not in all_keys and k.lower() not in ignored_keys:
                    all_keys.append(k)
        
        first_keys = [k for k in all_keys if k.lower() in {"company", "name", "tool_name", "carrier"}]
        other_keys = [k for k in all_keys if k.lower() not in {"company", "name", "tool_name", "carrier"}]
        ordered_keys = first_keys + other_keys

        if ordered_keys:
            headers = [format_header(k) for k in ordered_keys]
            for item in data:
                row = []
                for k in ordered_keys:
                    row.append(format_cell(item.get(k, "")))
                rows.append(row)

    # Case 2: Dict where values are dicts (e.g. entity-based lookup)
    elif isinstance(data, dict) and all(isinstance(v, dict) for v in data.values()):
        all_keys = []
        ignored_keys = {"vector_id", "timestamp", "status", "error", "confidence", "data_confidence", "data_sources"}
        for sub_dict in data.values():
            for k in sub_dict.keys():
                if k not in all_keys and k.lower() not in ignored_keys:
                    all_keys.append(k)
        
        first_col = "Entity"
        topic_lower = topic.lower()
        if "carrier" in topic_lower or "logistics" in topic_lower or "shipping" in topic_lower:
            first_col = "Carrier"
        elif "company" in topic_lower or "provider" in topic_lower:
            first_col = "Company"
        elif "tool" in topic_lower:
            first_col = "Tool"

        headers = [first_col] + [format_header(k) for k in all_keys]
        for key, sub_dict in data.items():
            row = [format_cell(key)]
            for k in all_keys:
                row.append(format_cell(sub_dict.get(k, "")))
            rows.append(row)

    # Case 3: Flat dictionary (parameter-value mapping)
    elif isinstance(data, dict):
        headers = ["Parameter", "Value"]
        for k, v in data.items():
            if k.lower() not in {"vector_id", "timestamp", "status", "error", "confidence", "data_confidence", "data_sources"}:
                rows.append([format_header(k), format_cell(v)])

    # Case 4: List of scalars
    elif isinstance(data, list):
        headers = ["Item"]
        for x in data:
            rows.append([format_cell(x)])

    if headers and rows:
        return {
            "title": topic,
            "headers": headers,
            "rows": rows
        }
    return None


def clean_report_title(title: str) -> str:
    title = title.strip()
    cleaned = title
    if cleaned.lower().startswith("research report:"):
        cleaned = cleaned[16:].strip()
    elif cleaned.lower().startswith("research report (mechanically assembled):"):
        cleaned = cleaned[40:].strip()
    elif cleaned.lower().startswith("partial report:"):
        cleaned = cleaned[15:].strip()
    elif cleaned.lower().startswith("research report on "):
        cleaned = cleaned[19:].strip()
        
    if len(cleaned) > 50 or any(p in cleaned.lower() for p in ["give me", "tell me", "show me", "write a", "compare", "guide for", "beginner", "wnats to"]):
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
        
        return f"Research Report on {title_str}"
        
    return title


def build_presentable(payload: Dict[str, Any], sources: List[Dict[str, Any]] | None = None, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    config = config or {}
    sources = sources or payload.get("sources", [])

    raw_title = payload.get("title") or payload.get("query") or "Research Report"
    result = {
        "title": clean_report_title(raw_title),
        "session_id": payload.get("session_id", ""),
        "generated_at": payload.get("generated_at") or payload.get("created_at", ""),
        "status": payload.get("status", "partial"),
        "banner": "",
        "executive_summary": "",
        "key_takeaways": [],
        "sections": [],
        "tables": [],
        "gaps": [],
        "sources": [],
    }

    raw_summary = payload.get("executive_summary") or payload.get("summary")
    if raw_summary and not is_placeholder_text(raw_summary) and "no summary available" not in str(raw_summary).lower():
        result["executive_summary"] = raw_summary

    raw_sections = payload.get("sections") or payload.get("vectors") or payload.get("results") or []

    for sec in raw_sections:
        if not isinstance(sec, dict):
            continue

        vector_id = sec.get("vector_id") or sec.get("id") or ""
        topic = sec.get("topic") or sec.get("title") or sec.get("company") or f"Section {vector_id}"
        data = sec.get("data") or sec.get("extracted_data")

        if not section_has_useful_data(sec):
            result["gaps"].append({
                "vector_id": vector_id,
                "topic": topic,
                "reason": "Insufficient usable data captured.",
            })
            continue

        body = sec.get("body") or sec.get("content") or sec.get("text") or ""
        if is_placeholder_text(body):
            body = ""

        table_data = flatten_json_to_table(data, topic=topic)
        if table_data:
            table_data["vector_id"] = vector_id
            result["tables"].append(table_data)

        if body:
            result["sections"].append({
                "vector_id": vector_id,
                "title": topic,
                "body": body,
            })

    result["sources"] = dedupe_sources(sources)

    usable_count = len(result["sections"]) + len(result["tables"])
    if usable_count == 0:
        result["status"] = "incomplete_fallback"
        result["banner"] = "No renderable findings were found. Raw scrape/debug data was withheld."
    elif result["gaps"]:
        result["status"] = "partial"
        result["banner"] = f"Partial report: {len(result['gaps'])} section(s) had insufficient usable data."

    return result
