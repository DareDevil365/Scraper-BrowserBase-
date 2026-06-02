#!/usr/bin/env python3
"""
fallback_synth.py â€” No-API deterministic synthesis assembler.

Referenced by Synthesis.md Â§7. Runs when every (key x model) cell is exhausted,
OR manually against any run_<id>/ folder. Does ZERO model inference: it only
structures the on-disk extracted JSON into a Markdown deliverable and stamps it
as mechanically assembled.

Usage:
    python fallback_synth.py /path/to/run_<id>

Reads (input contract, Synthesis.md Â§1):
    run_<id>/extracted/<vector_id>.json   # per-vector payloads
    run_<id>/state.json                   # vector list + status
    run_<id>/sources.json                 # (optional) per-vector sources

Writes:
    run_<id>/final_report_fallback.md     # never overwrites v1/v2
    run_<id>/state.json                   # updated with fallback flags (Â§7.6)
"""

import json
import os
import sys
import glob
import re
from datetime import datetime, timezone

# --- status taxonomy (mirrors API_Limit_Tuning.md Â§8) -----------------------
RENDER_DATA = {"SUCCESS", "PARTIAL"}
FLAG_THIN = {"LOW_COVERAGE"}
PLACEHOLDER = {"EMPTY", "NOT_APPLICABLE", "FAILED", "FAILED_RETRYABLE",
               "NO_PUBLIC_DATA", "SOFT_404", "LOGIN_GATED"}

INTERNAL_KEYS = {
    "vector_id", "vector", "sources", "search_hints", "priority",
    "score", "tier", "label", "status", "had_data", "timestamp",
    "success", "error", "pages_scraped", "data_sources", "data_confidence",
}


def _load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _count_leaves(obj):
    """Richness score: number of non-null leaf fields."""
    if obj is None:
        return 0
    if isinstance(obj, dict):
        return sum(_count_leaves(v) for v in obj.values())
    if isinstance(obj, list):
        return sum(_count_leaves(v) for v in obj)
    return 0 if (obj == "" or obj is None) else 1


def load_payloads(run_dir):
    """Load every extracted/<vector_id>.json into {vector_id: [payloads...]}."""
    groups = {}
    for path in glob.glob(os.path.join(run_dir, "extracted", "*.json")):
        vid = os.path.splitext(os.path.basename(path))[0]
        payload = _load_json(path)
        if payload is None:
            continue
        ts = os.path.getmtime(path)
        groups.setdefault(vid, []).append((ts, payload))
    return groups


def dedupe_richest(groups):
    """Synthesis.md Â§2: keep single richest successful payload per vector_id."""
    chosen = {}
    for vid, items in groups.items():
        # rank by richness, tie-break by most recent timestamp
        best = max(items, key=lambda t: (_count_leaves(t[1]), t[0]))
        chosen[vid] = best[1]
    return chosen


def render_value_as_markdown_table(data) -> list[str]:
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


def render_value(value, depth=0):
    """Faithfully render JSON into Markdown bullets/tables. No prose generation."""
    pad = "  " * depth
    lines = []
    if isinstance(value, dict):
        for k, v in value.items():
            if k in INTERNAL_KEYS:
                continue
            if v is None or v == "":
                continue
            if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
                lines.append(f"{pad}- **{k}:**")
                lines.extend(render_value_as_markdown_table(v))
            elif isinstance(v, (dict, list)):
                lines.append(f"{pad}- **{k}:**")
                lines.extend(render_value(v, depth + 1))
            else:
                lines.append(f"{pad}- **{k}:** {v}")
    elif isinstance(value, list):
        # Check if list of dicts directly
        if value and all(isinstance(x, dict) for x in value):
            lines.extend(render_value_as_markdown_table(value))
        else:
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.extend(render_value(item, depth))
                elif item not in (None, ""):
                    lines.append(f"{pad}- {item}")
    else:
        if value not in (None, ""):
            lines.append(f"{pad}- {value}")
    return lines


def vector_title(vid, payload, state_vectors):
    meta = state_vectors.get(vid, {})
    if isinstance(meta, dict) and meta.get("topic"):
        return meta["topic"]
    if isinstance(payload, dict):
        for key in ("topic", "company", "title"):
            if payload.get(key):
                return payload[key]
    return vid


def status_for(vid, payload, state_vectors):
    meta = state_vectors.get(vid, {})
    if isinstance(meta, dict) and meta.get("status"):
        return meta["status"]
    return "SUCCESS" if _count_leaves(payload) > 2 else "LOW_COVERAGE"


def build_report(run_dir, chosen, state):
    state_vectors = {}
    for v in state.get("vectors", []) if isinstance(state, dict) else []:
        if isinstance(v, dict) and "id" in v:
            state_vectors[v["id"]] = v

    total = state.get("total_vectors") or len(state.get("completed_vector_ids", [])) or len(chosen)
    completed = len(chosen)
    now = datetime.now(timezone.utc).isoformat()

    out = []
    out.append("# Research Report (Mechanically Assembled)\n")
    out.append("> âš ï¸ MECHANICALLY ASSEMBLED â€” NO AI SYNTHESIS.")
    out.append("> Generated because all API quota cells were exhausted.")
    out.append(f"> Completed {completed}/{total} vectors. "
               "Re-run after quota reset for the AI report.\n")
    out.append(f"_Generated: {now}_\n")
    out.append("---\n")

    upgradeable = []
    for i, (vid, payload) in enumerate(sorted(chosen.items()), 1):
        title = vector_title(vid, payload, state_vectors)
        status = status_for(vid, payload, state_vectors)
        out.append(f"## {i}. {title}")
        out.append(f"_vector: `{vid}` Â· status: `{status}`_\n")

        if status in PLACEHOLDER:
            out.append(f"_No usable data captured for this section ({status})._\n")
        else:
            if status in FLAG_THIN:
                out.append("> ⚠️ low coverage — based on limited data.\n")
                upgradeable.append(vid)

            data_only = None
            if isinstance(payload, dict):
                data_only = payload.get("data") or payload.get("extracted_data")
            else:
                data_only = payload

            body = render_value(data_only)

            if body:
                out.extend(body)
            else:
                out.append("_No populated user-facing fields._")

            out.append("")
        out.append("---\n")

    return "\n".join(out), completed, total, upgradeable


def update_state(run_dir, state, completed, total, upgradeable):
    """Synthesis.md Â§7.6 â€” write machine-readable incompleteness flags."""
    if not isinstance(state, dict):
        state = {}
    state["synthesis_mode"] = "fallback_no_api"
    state["completed_vectors"] = completed
    state["total_vectors"] = total
    state["upgradeable"] = upgradeable
    state["status"] = "incomplete_fallback"
    with open(os.path.join(run_dir, "state.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def main():
    if len(sys.argv) != 2:
        print("Usage: python fallback_synth.py /path/to/run_<id>")
        sys.exit(1)

    run_dir = sys.argv[1]
    if not os.path.isdir(run_dir):
        print(f"Error: {run_dir} is not a directory")
        sys.exit(1)

    state = _load_json(os.path.join(run_dir, "state.json"), default={})
    groups = load_payloads(run_dir)
    if not groups:
        print("No extracted payloads found â€” nothing to assemble.")
        sys.exit(2)

    chosen = dedupe_richest(groups)
    report, completed, total, upgradeable = build_report(run_dir, chosen, state)

    # never overwrite v1/v2 â€” write our own filename only
    out_path = os.path.join(run_dir, "final_report_fallback.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)

    update_state(run_dir, state, completed, total, upgradeable)

    print(f"Wrote {out_path}")
    print(f"Completed {completed}/{total} vectors; "
          f"{len(upgradeable)} marked upgradeable.")


if __name__ == "__main__":
    main()