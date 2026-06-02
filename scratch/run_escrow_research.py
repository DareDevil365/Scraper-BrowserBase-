"""
Run escrow research session using the local stealth scraper
"""
import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:5000"

def run_escrow():
    print("=== STARTING ESCROW RESEARCH WITH STEALTH SCRAPER ===")
    
    # Wait for server to start
    print("Checking if server is running...")
    try:
        requests.get(f"{BASE_URL}/api/debug/ping", timeout=3)
    except Exception:
        print("[!] Error: Flask server is not running. Please start the server first.")
        sys.exit(1)
        
    # 1. Plan Research
    query_text = (
        "-->what exactly is an escrow account\n"
        "-->Difference in 3PL and Payment gateways, who provides what? how much we need to rely on 3PL companies and how much on Payment gateways?\n"
        "-->3 types of transactions \n"
        "\t1)product\n"
        "\t2)service\n"
        "\t3)outside escrow(COD case-what happens, how companies handle it? Cap on max order amount for COD etc.)\n\n"
        "-->Map out the different milestones for the above 3 types of transactions which act as triggers in the escrow mechanism\n"
        "-->Analyse competitors in product, service and see how their escrow mechanism is designed\n"
        "--> requirements for setting up escrow\n"
        "\tGateway api, 3PL webhook, requirements from silaai platform"
    )
    
    plan_payload = {
        "query": query_text,
        "context": "Focus on milestones and operational flows.",
        "export_format": "pdf"
    }
    
    print("\n1. Submitting Escrow query...")
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
        # We explicitly set standard depth to run full research
        if "depth" in q["id"] or q["id"] == "research_depth":
            ans = "Standard Depth"
        elif q.get("options"):
            ans = q["options"][0]
        else:
            ans = "Not specified"
        answers.append({"question_id": q["id"], "answer": ans})
        
    clarify_payload = {
        "session_id": session_id,
        "answers": answers,
        "note": "Focus on standard courier systems and e-commerce milestones."
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
        "session_id": session_id
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
    print(f"-> Generated {len(vectors)} parallel research vectors.")
    
    # Wait a bit for global source discovery to complete
    print("\nWaiting 6 seconds for background source discovery to settle...")
    time.sleep(6)
    
    # 4. Stream and Run Research
    print(f"\n4. Starting streaming research for session {session_id}...")
    stream_url = f"{BASE_URL}/api/research/stream/{session_id}"
    
    start_time = time.time()
    try:
        response = requests.get(stream_url, stream=True, timeout=1200)
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
                            # Truncate long synthesis chunks
                            if msg.startswith("Synthesizing v1:") or msg.startswith("Synthesizing v2:"):
                                msg = msg[:80] + "..."
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
                            print(f"Synthesis details: {payload.get('synthesis', {}).get('title')}")
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
    run_escrow()
