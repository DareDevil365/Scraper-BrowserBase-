import os
import sys
import json
import time
import requests

BASE_URL = "http://127.0.0.1:5000"

def run_ques_research():
    print("=== STARTING FULL RESEARCH FROM Ques.txt ===")
    
    # Check if server is running
    print("Checking if server is running on port 5000...")
    try:
        requests.get(f"{BASE_URL}/api/debug/ping", timeout=3)
        print("[+] Server is running!")
    except Exception:
        print("[!] Error: Flask server is not running. Please start the server first.")
        sys.exit(1)
        
    # Read Ques.txt
    ques_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Ques.txt")
    if not os.path.exists(ques_path):
        print(f"[!] Error: {ques_path} does not exist.")
        sys.exit(1)
        
    with open(ques_path, "r", encoding="utf-8") as f:
        query_text = f.read().strip()
        
    print(f"\nLoaded Query from Ques.txt ({len(query_text)} chars):")
    print("-" * 50)
    print(query_text[:300] + "\n...")
    print("-" * 50)
    
    # 1. Plan Research
    plan_payload = {
        "query": query_text,
        "context": "Escrow integration research for clothing marketplace in India.",
        "export_format": "html"
    }
    
    print("\n1. Submitting query to planner...")
    res = requests.post(f"{BASE_URL}/api/research/plan", json=plan_payload)
    if res.status_code != 200:
        print(f"Error planning: {res.text}")
        return
        
    plan_data = res.json()
    if not plan_data.get("success"):
        print(f"Planning failed: {plan_data.get('error')}")
        return
        
    session_id = plan_data["session_id"]
    questions = plan_data["questions"]
    print(f"-> Session ID: {session_id}")
    print(f"-> Generated {len(questions)} clarifying questions.")
    
    # 2. Answer Clarifying Questions
    answers = []
    for q in questions:
        question_id = q["id"]
        options = q.get("options", [])
        
        # Set default answer
        ans = "Not specified"
        
        # Detect depth question and choose the deepest available option
        if "depth" in question_id.lower() or "depth" in q.get("question", "").lower():
            # Look for Deep Research
            deep_options = [o for o in options if "deep" in o.lower()]
            if deep_options:
                ans = deep_options[0]
            elif options:
                ans = options[0]
        elif options:
            ans = options[0]
            
        print(f"   Question: {q['question']}")
        print(f"   Selected Answer: {ans}")
        answers.append({"question_id": question_id, "answer": ans})
        
    clarify_payload = {
        "session_id": session_id,
        "answers": answers,
        "user_note": "Ensure strict compliance with all items in prompt. Do not skip YouTube or Web research."
    }
    
    print("\n2. Submitting answers...")
    res = requests.post(f"{BASE_URL}/api/research/clarify", json=clarify_payload)
    if res.status_code != 200:
        print(f"Error clarifying: {res.text}")
        return
    print(f"-> Clarify Success: {res.json().get('success')}")
    
    # 3. Refine Research (Generate blueprint vectors)
    print("\n3. Refining research and generating blueprint...")
    refine_payload = {
        "session_id": session_id,
        "answers": answers
    }
    res = requests.post(f"{BASE_URL}/api/research/refine", json=refine_payload)
    if res.status_code != 200:
        print(f"Error refining: {res.text}")
        return
        
    refine_data = res.json()
    if not refine_data.get("success"):
        print(f"Refinement failed: {refine_data.get('error')}")
        return
        
    vectors = refine_data.get("vectors", [])
    print(f"-> Generated {len(vectors)} research vectors:")
    for v in vectors:
        print(f"   - Topic: '{v.get('topic')}'")
        
    # Wait a bit for global source discovery to complete
    print("\nWaiting 5 seconds for background source discovery to populate...")
    time.sleep(5)
    
    # 4. Stream and Run Research
    print(f"\n4. Streaming research execution for session {session_id}...")
    stream_url = f"{BASE_URL}/api/research/stream/{session_id}"
    
    start_time = time.time()
    try:
        response = requests.get(stream_url, stream=True, timeout=1800)
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data: "):
                    data_str = decoded[6:]
                    try:
                        payload = json.loads(data_str)
                        event = payload.get("event")
                        msg = payload.get("message", "")
                        
                        if event == "progress":
                            if len(msg) > 120 and "synthesiz" in msg.lower():
                                msg = msg[:120] + "..."
                            print(f"[PROGRESS] {msg}")
                        elif event == "status":
                            print(f"[STATUS] {msg}")
                        elif event == "vector_done":
                            vec = payload.get("vector", {})
                            result = payload.get("result", {})
                            success = result.get("success", False)
                            scraped_count = len(result.get("sources", []))
                            print(f"\n>>> VECTOR COMPLETED: '{vec.get('topic')}' -> Success={success} ({scraped_count} sources)")
                        elif event == "done":
                            print("\n=== RESEARCH FINISHED SUCCESSFULLY ===")
                            print(f"Report Title: {payload.get('synthesis', {}).get('title')}")
                            print(f"Output folder: {payload.get('output_folder')}")
                            break
                        elif event == "error":
                            print(f"\n[ERROR] {payload.get('error')}")
                            break
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        print(f"Connection error or timeout during stream: {e}")
        
    print(f"\nTotal elapsed time: {time.time() - start_time:.1f}s")

if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    run_ques_research()
