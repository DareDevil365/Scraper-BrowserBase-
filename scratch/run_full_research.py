import json
import requests
import time

BASE_URL = "http://localhost:5000"

def test_full_flow():
    print("=== STARTING FULL END-TO-END RESEARCH FLOW TEST ===")
    
    # 1. Plan Research
    plan_payload = {
        "query": "I need pricing data for Delhivery, Xpressbees, Leopards Courier, and FedEx India.",
        "context": "Focus on standard domestic courier rates in North India.",
        "export_format": "xlsx"
    }
    print(f"\n1. Submitting query: {plan_payload['query']}...")
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
    print(f"-> Generated {len(questions)} clarifying questions:")
    for q in questions:
        print(f"   [{q['id']}] {q['question']} (Options: {q.get('options')})")
        
    # 2. Answer Clarifying Questions
    answers = []
    for q in questions:
        # Provide sensible default answers
        if "depth" in q["id"] or q["id"] == "research_depth":
            ans = "Surface Level"
        elif q.get("options"):
            ans = q["options"][0]
        else:
            ans = "Not specified"
        answers.append({"question_id": q["id"], "answer": ans})
        
    clarify_payload = {
        "session_id": session_id,
        "answers": answers,
        "note": "Include COD charges and weight slabs of 1-5kg."
    }
    print(f"\n2. Submitting answers: {answers}...")
    res = requests.post(f"{BASE_URL}/api/research/clarify", json=clarify_payload)
    if res.status_code != 200:
        print(f"Error clarifying: {res.text}")
        return
        
    clarify_data = res.json()
    print(f"-> Clarify Success: {clarify_data.get('success')}")
    
    # 3. Refine Research (Generate vectors)
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
    print(f"-> Generated master prompt of length {len(refine_data.get('refined_prompt', ''))}")
    print(f"-> Generated {len(vectors)} parallel research vectors:")
    for v in vectors:
        print(f"   - Topic: '{v['topic']}'")
        print(f"     Data Points: {v.get('data_points')}")
        
    # 4. Stream and Run Research
    print(f"\n4. Starting streaming research for session {session_id}...")
    stream_url = f"{BASE_URL}/api/research/stream/{session_id}"
    
    try:
        # SSE stream read
        response = requests.get(stream_url, stream=True, timeout=300)
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
                            # Print progress updates
                            print(f"[SSE PROGRESS] {msg}")
                        elif event == "vector_status":
                            print(f"[SSE VECTOR STATUS] Vector {payload.get('vector_id')} -> {payload.get('status')} ({msg})")
                        elif event == "done":
                            print("\n=== SSE STREAM FINISHED SUCCESS ===")
                            print(f"Synthesis details: {payload.get('synthesis', {}).get('title')}")
                            print(f"Output files folder: {payload.get('output_folder')}")
                            break
                        elif event == "error":
                            print(f"\n[SSE ERROR] {payload.get('error')}")
                            break
                    except json.JSONDecodeError:
                        print(f"[SSE RAW DATA] {data_str}")
    except Exception as e:
        print(f"Connection error or timeout during stream: {e}")

if __name__ == "__main__":
    test_full_flow()
