"""
persistence.py — SQLite-based storage for research results
Ensures data survives server crashes, restarts, and failures.
"""
import json
import os
import sqlite3
import threading
from datetime import datetime

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scout_results.db")
_local = threading.local()


def _get_conn():
    conn = getattr(_local, 'conn', None)
    if conn is None:
        conn = sqlite3.connect(_DB_PATH)
        conn.row_factory = sqlite3.Row
        _init_db(conn)
        _local.conn = conn
    return conn



def _init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id TEXT PRIMARY KEY,
            mode TEXT,
            query TEXT,
            companies TEXT,
            data_points TEXT,
            instruction TEXT,
            data TEXT,
            sources TEXT,
            summary TEXT,
            status TEXT DEFAULT 'complete',
            raw_response TEXT,
            error TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS partial_results (
            stream_id TEXT,
            company TEXT,
            data TEXT,
            sources TEXT,
            success INTEGER,
            error TEXT,
            created_at TEXT,
            PRIMARY KEY (stream_id, company)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS research_sessions (
            id TEXT PRIMARY KEY,
            original_query TEXT,
            original_context TEXT,
            refined_prompt TEXT,
            clarification_answers TEXT,
            research_vectors TEXT,
            output_format TEXT,
            status TEXT DEFAULT 'planning',
            result_data TEXT,
            output_file_path TEXT,
            output_folder TEXT,
            sources_used TEXT,
            vector_results TEXT,
            quality_scores TEXT,
            depth TEXT,
            effort_estimate TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    # Migration: check and add original_context column if missing from existing db
    try:
        conn.execute("ALTER TABLE research_sessions ADD COLUMN original_context TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE research_sessions ADD COLUMN output_folder TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE research_sessions ADD COLUMN vector_results TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE research_sessions ADD COLUMN depth TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE research_sessions ADD COLUMN effort_estimate TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE research_sessions ADD COLUMN target_authority_domains TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE research_sessions ADD COLUMN required_deliverables TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()


def save_result(result_id: str, result: dict):
    """Save a complete research result."""
    conn = _get_conn()
    now = datetime.now().isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO results 
        (id, mode, query, companies, data_points, instruction, data, sources, summary, status, raw_response, error, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        result_id,
        result.get("mode", ""),
        result.get("query", ""),
        json.dumps(result.get("companies", []), default=str),
        json.dumps(result.get("data_points", []), default=str),
        result.get("instruction", ""),
        json.dumps(result.get("data") or result.get("merged_data"), default=str),
        json.dumps(result.get("sources", []), default=str),
        result.get("summary", ""),
        result.get("status", "complete"),
        result.get("raw_response", "")[:5000],  # limit raw
        result.get("error"),
        result.get("timestamp", now),
        now
    ))
    conn.commit()


def save_partial(stream_id: str, company: str, company_data: dict):
    """Save partial result for a single company during streaming."""
    conn = _get_conn()
    now = datetime.now().isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO partial_results 
        (stream_id, company, data, sources, success, error, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        stream_id, company,
        json.dumps(company_data.get("data"), default=str),
        json.dumps(company_data.get("sources", []), default=str),
        1 if company_data.get("success") else 0,
        company_data.get("error"),
        now
    ))
    conn.commit()


def get_partials(stream_id: str) -> list[dict]:
    """Get all partial results for a stream."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM partial_results WHERE stream_id = ? ORDER BY created_at", 
        (stream_id,)
    ).fetchall()
    results = []
    for r in rows:
        results.append({
            "company": r["company"],
            "data": json.loads(r["data"]) if r["data"] else None,
            "sources": json.loads(r["sources"]) if r["sources"] else [],
            "success": bool(r["success"]),
            "error": r["error"],
        })
    return results


def get_result(result_id: str) -> dict | None:
    """Get a single result by ID."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM results WHERE id = ?", (result_id,)).fetchone()
    if not row:
        return None
    return _row_to_dict(row)


def get_all_results() -> list[dict]:
    """Get all saved results, newest first."""
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM results ORDER BY created_at DESC").fetchall()
    return [_row_to_dict(r) for r in rows]


def delete_result(result_id: str) -> bool:
    """Delete a result by ID."""
    conn = _get_conn()
    cur = conn.execute("DELETE FROM results WHERE id = ?", (result_id,))
    conn.commit()
    return cur.rowcount > 0


def cleanup_partials(stream_id: str):
    """Remove partial results after a stream completes successfully."""
    conn = _get_conn()
    conn.execute("DELETE FROM partial_results WHERE stream_id = ?", (stream_id,))
    conn.commit()


def _row_to_dict(row) -> dict:
    d = dict(row)
    for key in ["data", "sources", "companies", "data_points"]:
        if d.get(key):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    d["merged_data"] = d.get("data")
    d["timestamp"] = d.get("created_at", "")
    return d


def save_session(session_id: str, session: dict):
    """Save or update a research session."""
    conn = _get_conn()
    now = datetime.now().isoformat()
    conn.execute("""
        INSERT OR REPLACE INTO research_sessions
        (id, original_query, original_context, refined_prompt, clarification_answers, research_vectors, output_format, status, result_data, output_file_path, output_folder, sources_used, vector_results, quality_scores, depth, effort_estimate, target_authority_domains, required_deliverables, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        session.get("original_query", ""),
        session.get("original_context", ""),
        session.get("refined_prompt", ""),
        json.dumps(session.get("clarification_answers", []), default=str),
        json.dumps(session.get("research_vectors", []), default=str),
        session.get("output_format", ""),
        session.get("status", "planning"),
        json.dumps(session.get("result_data") or session.get("data"), default=str),
        session.get("output_file_path", ""),
        session.get("output_folder", ""),
        json.dumps(session.get("sources_used", []), default=str),
        json.dumps(session.get("vector_results", []), default=str),
        json.dumps(session.get("quality_scores", {}), default=str),
        session.get("depth", "standard"),
        json.dumps(session.get("effort_estimate", {}), default=str),
        json.dumps(session.get("target_authority_domains", []), default=str),
        json.dumps(session.get("required_deliverables", []), default=str),
        session.get("created_at", now),
        now
    ))
    conn.commit()


def update_session_status(session_id: str, status: str, **kwargs):
    """Update only status and other optional fields of a session."""
    conn = _get_conn()
    now = datetime.now().isoformat()
    
    # build update query dynamically
    fields = ["status = ?", "updated_at = ?"]
    params = [status, now]
    
    for k, v in kwargs.items():
        if k in ["original_query", "original_context", "refined_prompt", "output_format", "output_file_path", "output_folder", "depth"]:
            fields.append(f"{k} = ?")
            params.append(v)
        elif k in ["clarification_answers", "research_vectors", "result_data", "sources_used", "vector_results", "quality_scores", "effort_estimate", "target_authority_domains", "required_deliverables"]:
            fields.append(f"{k} = ?")
            params.append(json.dumps(v, default=str))
            
    params.append(session_id)
    query = f"UPDATE research_sessions SET {', '.join(fields)} WHERE id = ?"
    conn.execute(query, tuple(params))
    conn.commit()


def get_session(session_id: str) -> dict | None:
    """Get a single session by ID."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM research_sessions WHERE id = ?", (session_id,)).fetchone()
    if not row:
        return None
    return _session_row_to_dict(row)


def get_all_sessions() -> list[dict]:
    """Get all saved sessions, newest first."""
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM research_sessions ORDER BY created_at DESC").fetchall()
    return [_session_row_to_dict(r) for r in rows]


def delete_session(session_id: str) -> bool:
    """Delete a session by ID."""
    conn = _get_conn()
    cur = conn.execute("DELETE FROM research_sessions WHERE id = ?", (session_id,))
    conn.commit()
    return cur.rowcount > 0


def _session_row_to_dict(row) -> dict:
    d = dict(row)
    for key in ["clarification_answers", "research_vectors", "result_data", "sources_used", "vector_results", "quality_scores", "effort_estimate", "target_authority_domains", "required_deliverables"]:
        if d.get(key):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    d["timestamp"] = d.get("created_at", "")
    return d
