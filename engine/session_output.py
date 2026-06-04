"""
session_output.py - durable per-session research artifacts.
Writes useful files while research is still running so failed sessions still
leave scraped data, sources, and partial findings behind.
"""
import json
import os
import re
import threading
from datetime import datetime

_csv_lock = threading.Lock()


def _safe_name(text: str, fallback: str = "research") -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text or "").strip("_").lower()
    return (text[:60] or fallback)


def ensure_session_folder(session_id: str, topic: str, created_at: str = "") -> str:
    root = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
    os.makedirs(root, exist_ok=True)

    if created_at:
        stamp = re.sub(r"[^0-9]", "", created_at)[:14]
    else:
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")

    folder = os.path.join(root, f"{_safe_name(topic)}_{stamp}_{session_id}")
    os.makedirs(os.path.join(folder, "media"), exist_ok=True)
    return folder


def write_run_config(folder: str, session: dict):
    path = os.path.join(folder, "run_config.json")
    payload = {
        "session_id": session.get("id", ""),
        "query": session.get("original_query", ""),
        "context": session.get("original_context", ""),
        "depth": session.get("depth", "standard"),
        "output_format": session.get("output_format", "pdf"),
        "effort_estimate": session.get("effort_estimate", {}),
        "created_at": session.get("created_at", ""),
        "clarification_answers": session.get("clarification_answers", [])
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    return path


def write_search_parameters(folder: str, session: dict):
    write_run_config(folder, session)
    
    path = os.path.join(folder, "01_search_parameters.txt")
    answers = session.get("clarification_answers") or []
    vectors = session.get("research_vectors") or []

    content = [
        "# Search Parameters",
        "",
        f"- Session ID: {session.get('id', '')}",
        f"- Created At: {session.get('created_at', '')}",
        f"- Status: {session.get('status', '')}",
        f"- Output Format: {session.get('output_format', '')}",
        "",
        "## Original Query",
        session.get("original_query", ""),
        "",
        "## Additional Context",
        session.get("original_context", "") or "None",
        "",
        "## Refined Prompt",
        session.get("refined_prompt", "") or "Not generated yet",
        "",
        "## Clarification Answers",
        json.dumps(answers, indent=2, default=str),
        "",
        "## Research Vectors",
        json.dumps(vectors, indent=2, default=str),
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(content))
    return path


def append_raw_research(folder: str, url: str, tier: str, rationale: str, text: str):
    path = os.path.join(folder, "raw_research.jsonl")
    payload = {
        "url": url,
        "tier": tier,
        "rationale": rationale,
        "scraped_at": datetime.now().isoformat(),
        "text": text
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, default=str) + "\n")
    return path


def append_raw_vector(folder: str, vector: dict, result: dict):
    # Call the new research logger for each source scraped
    sources = result.get("sources") or []
    for src in sources:
        # Get content text if present, otherwise title/snippet
        text_content = result.get("data", {}).get("raw_data") or result.get("data", {}).get("summary") or src.get("snippet", "")
        append_raw_research(folder, src.get("url"), src.get("tier", "TIER_6"), src.get("label", "General Web"), str(text_content))

    path = os.path.join(folder, "02_raw_scraped_data.txt")
    payload = {
        "timestamp": datetime.now().isoformat(),
        "vector": vector,
        "success": result.get("success"),
        "pages_scraped": result.get("pages_scraped"),
        "error": result.get("error"),
        "sources": sources,
        "data": result.get("data"),
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 80 + "\n")
        f.write(f"VECTOR: {vector.get('topic', 'Sub-topic')}\n")
        f.write(f"TIME: {payload['timestamp']}\n")
        f.write(f"SUCCESS: {payload['success']}\n")
        f.write(f"PAGES SCRAPED: {payload['pages_scraped']}\n")
        if payload["error"]:
            f.write(f"ERROR: {payload['error']}\n")
        f.write("\nSOURCES:\n")
        for src in sources:
            f.write(f"- {src.get('title') or src.get('url')} | {src.get('url')}\n")
        f.write("\nEXTRACTED DATA:\n")
        f.write(json.dumps(payload["data"], indent=2, default=str))
        f.write("\n")
    return path


def write_sources_ledger(folder: str, sources: list[dict]):
    path = os.path.join(folder, "sources.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sources, f, indent=2, default=str)
    # Sync the in-memory cache
    _ledger_cache[folder] = sources
    _ledger_dirty[folder] = False
    return path


# In-memory ledger cache to avoid O(n) read/write per URL update
_ledger_cache = {}  # keyed by folder path -> list of source dicts
_ledger_dirty = {}  # keyed by folder path -> bool


def _load_ledger(folder: str) -> list:
    """Load sources ledger into memory cache if not already loaded."""
    if folder in _ledger_cache:
        return _ledger_cache[folder]
    ledger_path = os.path.join(folder, "sources.json")
    sources = []
    if os.path.exists(ledger_path):
        try:
            with open(ledger_path, "r", encoding="utf-8") as f:
                sources = json.load(f)
        except Exception:
            pass
    _ledger_cache[folder] = sources
    _ledger_dirty[folder] = False
    return sources


def flush_sources_ledger(folder: str):
    """Flush the in-memory ledger cache to disk."""
    if not folder or folder not in _ledger_cache:
        return
    if not _ledger_dirty.get(folder, False):
        return
    ledger_path = os.path.join(folder, "sources.json")
    try:
        with open(ledger_path, "w", encoding="utf-8") as f:
            json.dump(_ledger_cache[folder], f, indent=2, default=str)
        _ledger_dirty[folder] = False
    except Exception as e:
        print(f"Failed to flush sources ledger: {e}")


def update_sources_ledger_entry(folder: str, url: str, status: str, had_data: bool, details: dict = None):
    if not folder:
        return
    sources = _load_ledger(folder)
            
    found = False
    for src in sources:
        if src.get("url") == url:
            src["status"] = status
            src["had_data"] = had_data
            src["timestamp"] = datetime.now().isoformat()
            if details:
                for k, v in details.items():
                    src[k] = v
            found = True
            break
            
    if not found:
        new_src = {
            "url": url,
            "status": status,
            "had_data": had_data,
            "timestamp": datetime.now().isoformat()
        }
        if details:
            for k, v in details.items():
                new_src[k] = v
        sources.append(new_src)
    
    _ledger_dirty[folder] = True
    
    # Auto-flush every 10 updates to prevent data loss on crash
    if len(sources) % 10 == 0:
        flush_sources_ledger(folder)


def append_failure(folder: str, target: str, tier: str, error: str, action_taken: str):
    path = os.path.join(folder, "failures.jsonl")
    payload = {
        "target": target,
        "tier": tier,
        "error": error,
        "action_taken": action_taken,
        "timestamp": datetime.now().isoformat()
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, default=str) + "\n")
    return path


def append_run_log(folder: str, estimated_work: dict, actual_work: dict):
    path = os.path.join(folder, "run_log.jsonl")
    payload = {
        "estimated_work": estimated_work,
        "actual_work": actual_work,
        "timestamp": datetime.now().isoformat()
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, default=str) + "\n")
    return path


def write_state(folder: str, state: dict):
    path = os.path.join(folder, "state.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, default=str)
    return path


def save_extracted_vector(folder: str, vector_id: str, result: dict):
    extracted_dir = os.path.join(folder, "extracted")
    os.makedirs(extracted_dir, exist_ok=True)
    path = os.path.join(extracted_dir, f"{vector_id}.json")
    
    payload = {
        "vector_id": vector_id,
        "vector": result.get("vector"),
        "data": result.get("data"),
        "sources": result.get("sources"),
        "success": result.get("success"),
        "error": result.get("error"),
        "pages_scraped": result.get("pages_scraped", 0),
        "timestamp": datetime.now().isoformat()
    }
    
    # Classify status based on results
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from presentation_filter import classify_vector
    
    status = classify_vector(result)
    if status == "RICH":
        payload["status"] = "SUCCESS"
    elif status == "PARTIAL":
        payload["status"] = "LOW_COVERAGE"
    else:
        err = str(result.get("error") or "").lower()
        if "login" in err or "auth" in err:
            payload["status"] = "LOGIN_GATED"
        elif "not applicable" in err or "wrong entity" in err:
            payload["status"] = "NOT_APPLICABLE"
        else:
            payload["status"] = "EMPTY"
            
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    return path


def write_sources_log_csv(folder: str, sources: list[dict], entity_name: str = ""):
    path = os.path.join(folder, "sources_log.csv")
    import csv
    headers = [
        "entity", "url", "title", "priority", "authority_score", "domain", "tier",
        "scrape_success", "had_data", "status", "error_type", "decision", "timestamp"
    ]
    with _csv_lock:
        try:
            exists = os.path.exists(path)
            with open(path, "a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if not exists or os.path.getsize(path) == 0:
                    writer.writerow(headers)
                for src in sources:
                    url = src.get("url") or src.get("link") or ""
                    if not url:
                        continue
                    domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url.lower())
                    domain = domain_match.group(1) if domain_match else url
                    
                    scrape_success = src.get("scrape_success", src.get("status") == "SUCCESS")
                    had_data = src.get("had_data", scrape_success)
                    decision = src.get("decision", "accept" if had_data else "reject")
                    
                    writer.writerow([
                        entity_name,
                        url,
                        src.get("title", ""),
                        src.get("priority", src.get("vector_id", "medium")),
                        src.get("score", src.get("authority_score", 50)),
                        domain,
                        src.get("tier", "TIER_6"),
                        scrape_success,
                        had_data,
                        src.get("status", "FAILED"),
                        src.get("error_type", src.get("error", "")),
                        decision,
                        src.get("timestamp", datetime.now().isoformat())
                    ])
        except Exception as e:
            print(f"Failed to write sources_log.csv: {e}")
    return path


def render_value_as_markdown_table(data: Any) -> list[str]:
    """Render list of dicts as a clean Markdown table (unindented)."""
    if not isinstance(data, list) or not data or not all(isinstance(x, dict) for x in data):
        return []
        
    ignore_keys = {
        "vector_id", "vector", "sources", "search_hints", "priority",
        "score", "tier", "label", "status", "had_data", "timestamp",
        "success", "error", "pages_scraped", "data_sources", "data_confidence",
        "company", "entity", "topic"
    }
    
    keys = []
    for item in data:
        for k in item.keys():
            if k.lower() not in ignore_keys and k not in keys:
                keys.append(k)
                
    if not keys:
        return []
        
    def _pretty_key(s: str) -> str:
        if not s:
            return ""
        words = re.split(r"[_\-]+", str(s))
        processed = []
        for word in words:
            if not word:
                continue
            w_lower = word.lower()
            if w_lower in {"ai", "ml", "sql", "url", "pdf", "api", "vs"}:
                processed.append(word.upper())
            else:
                processed.append(word.capitalize())
        return " ".join(processed)
        
    headers = [_pretty_key(k) for k in keys]
    
    lines = [""] # add empty line before table
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    
    for item in data:
        row_cells = []
        for k in keys:
            val = item.get(k, "")
            if val is None:
                val = ""
            elif isinstance(val, list):
                val = ", ".join(str(x) for x in val if x not in (None, ""))
            elif isinstance(val, dict):
                val = "; ".join(f"{dk}: {dv}" for dk, dv in val.items() if dv not in (None, ""))
            else:
                val = str(val).replace("\n", " ").replace("|", "\\|")
            row_cells.append(val)
        lines.append("| " + " | ".join(row_cells) + " |")
    lines.append("") # add empty line after table
    return lines


def render_value_as_markdown(value, depth=0) -> list[str]:
    """Faithfully render JSON into Markdown bullets. No raw JSON code block."""
    pad = "  " * depth
    lines = []
    
    ignore_keys = {
        "vector_id", "vector", "sources", "search_hints", "priority",
        "score", "tier", "label", "status", "had_data", "timestamp",
        "success", "error", "pages_scraped", "data_sources", "data_confidence",
        "company", "entity", "topic"
    }

    def _pretty_key(s: str) -> str:
        if not s:
            return ""
        words = re.split(r"[_\-]+", str(s))
        processed = []
        for word in words:
            if not word:
                continue
            w_lower = word.lower()
            if w_lower in {"ai", "ml", "sql", "url", "pdf", "api", "vs"}:
                processed.append(word.upper())
            else:
                processed.append(word.capitalize())
        return " ".join(processed)

    if isinstance(value, dict):
        for k, v in value.items():
            if k.lower() in ignore_keys:
                continue
            if v is None or v == "" or v == [] or v == {}:
                continue
            
            pretty_k = _pretty_key(k)
            if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
                lines.append(f"{pad}- **{pretty_k}:**")
                lines.extend(render_value_as_markdown_table(v))
            elif isinstance(v, (dict, list)):
                lines.append(f"{pad}- **{pretty_k}:**")
                lines.extend(render_value_as_markdown(v, depth + 1))
            else:
                lines.append(f"{pad}- **{pretty_k}:** {v}")
                
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                lines.extend(render_value_as_markdown(item, depth))
            elif item not in (None, ""):
                lines.append(f"{pad}- {item}")
    else:
        if value not in (None, ""):
            lines.append(f"{pad}- {value}")
            
    return lines


def write_partial_final(folder: str, session: dict, vector_results: list[dict], error: str = ""):
    legacy_path = os.path.join(folder, "03_final_analysis_output.txt")
    path = os.path.join(folder, "partial_report.txt")
    final_output_path = os.path.join(folder, "final_output.txt")
    
    completed = [v for v in vector_results if v.get("success")]
    failed = [v for v in vector_results if not v.get("success")]

    lines = [
        "# Partial Research Output",
        "",
        f"Session ID: {session.get('id', '')}",
        f"Status: {session.get('status', '')}",
        f"Last Updated: {datetime.now().isoformat()}",
        "",
        f"Completed vectors: {len(completed)}/{len(vector_results)}",
    ]
    if error:
        lines.extend(["", "## Failure / Stop Reason", error])

    for idx, result in enumerate(vector_results, 1):
        vector = result.get("vector") or {}
        lines.extend([
            "",
            f"## {idx}. {vector.get('topic', 'Sub-topic')}",
            "",
            f"- Success: {result.get('success')}",
            f"- Pages scraped: {result.get('pages_scraped', 0)}",
            f"- Error: {result.get('error') or 'None'}",
            "",
            "### Sources",
        ])
        sources = result.get("sources") or []
        if sources:
            for src in sources:
                lines.append(f"- [{src.get('title') or src.get('url')}]({src.get('url')})")
        else:
            lines.append("- No sources captured.")

        data = result.get("data")
        if data:
            lines.extend(["", "### Extracted Data"])
            lines.extend(render_value_as_markdown(data))

    if failed:
        lines.extend(["", "## Failed / Empty Vectors"])
        for result in failed:
            vector = result.get("vector") or {}
            lines.append(f"- {vector.get('topic', 'Sub-topic')}: {result.get('error') or 'No data returned'}")

    for p in [path, legacy_path, final_output_path]:
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except Exception:
            pass
    return path


def write_final_synthesis(folder: str, synthesis: dict, version: str = "v1"):
    legacy_path = os.path.join(folder, "03_final_analysis_output.txt")
    final_output_path = os.path.join(folder, "final_output.txt")
    
    # Path for versioned report
    v_path = os.path.join(folder, f"final_report_{version}.txt")
    latest_path = os.path.join(folder, "final_report.txt")
    
    lines = [
        f"# {synthesis.get('title', 'Research Report')}",
        "",
        "## Executive Summary",
        synthesis.get("summary", ""),
        "",
        "## Key Takeaways",
    ]
    for item in synthesis.get("key_takeaways") or []:
        lines.append(f"- {item}")

    for section in synthesis.get("sections") or []:
        lines.extend(["", f"## {section.get('title', 'Section')}", ""])
        lines.append(section.get("content", ""))
        findings = section.get("key_findings") or []
        if findings:
            lines.extend(["", "### Key Findings"])
            for finding in findings:
                lines.append(f"- {finding}")
        data = section.get("data")
        if data:
            lines.extend(["", "### Data"])
            if isinstance(data, list) and data and all(isinstance(x, dict) for x in data):
                lines.extend(render_value_as_markdown_table(data))
            else:
                lines.extend(render_value_as_markdown(data))

    lines.extend(["", "## Sources"])
    for src in synthesis.get("sources") or []:
        lines.append(f"- [{src.get('title') or src.get('url')}]({src.get('url')})")

    # Write to all relevant files
    targets = [v_path, latest_path, legacy_path, final_output_path]
    for p in targets:
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except Exception as e:
            print(f"Failed to write final synthesis to {p}: {e}")
            
    return latest_path


def write_blueprint(folder: str, blueprint: dict):
    path = os.path.join(folder, "blueprint.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(blueprint, f, indent=2, default=str)
    return path


def load_blueprint(folder: str) -> dict:
    path = os.path.join(folder, "blueprint.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load blueprint: {e}")
    return {"sections": [], "presentation_rules": {}}


def write_heading_draft(folder: str, heading_id: str, data: dict):
    draft_dir = os.path.join(folder, "drafts")
    os.makedirs(draft_dir, exist_ok=True)
    path = os.path.join(draft_dir, f"{heading_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    return path


def load_heading_drafts(folder: str) -> dict:
    drafts = {}
    draft_dir = os.path.join(folder, "drafts")
    if os.path.exists(draft_dir):
        for f_name in os.listdir(draft_dir):
            if f_name.endswith(".json"):
                heading_id = f_name[:-5]
                path = os.path.join(draft_dir, f_name)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        drafts[heading_id] = json.load(f)
                except Exception as e:
                    print(f"Failed to load draft {heading_id}: {e}")
    return drafts
