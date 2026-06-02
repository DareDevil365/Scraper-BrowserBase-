"""
Full pipeline test for RunawayScout.
Tests: Plan -> Refine -> Stream (SSE) with timing instrumentation.
"""
import requests
import json
import time
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://127.0.0.1:5000"

def timed_post(url, payload):
    start = time.time()
    r = requests.post(url, json=payload, timeout=120)
    elapsed = time.time() - start
    return r, elapsed

def timed_get_sse(url, timeout=600):
    """Stream SSE events and collect them with timestamps."""
    start = time.time()
    events = []
    try:
        with requests.get(url, stream=True, timeout=timeout) as r:
            buffer = ""
            current_event = None
            for line in r.iter_lines(decode_unicode=True):
                if line is None:
                    continue
                if line.startswith("event: "):
                    current_event = line[7:]
                elif line.startswith("data: "):
                    data_str = line[6:]
                    elapsed = time.time() - start
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        data = {"raw": data_str}
                    events.append({
                        "event": current_event,
                        "elapsed": round(elapsed, 1),
                        "data": data
                    })
                    
                    # Print progress
                    msg = data.get("message", "")
                    step = data.get("step", "")
                    total = data.get("total", "")
                    
                    if current_event == "progress":
                        # Truncate long synthesis chunk messages
                        if msg.startswith("Synthesizing v1:") or msg.startswith("Synthesizing v2:"):
                            msg = msg[:80] + "..."
                        print(f"  [{elapsed:6.1f}s] [{step}/{total}] {msg}")
                    elif current_event == "status":
                        print(f"  [{elapsed:6.1f}s] STATUS: {msg}")
                    elif current_event == "vector_done":
                        vec = data.get("vector", {})
                        result = data.get("result", {})
                        success = result.get("success", False)
                        sources = len(result.get("sources", []))
                        resumed = data.get("resumed", False)
                        tag = "RESUMED" if resumed else ("OK" if success else "FAIL")
                        print(f"  [{elapsed:6.1f}s] VECTOR_DONE: {vec.get('topic','')} [{tag}] ({sources} sources)")
                    elif current_event == "done":
                        status = data.get("status", "")
                        print(f"  [{elapsed:6.1f}s] DONE! Status={status}")
                        break
    except Exception as e:
        print(f"  SSE error: {e}")
    total_time = time.time() - start
    return events, total_time

# Wait for server to start
print("Waiting for server to start...")
for _ in range(30):
    try:
        requests.get(f"{BASE}/api/debug/ping", timeout=1)
        print("Server is up!")
        break
    except Exception:
        time.sleep(1)
else:
    print("Server failed to start after 30 seconds.")
    sys.exit(1)

# ===================== STEP 1: Plan =====================
print("=" * 60)
print("STEP 1: Planning")
print("=" * 60)
r, t = timed_post(f"{BASE}/api/research/plan", {
    "query": "Compare pricing and features of top 3 cloud storage providers: Google Drive, Dropbox, OneDrive",
    "context": "Focus on business plans, storage limits, and collaboration features"
})
plan = r.json()
print(f"  Plan took: {t:.1f}s")
print(f"  Success: {plan.get('success')}")
session_id = plan.get("session_id")
print(f"  Session: {session_id}")
questions = plan.get("questions", [])
print(f"  Questions: {len(questions)}")

if not plan.get("success"):
    print(f"  ERROR: {plan.get('error')}")
    sys.exit(1)

# ===================== STEP 2: Refine =====================
print()
print("=" * 60)
print("STEP 2: Refining")
print("=" * 60)

# Auto-answer: pick defaults
answers = []
for q in questions:
    answers.append({
        "question_id": q.get("id"),
        "answer": q.get("default", q.get("options", [""])[0])
    })
# Override depth to Surface for speed test
for a in answers:
    if a["question_id"] == "research_depth":
        a["answer"] = "Surface Level"

print(f"  Answers: {json.dumps(answers, indent=2)}")

r, t = timed_post(f"{BASE}/api/research/refine", {
    "session_id": session_id,
    "answers": answers,
    "output_format": "docx"
})
refine = r.json()
print(f"  Refine took: {t:.1f}s")
print(f"  Success: {refine.get('success')}")
vectors = refine.get("vectors", [])
print(f"  Vectors: {len(vectors)}")
for v in vectors:
    print(f"    - [{v.get('priority','?')}] {v.get('id')}: {v.get('topic')}")

if not refine.get("success"):
    print(f"  ERROR: {refine.get('error')}")
    sys.exit(1)

# ===================== STEP 3: Research Stream =====================
print()
print("=" * 60)
print("STEP 3: Research Stream (SSE)")
print("=" * 60)

# Wait a bit for background source discovery to complete
print("  Waiting 5s for background source discovery...")
time.sleep(5)

events, total = timed_get_sse(f"{BASE}/api/research/stream/{session_id}", timeout=600)

print()
print("=" * 60)
print("RESULTS SUMMARY")
print("=" * 60)
print(f"  Total stream time: {total:.1f}s")
print(f"  Total SSE events: {len(events)}")

# Breakdown by event type
event_types = {}
for e in events:
    et = e["event"]
    event_types[et] = event_types.get(et, 0) + 1
print(f"  Event breakdown: {event_types}")

# Check final result
done_events = [e for e in events if e["event"] == "done"]
if done_events:
    done = done_events[0]["data"]
    status = done.get("status", "unknown")
    sources = len(done.get("sources", []))
    synth = done.get("synthesis", {})
    title = synth.get("title", "N/A") if isinstance(synth, dict) else "N/A"
    sections = len(synth.get("sections", [])) if isinstance(synth, dict) else 0
    output_file = done.get("output_file_path", "N/A")
    print(f"  Status: {status}")
    print(f"  Report title: {title}")
    print(f"  Sections: {sections}")
    print(f"  Total sources: {sources}")
    print(f"  Output file: {output_file}")
else:
    print("  WARNING: No 'done' event received!")

# Time breakdown between vectors
vector_events = [e for e in events if e["event"] == "vector_done"]
if vector_events:
    print()
    print("  Per-vector timing:")
    prev_time = 0
    for ve in vector_events:
        vec_name = ve["data"].get("vector", {}).get("topic", "?")
        delta = ve["elapsed"] - prev_time
        success = ve["data"].get("result", {}).get("success", False)
        sources = len(ve["data"].get("result", {}).get("sources", []))
        print(f"    {vec_name}: {delta:.1f}s ({'OK' if success else 'FAIL'}, {sources} sources)")
        prev_time = ve["elapsed"]
