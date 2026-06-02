"""
RunawayScout — AI-Powered Web Scraping & Data Intelligence Tool
Main Flask application with SSE streaming, deep scraping, Perplexity discovery, and SQLite persistence
"""
import json
import os
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response, send_file
from engine import extractor
from engine.scraper import fetch_page, _run_async
from engine.compiler import compile_from_urls
from engine.deep_extractor import deep_research_company, configure_perplexity, deep_research_vector
from engine.persistence import (
    save_result, save_partial, get_result, get_all_results,
    delete_result, cleanup_partials, get_partials,
    save_session, update_session_status, get_session, get_all_sessions, delete_session
)
from engine import discoverer
from engine import session_output
import sys
import queue
import concurrent.futures

# Fix Windows console encoding (cp1252 can't handle unicode)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# --- Configuration ---
def _load_api_keys():
    keys = []
    # 1. Load from api_keys.txt if it exists
    keys_file = os.path.join(os.path.dirname(__file__), "api_keys.txt")
    if os.path.exists(keys_file):
        with open(keys_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # split by comma just in case user pastes comma-separated keys in the file
                    keys.extend([k.strip() for k in line.split(",") if k.strip()])
    
    # 2. Load from environment variables
    env_keys = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY") or ""
    if env_keys:
        keys.extend([k.strip() for k in env_keys.split(",") if k.strip()])
        
    # Deduplicate while preserving order
    seen = set()
    unique_keys = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            unique_keys.append(k)
            
    return ",".join(unique_keys)

API_KEY = _load_api_keys()
if not API_KEY:
    print("[!] Warning: No keys found in api_keys.txt or environment variables. Web server will start, but you must add your key in the settings modal in the UI to run research.")
    API_KEY = ""
PERPLEXITY_KEY = ""  # User can set via /api/config or env var
YOUTUBE_KEY = os.environ.get("YOUTUBE_API_KEY", "")  # Optional YouTube Data API key

app = Flask(__name__)
# Track which companies should be skipped (keyed by stream_id)
skip_requests = {}
# Track active background source discovery threads (keyed by session_id)
discovery_tasks = {}


def run_presenter_for_session(output_folder: str, output_format: str) -> str:
    fmt = (output_format or "docx").lower().strip()
    if fmt == "excel":
        fmt = "xlsx"
    if fmt not in {"docx", "html", "pdf", "xlsx"}:
        fmt = "docx"

    present_py = Path(__file__).parent / "present.py"
    if not present_py.exists():
        present_py = Path("present.py").resolve()

    subprocess.run(
        [sys.executable, str(present_py), output_folder, "--formats", fmt],
        check=True,
    )

    expected = Path(output_folder) / f"report.{fmt}"
    if expected.exists():
        return str(expected)

    html = Path(output_folder) / "report.html"
    if html.exists():
        return str(html)

    raise FileNotFoundError(f"Presenter did not create report.{fmt}")


def _state_payload(session_id, status, completed_vector_ids, vectors, **extra):
    payload = {
        "session_id": session_id,
        "status": status,
        "completed_vector_ids": list(completed_vector_ids),
        "vectors": [
            {
                "id": v.get("id"),
                "topic": v.get("topic"),
                "status": "SUCCESS" if v.get("id") in completed_vector_ids else "EMPTY",
            }
            for v in vectors
        ],
        "total_vectors": len(vectors),
        "completed_vectors": len(completed_vector_ids),
        "rotation_cells": _get_key_rotation_status(),
        "last_updated": datetime.now().isoformat(),
    }
    payload.update(extra)
    return payload


def _get_key_rotation_status():
    try:
        import time
        from engine import extractor
        cells = []
        for (key_idx, tier), state in extractor._cell_states.items():
            cells.append({
                "key_index": key_idx + 1,
                "tier": tier,
                "cooldown_until": state["cooldown_until"],
                "exhausted_today": state["exhausted_today"],
                "is_active": state["cooldown_until"] <= time.time() and not state["exhausted_today"]
            })
        return cells
    except Exception:
        return []

# Initialize Gemini
extractor.configure(API_KEY)

# Initialize Perplexity (from env var if available)
_perp_key = os.environ.get("PERPLEXITY_API_KEY", PERPLEXITY_KEY)
if _perp_key:
    configure_perplexity(_perp_key)

# Ensure outputs directory exists on startup
os.makedirs(os.path.join(os.path.dirname(__file__), "outputs"), exist_ok=True)

# Load past results into memory cache for quick access
_results_cache = {}
try:
    for r in get_all_results():
        _results_cache[r["id"]] = r
except Exception:
    pass


def _debug_log(run_id: str, hypothesis_id: str, location: str, message: str, data: dict):
    try:
        log_path = os.path.join(os.path.dirname(__file__), "debug-02993e.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "sessionId": "02993e",
                "runId": run_id,
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data,
                "timestamp": int(datetime.now().timestamp() * 1000)
            }, default=str) + "\n")
    except Exception:
        pass


@app.route("/api/debug/ping")
def api_debug_ping():
    #region agent log
    _debug_log(
        run_id="initial-debug",
        hypothesis_id="H0",
        location="app.py:api_debug_ping",
        message="Debug ping hit",
        data={"ok": True}
    )
    #endregion
    return jsonify({"ok": True})


def _store_result(result_id: str, result: dict):
    """Save result to both memory cache and SQLite."""
    _results_cache[result_id] = result
    try:
        save_result(result_id, result)
    except Exception as e:
        print(f"  [!] Persistence save failed: {e}")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/config", methods=["POST"])
def api_config():
    """Set API keys at runtime. Gemini keys are APPENDED to the rotation pool."""
    data = request.json or {}
    updated = []
    if data.get("perplexity_key"):
        configure_perplexity(data["perplexity_key"])
        updated.append("Perplexity API key set")
    if data.get("gemini_key"):
        try:
            key_num = extractor.add_key(data["gemini_key"])
            updated.append(f"Gemini API key added as Key #{key_num}")
        except ValueError as e:
            if "already in the rotation" in str(e):
                updated.append("Gemini API key already in pool (skipped)")
            else:
                return jsonify({"ok": False, "error": str(e)}), 400
    if data.get("youtube_key"):
        global YOUTUBE_KEY
        YOUTUBE_KEY = data["youtube_key"]
        updated.append("YouTube API key set")
    if updated:
        return jsonify({
            "ok": True,
            "message": ", ".join(updated),
            "key_count": extractor.get_key_count(),
            "rotation_cells": _get_key_rotation_status()
        })
    return jsonify({"ok": False, "error": "No key provided"}), 400


@app.route("/api/keys/status", methods=["GET"])
def api_keys_status():
    """Return current API key rotation status."""
    return jsonify({
        "key_count": extractor.get_key_count(),
        "rotation_cells": _get_key_rotation_status()
    })


@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    """Direct scrape mode."""
    data = request.json
    url = data.get("url", "").strip()
    instruction = data.get("instruction", "Extract all relevant data").strip()
    
    if not url:
        return jsonify({"success": False, "error": "URL is required"}), 400
    if not url.startswith("http"):
        url = "https://" + url
    
    try:
        page_data = _run_async(fetch_page(url))
        
        if not page_data["success"]:
            return jsonify({"success": False, "error": f"Failed to fetch: {page_data.get('error')}"})
        
        extraction = extractor.extract(page_data["markdown"], instruction)
        
        result_id = str(uuid.uuid4())[:8]
        result = {
            "id": result_id, "mode": "scrape", "url": url,
            "data": extraction.get("data"),
            "raw_response": extraction.get("raw_response", ""),
            "success": extraction.get("success", False),
            "error": extraction.get("error"),
            "timestamp": datetime.now().isoformat()
        }
        _store_result(result_id, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/discover", methods=["POST"])
def api_discover():
    """Auto-discover mode with Google Search grounding."""
    data = request.json
    query = data.get("query", "").strip()
    instruction = data.get("instruction", "").strip()
    
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400
    
    try:
        full_query = query
        if instruction:
            full_query += f"\n\nAdditional instructions: {instruction}"
        
        result = extractor.research(full_query, instruction)
        
        result_id = str(uuid.uuid4())[:8]
        response_data = {
            "id": result_id, "mode": "discover", "query": query,
            "success": result.get("success", False),
            "data": result.get("data"),
            "summary": result.get("summary", ""),
            "sources": result.get("grounding_sources", []),
            "source_urls": result.get("sources", []),
            "confidence": result.get("confidence", ""),
            "notes": result.get("notes", ""),
            "raw_response": result.get("raw_response", ""),
            "error": result.get("error"),
            "timestamp": datetime.now().isoformat()
        }
        _store_result(result_id, response_data)
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/agent/plan", methods=["POST"])
def api_agent_plan():
    """Stage 1: Generate a research plan (entities, data points, clarifying questions)."""
    data = request.json
    query = data.get("query", "").strip()
    instruction = data.get("instruction", "").strip()
    
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400
        
    try:
        from engine.discoverer import generate_research_plan
        result = generate_research_plan(query, instruction)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/skip/<stream_id>/<company>", methods=["POST"])
def api_skip(stream_id, company):
    """Signal to skip a company during streaming research."""
    if stream_id not in skip_requests:
        skip_requests[stream_id] = set()
    skip_requests[stream_id].add(company.lower().strip())
    return jsonify({"ok": True, "skipped": company})


@app.route("/api/compile/stream", methods=["GET", "POST"])
@app.route("/api/agent/stream", methods=["GET", "POST"])
def api_compile_stream():
    """
    Multi-source compile with SSE streaming.
    Uses deep scraping + Perplexity discovery for data extraction.
    """
    if request.method == "POST":
        data = request.json or {}
        companies = data.get("companies", [])
        data_points = data.get("data_points", [])
        instruction = data.get("instruction", "").strip()
    else:
        companies_param = request.args.get("companies", "[]")
        data_points_param = request.args.get("data_points", "[]")
        try:
            companies = json.loads(companies_param)
        except json.JSONDecodeError:
            companies = []
        try:
            data_points = json.loads(data_points_param)
        except json.JSONDecodeError:
            data_points = []
        
        # Fallback for old ?urls= GET usage
        if not companies and request.args.get("urls"):
            urls = request.args.get("urls", "").split(",")
            companies = [u.strip() for u in urls if u.strip()]
        
        instruction = request.args.get("instruction", "").strip()
    
    if not companies or not data_points:
        return jsonify({"success": False, "error": "Companies and data points required"}), 400
    
    result_id = str(uuid.uuid4())[:8]
    stream_id = str(uuid.uuid4())[:8]
    skip_requests[stream_id] = set()
    
    def generate():
        all_company_data = []
        all_sources = []
        
        try:
            yield _sse_event("status", {
                "message": f"Starting deep research for {len(companies)} entities...",
                "step": 0, "total": len(companies) + 1,
                "stream_id": stream_id,
            })
            
            for i, company in enumerate(companies):
                # Check if this company should be skipped
                if company.lower().strip() in skip_requests.get(stream_id, set()):
                    yield _sse_event("company_done", {
                        "company": company, "step": i + 1, "total": len(companies) + 1,
                        "result": {"company": company, "success": False, "error": "Skipped by user"},
                        "skipped": True,
                        "table_so_far": all_company_data
                    })
                    continue
                
                yield _sse_event("progress", {
                    "message": f"Deep-researching {company}...",
                    "step": i + 1, "total": len(companies) + 1,
                    "company": company
                })
                
                def progress_update(msg):
                    pass  # We can't yield from a callback, but it logs to console
                
                try:
                    result = deep_research_company(
                        company=company,
                        data_points=data_points,
                        instruction=instruction,
                        max_scrape=4,
                        progress_cb=lambda msg: print(f"    [{company}] {msg}")
                    )
                    
                    company_result = {
                        "company": company,
                        "success": result.get("success", False),
                        "data": result.get("data"),
                        "sources": result.get("sources", []),
                        "pages_scraped": result.get("pages_scraped", 0),
                        "pages_extracted": result.get("pages_with_data", 0),
                        "perplexity_sources": result.get("perplexity_sources", 0),
                        "error": result.get("error")
                    }
                    
                    if result.get("success") and result.get("data"):
                        extracted = result["data"]
                        if isinstance(extracted, list) and len(extracted) > 0:
                            extracted = extracted[0]
                        if isinstance(extracted, dict):
                            extracted["company"] = company
                            all_company_data.append(extracted)
                        else:
                            all_company_data.append({"company": company, "raw_data": extracted})
                    
                    for s in (result.get("sources") or []):
                        if s not in all_sources:
                            all_sources.append(s)
                    
                    # Save partial result
                    save_partial(stream_id, company, company_result)
                    
                except Exception as e:
                    company_result = {
                        "company": company, "success": False,
                        "data": None, "sources": [], "error": str(e)
                    }
                    save_partial(stream_id, company, company_result)
                
                yield _sse_event("company_done", {
                    "company": company, "step": i + 1, "total": len(companies) + 1,
                    "result": company_result,
                    "table_so_far": all_company_data
                })
            
            # Final
            yield _sse_event("progress", {
                "message": "Compiling final results...",
                "step": len(companies) + 1, "total": len(companies) + 1
            })
            
            final_result = {
                "id": result_id, "mode": "compile",
                "success": len(all_company_data) > 0,
                "data": all_company_data, "merged_data": all_company_data,
                "sources": all_sources,
                "companies": companies,
                "data_points": data_points,
                "instruction": instruction,
                "summary": f"Deep-researched {len(all_company_data)}/{len(companies)} entities.",
                "timestamp": datetime.now().isoformat()
            }
            _store_result(result_id, final_result)
            
            yield _sse_event("done", final_result)
        finally:
            # Cleanup
            skip_requests.pop(stream_id, None)
            cleanup_partials(stream_id)
    
    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive"
    })


@app.route("/api/compile", methods=["POST"])
def api_compile():
    """Non-streaming compile fallback."""
    data = request.json
    companies = data.get("companies", [])
    data_points = data.get("data_points", [])
    instruction = data.get("instruction", "").strip()
    
    try:
        if companies and data_points:
            dp_text = ", ".join(data_points)
            company_text = ", ".join(companies)
            
            research_query = f"""Research details, specifications, features, or rates for these entities: {company_text}

For EACH entity, find information for these parameters: {dp_text}

{instruction}

Return JSON: {{"data": [one object per entity/company], "summary": "...", "sources": [...]}}"""
            
            result = extractor.research(research_query)
            
            result_id = str(uuid.uuid4())[:8]
            response_data = {
                "id": result_id, "mode": "compile",
                "success": result.get("success", False),
                "data": result.get("data"), "merged_data": result.get("data"),
                "summary": result.get("summary", ""),
                "sources": result.get("grounding_sources", []),
                "raw_response": result.get("raw_response", ""),
                "error": result.get("error"),
                "timestamp": datetime.now().isoformat()
            }
            _store_result(result_id, response_data)
            return jsonify(response_data)
        
        return jsonify({"success": False, "error": "Provide companies + data_points"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/export/<result_id>")
def api_export(result_id):
    """Download CSV export."""
    result = _results_cache.get(result_id) or get_result(result_id)
    if not result:
        return jsonify({"error": "Result not found"}), 404
    
    from engine.compiler import _export_to_csv
    data = result.get("merged_data") or result.get("data")
    if data:
        export_path = _export_to_csv(data, "export")
        if export_path and os.path.exists(export_path):
            return send_file(export_path, as_attachment=True)
    
    return jsonify({"error": "No exportable data"}), 404


@app.route("/api/results")
def api_results():
    """Get all results (from cache + SQLite)."""
    # Merge cache and DB
    all_results = {}
    try:
        for r in get_all_results():
            all_results[r["id"]] = r
    except Exception:
        pass
    for rid, r in _results_cache.items():
        all_results[rid] = r
    return jsonify(list(all_results.values()))


@app.route("/api/history")
def api_history():
    """Get research history from SQLite — survives restarts."""
    try:
        results = get_all_results()
        # Return summary info for each
        history = []
        for r in results:
            history.append({
                "id": r.get("id"),
                "mode": r.get("mode"),
                "query": r.get("query", ""),
                "companies": r.get("companies", []),
                "summary": r.get("summary", ""),
                "status": r.get("status", "complete"),
                "timestamp": r.get("timestamp", r.get("created_at", "")),
                "has_data": r.get("data") is not None,
            })
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history/<result_id>")
def api_history_detail(result_id):
    """Get full details of a past research result."""
    result = _results_cache.get(result_id) or get_result(result_id)
    if not result:
        return jsonify({"error": "Not found"}), 404
    return jsonify(result)


@app.route("/api/history/<result_id>", methods=["DELETE"])
def api_history_delete(result_id):
    """Delete a past result."""
    _results_cache.pop(result_id, None)
    deleted = delete_result(result_id)
    return jsonify({"ok": deleted})


@app.route("/api/research/plan", methods=["POST"])
def api_research_session_plan():
    """Stage 1: Analyze raw query and generate clarifying questions."""
    data = request.json or {}
    query = data.get("query", "").strip()
    context = data.get("context", "").strip()
    
    if not query:
        return jsonify({"success": False, "error": "Query is required"}), 400
        
    try:
        #region agent log
        _debug_log(
            run_id="initial-debug",
            hypothesis_id="H1",
            location="app.py:api_research_session_plan:before_generate",
            message="Plan endpoint input received",
            data={"query_len": len(query), "context_len": len(context), "query_preview": query[:120]}
        )
        #endregion
        res = discoverer.generate_clarifying_questions(query, context)
        #region agent log
        _debug_log(
            run_id="initial-debug",
            hypothesis_id="H2",
            location="app.py:api_research_session_plan:after_generate",
            message="Plan generation returned",
            data={"success": res.get("success"), "questions_count": len(res.get("questions", [])), "error": res.get("error")}
        )
        #endregion
        if not res.get("success"):
            return jsonify({"success": False, "error": res.get("error")})
            
        session_id = str(uuid.uuid4())[:8]
        session = {
            "id": session_id,
            "original_query": query,
            "original_context": context,
            "status": "planning",
            "clarification_answers": [],
            "research_vectors": [],
            "created_at": datetime.now().isoformat()
        }
        save_session(session_id, session)
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "questions": res.get("questions", []),
            "assumptions": res.get("assumptions", []),
            "detected_topic": res.get("detected_topic", ""),
            "detected_scope": res.get("detected_scope", "")
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/research/clarify", methods=["POST"])
def api_research_session_clarify_more():
    """Continue Stage 1 after user answers and adds extra free-form clarification."""
    data = request.json or {}
    session_id = data.get("session_id")
    answers = data.get("answers", [])
    user_note = data.get("user_note", "").strip()

    if not session_id:
        return jsonify({"success": False, "error": "session_id is required"}), 400

    session = get_session(session_id)
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404

    if not answers and not user_note:
        return jsonify({"success": False, "error": "Add an answer or a clarification note first."}), 400

    try:
        res = discoverer.continue_clarifying_questions(
            session["original_query"],
            answers,
            user_note,
            context=session.get("original_context", "")
        )
        if not res.get("success"):
            return jsonify({"success": False, "error": res.get("error")})

        update_session_status(
            session_id,
            status="planning",
            clarification_answers=answers
        )

        return jsonify({
            "success": True,
            "session_id": session_id,
            "questions": res.get("questions", []),
            "assumptions": res.get("assumptions", []),
            "detected_topic": res.get("detected_topic", ""),
            "detected_scope": res.get("detected_scope", "")
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


def infer_output_format(query: str, requested: str | None = None) -> str:
    q = query.lower()
    if requested:
        return requested
    if "excel" in q or "spreadsheet" in q or "xlsx" in q:
        return "xlsx"
    if "csv" in q:
        return "csv"
    if "pdf" in q:
        return "pdf"
    if "docx" in q or "word" in q:
        return "docx"
    return "docx"


@app.route("/api/research/refine", methods=["POST"])
def api_research_session_refine():
    """Stage 2: Refine prompt and generate parallel vectors based on user answers."""
    data = request.json or {}
    session_id = data.get("session_id")
    answers = data.get("answers", [])
    output_format = data.get("output_format")
    
    if not session_id:
        return jsonify({"success": False, "error": "session_id is required"}), 400
        
    session = get_session(session_id)
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404
        
    output_format = infer_output_format(session.get("original_query", ""), output_format)

    #region agent log
    _debug_log(
        run_id="initial-debug",
        hypothesis_id="H3",
        location="app.py:api_research_session_refine:session_lookup",
        message="Refine endpoint session lookup",
        data={"session_id": session_id, "session_found": bool(session), "answers_count": len(answers), "output_format": output_format}
    )
    #endregion
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404
        
    try:
        res = discoverer.refine_research_prompt(
            session["original_query"], 
            answers, 
            context=session.get("original_context", "")
        )
        if not res.get("success"):
            return jsonify({"success": False, "error": res.get("error")})
            
        update_session_status(
            session_id,
            status="ready",
            refined_prompt=res.get("refined_prompt", ""),
            clarification_answers=answers,
            research_vectors=res.get("vectors", []),
            output_format=output_format,
            depth=res.get("depth", "standard"),
            effort_estimate=res.get("effort_estimate", {})
        )
        updated_session = get_session(session_id)
        output_folder = session_output.ensure_session_folder(
            session_id,
            updated_session.get("original_query", ""),
            updated_session.get("created_at", "")
        )
        session_output.write_search_parameters(output_folder, updated_session)
        
        # Stage 2 global source discovery and ranked scrape queue generation in a background thread
        import threading
        from engine.deep_extractor import discover_sources_for_session
        thread = threading.Thread(
            target=discover_sources_for_session,
            kwargs={
                "session_id": session_id,
                "vectors": updated_session.get("research_vectors", []),
                "refined_prompt": updated_session.get("refined_prompt", ""),
                "original_query": updated_session.get("original_query", ""),
                "depth": updated_session.get("depth", "standard"),
                "output_folder": output_folder
            }
        )
        discovery_tasks[session_id] = thread
        thread.start()
        
        update_session_status(session_id, status="ready", output_folder=output_folder)
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "refined_prompt": res.get("refined_prompt"),
            "vectors": res.get("vectors"),
            "suggested_data_points": res.get("suggested_data_points"),
            "quality_notes": res.get("quality_notes")
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/research/stream/<session_id>")
def api_research_session_stream(session_id):
    """
    Execute vector-based research session in parallel/sequential stream.
    Synthesizes results and generates the requested export document format.
    """
    session = get_session(session_id)
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404
        
    def generate():
        vectors = session.get("research_vectors", [])
        original_query = session.get("original_query", "")
        output_format = session.get("output_format", "pdf")
        
        # Check if background discovery task is running and wait for it
        thread = discovery_tasks.get(session_id)
        if thread and thread.is_alive():
            yield _sse_event("status", {
                "message": "Waiting for global source discovery to complete...",
                "step": 0, "total": len(vectors) + 2,
                "session_id": session_id,
            })
            thread.join()
            
        output_folder = session.get("output_folder") or session_output.ensure_session_folder(
            session_id,
            original_query,
            session.get("created_at", "")
        )
        session["output_folder"] = output_folder
        try:
            session_output.write_search_parameters(output_folder, session)
        except Exception as e:
            print(f"Failed to write search parameters: {e}")
        #region agent log
        _debug_log(
            run_id="initial-debug",
            hypothesis_id="H4",
            location="app.py:api_research_session_stream:stream_start",
            message="Research stream started",
            data={"session_id": session_id, "vectors_count": len(vectors), "vector_ids": [v.get("id") for v in vectors], "output_format": output_format}
        )
        #endregion
        
        existing_vector_results = session.get("vector_results") or []
        completed_vector_ids = {
            (r.get("vector") or {}).get("id")
            for r in existing_vector_results
            if r.get("success") and (r.get("vector") or {}).get("id")
        }
        all_vector_results = list(existing_vector_results)
        all_sources = []
        seen_source_urls = set()
        for result in all_vector_results:
            for s in result.get("sources") or []:
                url = s.get("url") or s.get("link")
                if url and url in seen_source_urls:
                    continue
                if url:
                    seen_source_urls.add(url)
                all_sources.append(s)

        remaining_count = len([v for v in vectors if v.get("id") not in completed_vector_ids])
        
        # Initialize state.json cursor
        state_payload = _state_payload(
            session_id, "researching", completed_vector_ids, vectors
        )
        session_output.write_state(output_folder, state_payload)

        yield _sse_event("status", {
            "message": f"Starting research for {remaining_count} remaining vectors...",
            "step": 0, "total": len(vectors) + 2,
            "session_id": session_id,
            "output_folder": output_folder,
            "resuming": len(completed_vector_ids) > 0,
            "source_count": len(all_sources),
            "active_rotation_cells": _get_key_rotation_status()
        })
        
        update_session_status(
            session_id,
            "researching",
            output_folder=output_folder,
            vector_results=all_vector_results,
            sources_used=all_sources
        )
        
        vectors_to_research = []
        for i, vector in enumerate(vectors):
            if vector.get("id") in completed_vector_ids:
                prior = next((r for r in all_vector_results if (r.get("vector") or {}).get("id") == vector.get("id")), None)
                yield _sse_event("vector_done", {
                    "vector": vector,
                    "step": i + 1,
                    "total": len(vectors) + 2,
                    "result": prior,
                    "resumed": True,
                    "source_count": len(all_sources),
                    "active_rotation_cells": _get_key_rotation_status()
                })
            else:
                vectors_to_research.append((i, vector))

        if vectors_to_research:
            msg_queue = queue.Queue()
            
            def run_single_vector(idx, vec):
                v_topic = vec.get("topic", "Sub-topic")
                
                def progress_callback(msg):
                    msg_queue.put({
                        "type": "progress",
                        "idx": idx,
                        "vector": vec,
                        "message": f"[{v_topic}] {msg}"
                    })
                
                from engine.extractor import GeminiRateLimitError
                max_vector_retries = 3
                for v_attempt in range(max_vector_retries):
                    try:
                        depth = session.get("depth", "standard")
                        max_scrape = 5 if depth == "surface" else (10 if depth == "standard" else 20)
                        res = deep_research_vector(
                            vector=vec,
                            research_context=original_query,
                            instruction=session.get("refined_prompt", ""),
                            max_scrape=max_scrape,
                            progress_cb=progress_callback,
                            output_folder=output_folder,
                            depth=depth
                        )
                        msg_queue.put({
                            "type": "done",
                            "idx": idx,
                            "vector": vec,
                            "result": res,
                            "success": True
                        })
                        return res
                    except GeminiRateLimitError as rate_err:
                        cooldown = getattr(rate_err, "cooldown_sec", 30.0)
                        msg_queue.put({
                            "type": "status",
                            "idx": idx,
                            "message": f"Rate limit hit. Waiting {cooldown:.1f}s before retry...",
                            "cooldown": cooldown
                        })
                        import time
                        time.sleep(cooldown)
                    except Exception as e:
                        msg_queue.put({
                            "type": "done",
                            "idx": idx,
                            "vector": vec,
                            "success": False,
                            "error": str(e)
                        })
                        return {
                            "vector": vec,
                            "data": {"error": str(e)},
                            "sources": [],
                            "success": False
                        }
                
                err_msg = "Gemini API rate limits exhausted after multiple retries."
                msg_queue.put({
                    "type": "done",
                    "idx": idx,
                    "vector": vec,
                    "success": False,
                    "error": err_msg
                })
                return {
                    "vector": vec,
                    "data": {"error": err_msg},
                    "sources": [],
                    "success": False
                }

            executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
            futures = [executor.submit(run_single_vector, idx, vec) for idx, vec in vectors_to_research]
            
            completed_count = 0
            total_to_do = len(vectors_to_research)
            
            while completed_count < total_to_do:
                try:
                    event = msg_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                e_type = event["type"]
                if e_type == "progress":
                    yield _sse_event("progress", {
                        "message": event["message"],
                        "step": event["idx"] + 1,
                        "total": len(vectors) + 2,
                        "vector": event["vector"],
                        "source_count": len(all_sources),
                        "active_rotation_cells": _get_key_rotation_status()
                    })
                elif e_type == "status":
                    yield _sse_event("status", {
                        "message": event["message"],
                        "step": event["idx"] + 1,
                        "total": len(vectors) + 2,
                        "session_id": session_id,
                        "active_rotation_cells": _get_key_rotation_status()
                    })
                elif e_type == "done":
                    completed_count += 1
                    idx = event["idx"]
                    vec = event["vector"]
                    
                    if event["success"]:
                        res = event["result"]
                    else:
                        error_msg = event.get("error", "Unknown error")
                        res = {
                            "vector": vec,
                            "data": {"error": error_msg},
                            "sources": [],
                            "success": False
                        }
                        try:
                            session_output.append_failure(
                                folder=output_folder,
                                target=vec.get("topic", "Sub-topic"),
                                tier="TIER_5",
                                error=error_msg,
                                action_taken="Mark vector as failed"
                            )
                        except Exception as log_err:
                            print(f"Failed to log vector failure: {log_err}")
                            
                    all_vector_results.append(res)
                    for s in res.get("sources") or []:
                        url = s.get("url") or s.get("link")
                        if url and url in seen_source_urls:
                            continue
                        if url:
                            seen_source_urls.add(url)
                        all_sources.append(s)
                        
                    try:
                        session_output.append_raw_vector(output_folder, vec, res)
                        session_output.write_partial_final(output_folder, session, all_vector_results)
                        session_output.write_sources_ledger(output_folder, all_sources)
                    except Exception as e:
                        print(f"Failed to write partial output for {vec.get('topic')}: {e}")
                        
                    completed_vector_ids.add(vec.get("id"))
                    state_payload = _state_payload(
                        session_id, "researching", completed_vector_ids, vectors
                    )
                    session_output.write_state(output_folder, state_payload)
                    
                    update_session_status(
                        session_id,
                        "researching",
                        output_folder=output_folder,
                        vector_results=all_vector_results,
                        sources_used=all_sources,
                        result_data={
                            "success": False,
                            "partial": True,
                            "message": "Research is in progress or can be resumed.",
                            "vectors_completed": len([r for r in all_vector_results if r.get("success")]),
                            "vectors_total": len(vectors),
                            "output_folder": output_folder
                        }
                    )
                    
                    yield _sse_event("vector_done", {
                        "vector": vec,
                        "step": idx + 1,
                        "total": len(vectors) + 2,
                        "result": res,
                        "source_count": len(all_sources),
                        "active_rotation_cells": _get_key_rotation_status()
                    })
            executor.shutdown(wait=True)
                 # Step 2: Synthesis (First Pass)
        yield _sse_event("progress", {
            "message": "Synthesizing first-pass report (v1)...",
            "step": len(vectors) + 1, "total": len(vectors) + 2,
            "source_count": len(all_sources),
            "active_rotation_cells": _get_key_rotation_status()
        })
        
        synthesis = None
        synthesis_stream = extractor.synthesize_research_stream(
            vectors_data=all_vector_results,
            original_query=original_query,
            format_hint=output_format,
            output_folder=output_folder,
            vectors=vectors
        )
        
        # Clear out final_report_v1.md so we can append cleanly
        v1_path = os.path.join(output_folder, "final_report_v1.md")
        try:
            if os.path.exists(v1_path):
                os.remove(v1_path)
        except Exception:
            pass

        chunks = []
        for chunk in synthesis_stream:
            if isinstance(chunk, str):
                chunks.append(chunk)
                try:
                    with open(v1_path, "a", encoding="utf-8") as f:
                        f.write(chunk)
                except Exception:
                    pass
                yield _sse_event("progress", {
                    "message": f"Synthesizing v1: {chunk}",
                    "step": len(vectors) + 1, "total": len(vectors) + 2,
                    "source_count": len(all_sources),
                    "active_rotation_cells": _get_key_rotation_status()
                })
            else:
                synthesis = chunk
        
        #region agent log
        _debug_log(
            run_id="initial-debug",
            hypothesis_id="H5",
            location="app.py:api_research_session_stream:after_synthesis",
            message="Synthesis returned",
            data={"is_dict": isinstance(synthesis, dict), "success": synthesis.get("success") if isinstance(synthesis, dict) else None, "error": synthesis.get("error") if isinstance(synthesis, dict) else "non-dict"}
        )
        #endregion
        
        if isinstance(synthesis, dict) and not synthesis.get("success", True):
            error_msg = synthesis.get("error", "Failed to synthesize findings")

            try:
                session_output.append_failure(
                    folder=output_folder,
                    target="Synthesis Pass",
                    tier="TIER_1",
                    error=error_msg,
                    action_taken="AI synthesis failed; running deterministic fallback presenter",
                )
            except Exception:
                pass

            state_payload = _state_payload(
                session_id,
                "incomplete_fallback",
                completed_vector_ids,
                vectors,
                synthesis_mode="fallback_no_api",
                error=error_msg,
            )
            session_output.write_state(output_folder, state_payload)

            try:
                fallback_py = Path(__file__).parent / "fallback_synth.py"
                subprocess.run(
                    [sys.executable, str(fallback_py), output_folder],
                    check=True,
                )
                output_file_path = run_presenter_for_session(output_folder, output_format)
            except Exception as fallback_err:
                output_file_path = session_output.write_partial_final(
                    output_folder,
                    session,
                    all_vector_results,
                    f"{error_msg}\nFallback also failed: {fallback_err}",
                )

            update_session_status(
                session_id,
                status="incomplete_fallback",
                result_data={
                    "success": False,
                    "partial": True,
                    "synthesis_mode": "fallback_no_api",
                    "error": error_msg,
                    "output_folder": output_folder,
                },
                output_folder=output_folder,
                output_file_path=output_file_path,
                vector_results=all_vector_results,
                sources_used=all_sources,
            )

            yield _sse_event("done", {
                "session_id": session_id,
                "status": "incomplete_fallback",
                "synthesis": {
                    "title": f"Partial Report: {original_query}",
                    "summary": "AI synthesis failed, so a deterministic fallback report was generated from saved extracted data.",
                    "sections": [],
                    "key_takeaways": [],
                    "sources": all_sources,
                },
                "output_file_path": output_file_path,
                "output_folder": output_folder,
                "sources": all_sources,
            })
            return

        # Write final synthesis v1 to final_report.md
        if isinstance(synthesis, dict):
            session_output.write_final_synthesis(output_folder, synthesis, version="v1")

        # Step 3: Check budget & quota for Re-queue
        rotation_cells = _get_key_rotation_status()
        has_quota = any(cell.get("is_active") for cell in rotation_cells)
        
        # Scan extracted/ directory for LOW_COVERAGE vectors
        low_coverage_vector_ids = []
        extracted_dir = os.path.join(output_folder, "extracted")
        if os.path.exists(extracted_dir):
            for f_name in os.listdir(extracted_dir):
                if f_name.endswith(".json"):
                    path = os.path.join(extracted_dir, f_name)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            payload = json.load(f)
                            if payload.get("status") == "LOW_COVERAGE":
                                low_coverage_vector_ids.append(payload.get("vector_id"))
                    except Exception:
                        pass
        
        v2_eligible = False
        if has_quota and low_coverage_vector_ids:
            yield _sse_event("progress", {
                "message": f"Found {len(low_coverage_vector_ids)} low coverage vectors under synthesis budget. Starting re-queue pass...",
                "step": len(vectors) + 1, "total": len(vectors) + 2,
                "source_count": len(all_sources)
            })
            
            # Run one extra pass per low coverage vector
            for v_id in low_coverage_vector_ids:
                vector = next((v for v in vectors if v.get("id") == v_id), None)
                if not vector:
                    continue
                topic = vector.get("topic", "Sub-topic")
                
                # Clear ranked scrape queue for this vector to trigger rediscovery
                queue_path = os.path.join(output_folder, "scrape_queue.json")
                if os.path.exists(queue_path):
                    try:
                        with open(queue_path, "r", encoding="utf-8") as f:
                            all_queue_sources = json.load(f)
                        filtered_sources = [s for s in all_queue_sources if s.get("vector_id") != v_id]
                        with open(queue_path, "w", encoding="utf-8") as f:
                            json.dump(filtered_sources, f, indent=2, default=str)
                    except Exception:
                        pass
                
                yield _sse_event("progress", {
                    "message": f"Re-researching {topic} with alternate discovery...",
                    "step": len(vectors) + 1, "total": len(vectors) + 2,
                    "vector": vector,
                    "source_count": len(all_sources)
                })
                
                from engine.extractor import GeminiRateLimitError
                max_vector_retries = 3
                vector_success = False
                
                for v_attempt in range(max_vector_retries):
                    try:
                        res = deep_research_vector(
                            vector=vector,
                            research_context=original_query,
                            instruction=session.get("refined_prompt", ""),
                            max_scrape=4,
                            progress_cb=lambda msg: print(f"    [Re-queue Vector: {topic}] {msg}"),
                            output_folder=output_folder
                        )
                        
                        # Update in-memory collections
                        all_vector_results = [r for r in all_vector_results if (r.get("vector") or {}).get("id") != v_id]
                        all_vector_results.append(res)
                        
                        for s in res.get("sources") or []:
                            url = s.get("url") or s.get("link")
                            if url and url not in seen_source_urls:
                                seen_source_urls.add(url)
                                all_sources.append(s)
                                
                        # Check if it was successfully enriched (no longer low coverage)
                        vector_payload_path = os.path.join(extracted_dir, f"{v_id}.json")
                        if os.path.exists(vector_payload_path):
                            with open(vector_payload_path, "r", encoding="utf-8") as f:
                                updated_payload = json.load(f)
                                if updated_payload.get("status") == "SUCCESS":
                                    v2_eligible = True
                        vector_success = True
                        break
                    except GeminiRateLimitError as rate_err:
                        cooldown = getattr(rate_err, "cooldown_sec", 30.0)
                        print(f"    [Rate Limit] All keys in cooldown during re-research. Waiting {cooldown:.1f}s (attempt {v_attempt+1}/{max_vector_retries})...")
                        yield _sse_event("status", {
                            "message": f"All API keys are in cooldown. Waiting {cooldown:.1f}s before retrying re-research...",
                            "step": len(vectors) + 1, "total": len(vectors) + 2,
                            "session_id": session_id,
                            "active_rotation_cells": _get_key_rotation_status()
                        })
                        import time
                        time.sleep(cooldown)
                    except Exception as e:
                        print(f"Error in re-queue for vector {topic}: {e}")
                        vector_success = True
                        break
                    
            try:
                session_output.write_sources_ledger(output_folder, all_sources)
                session_output.write_sources_log_csv(output_folder, all_sources, original_query)
            except Exception:
                pass
                
        # Step 4: Second Pass Synthesis if eligible
        if v2_eligible:
            yield _sse_event("progress", {
                "message": "Enriched findings found! Synthesizing final report (v2)...",
                "step": len(vectors) + 1, "total": len(vectors) + 2,
                "source_count": len(all_sources)
            })
            
            synthesis_v2 = None
            synthesis_stream_v2 = extractor.synthesize_research_stream(
                vectors_data=all_vector_results,
                original_query=original_query,
                format_hint=output_format,
                output_folder=output_folder,
                vectors=vectors
            )
            
            v2_path = os.path.join(output_folder, "final_report_v2.md")
            try:
                if os.path.exists(v2_path):
                    os.remove(v2_path)
            except Exception:
                pass

            chunks_v2 = []
            for chunk in synthesis_stream_v2:
                if isinstance(chunk, str):
                    chunks_v2.append(chunk)
                    try:
                        with open(v2_path, "a", encoding="utf-8") as f:
                            f.write(chunk)
                    except Exception:
                        pass
                    yield _sse_event("progress", {
                        "message": f"Synthesizing v2: {chunk}",
                        "step": len(vectors) + 1, "total": len(vectors) + 2,
                        "source_count": len(all_sources)
                    })
                else:
                    synthesis_v2 = chunk
                    
            if isinstance(synthesis_v2, dict) and synthesis_v2.get("success", True):
                synthesis = synthesis_v2
                session_output.write_final_synthesis(output_folder, synthesis, version="v2")
                yield _sse_event("progress", {
                    "message": "Synthesis v2 complete.",
                    "step": len(vectors) + 1, "total": len(vectors) + 2
                })

        # Step 5: Document Generation
        yield _sse_event("progress", {
            "message": f"Generating output report in {output_format.upper()} format...",
            "step": len(vectors) + 2, "total": len(vectors) + 2,
            "source_count": len(all_sources),
            "active_rotation_cells": _get_key_rotation_status()
        })
        
        output_file_path = ""
        try:
            output_file_path = run_presenter_for_session(output_folder, output_format)
        except Exception as e:
            print(f"Error running presenter: {e}")
            output_file_path = os.path.join(output_folder, "partial_report.md")
            
        actual_work = {
            "sources_to_discover": len(all_sources),
            "pages_to_scrape": sum(r.get("pages_scraped", 0) for r in all_vector_results),
            "synthesis_passes": 2 if v2_eligible else 1
        }
        estimated_work = session.get("effort_estimate") or {}
        try:
            session_output.append_run_log(output_folder, estimated_work, actual_work)
        except Exception as e:
            print(f"Failed to write run log: {e}")

        state_payload = _state_payload(
            session_id,
            "complete",
            completed_vector_ids,
            vectors,
            v2_eligible=v2_eligible,
        )
        session_output.write_state(output_folder, state_payload)

        update_session_status(
            session_id,
            status="complete",
            result_data=synthesis,
            output_file_path=output_file_path,
            output_folder=output_folder,
            sources_used=all_sources,
            vector_results=all_vector_results
        )
        
        final_payload = {
            "session_id": session_id,
            "status": "complete",
            "synthesis": synthesis,
            "output_file_path": output_file_path,
            "output_folder": output_folder,
            "sources": all_sources
        }
        
        yield _sse_event("done", final_payload)
        
    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive"
    })


@app.route("/api/research/export/<session_id>")
def api_research_export(session_id):
    """Download the generated document for a research session."""
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    file_path = session.get("output_file_path")
    if file_path and os.path.exists(file_path):
        filename = os.path.basename(file_path)
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    return jsonify({"error": "No exportable document available for this session."}), 404


@app.route("/api/research/sessions")
def api_research_sessions():
    """Get all research sessions history."""
    try:
        sessions = get_all_sessions()
        return jsonify(sessions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/research/log_alert", methods=["POST"])
def api_research_log_alert():
    """Log client alert message to alert.txt in the active session's folder."""
    try:
        data = request.json or {}
        session_id = data.get("session_id")
        message = data.get("message")
        alert_type = data.get("type", "info")
        elapsed_time = data.get("elapsed_time", "N/A")
        
        if not session_id:
            return jsonify({"error": "session_id is required"}), 400
            
        session = get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
            
        output_folder = session.get("output_folder")
        if not output_folder:
            return jsonify({"error": "Session output folder not found"}), 404
            
        os.makedirs(output_folder, exist_ok=True)
        alert_file_path = os.path.join(output_folder, "alert.txt")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(alert_file_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] ALERT: {message}\n")
            f.write(f"Type: {alert_type}\n")
            f.write(f"Elapsed Time: {elapsed_time}\n")
            f.write("-" * 50 + "\n")
            
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/api/research/sessions/<session_id>")
def api_research_session_detail(session_id):
    """Get a single session details."""
    session = get_session(session_id)
    if not session:
        return jsonify({"error": "Not found"}), 404
    return jsonify(session)


@app.route("/api/research/sessions/<session_id>", methods=["DELETE"])
def api_research_session_delete(session_id):
    """Delete a research session."""
    deleted = delete_session(session_id)
    return jsonify({"ok": deleted})


@app.route("/api/research/refine_result", methods=["POST"])
def api_research_refine_result():
    """
    Refines the final result of a research session based on user comments/feedback
    without re-scraping the web.
    """
    data = request.json or {}
    session_id = data.get("session_id")
    refinement_instruction = data.get("refinement_instruction", "").strip()
    
    if not session_id or not refinement_instruction:
        return jsonify({"success": False, "error": "session_id and refinement_instruction are required"}), 400
        
    session = get_session(session_id)
    if not session:
        return jsonify({"success": False, "error": "Session not found"}), 404
        
    if session.get("status") != "complete":
        return jsonify({"success": False, "error": "Can only refine completed research sessions."}), 400
        
    existing_synthesis = session.get("result_data")
    if not existing_synthesis:
        return jsonify({"success": False, "error": "No existing result data found to refine."}), 400
        
    try:
        # Refine the synthesis JSON
        refined_synthesis = extractor.refine_synthesis(existing_synthesis, refinement_instruction)
        
        if not refined_synthesis.get("success", True):
            return jsonify({"success": False, "error": refined_synthesis.get("error", "Refinement failed.")})
            
        # Regenerate report via present.py
        output_format = session.get("output_format", "pdf")
        output_folder = session.get("output_folder")

        if output_folder:
            session_output.write_final_synthesis(output_folder, refined_synthesis, version="v1")
            output_file_path = run_presenter_for_session(output_folder, output_format)
        else:
            return jsonify({"success": False, "error": "No output folder found for session."}), 400
        
        # Persist updated session
        update_session_status(
            session_id,
            status="complete",
            result_data=refined_synthesis,
            output_file_path=output_file_path
        )
        
        # Include sources_used from session so frontend can display them
        sources_used = session.get("sources_used", [])
        
        return jsonify({
            "success": True,
            "synthesis": refined_synthesis,
            "output_file_path": output_file_path,
            "sources_used": sources_used
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


def _sse_event(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data, default=str)}\n\n"


if __name__ == "__main__":
    print("\n[*] RunawayScout is starting...")
    print("    Open http://localhost:5000 in your browser")
    print(f"    Perplexity: {'Yes, configured' if _perp_key else 'No, not set (set PERPLEXITY_API_KEY env var)'}")
    print(f"    Database: scout_results.db")
    print()
    app.run(debug=True, port=5000, use_reloader=False, threaded=True)
