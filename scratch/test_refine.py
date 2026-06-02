import requests, json, time

# Refine with answers
start = time.time()
r = requests.post('http://localhost:5000/api/research/refine', json={
    'session_id': '98a8212b',
    'answers': [
        {'question_id': 'q_1', 'answer': 'Small Business (1-50 users)'},
        {'question_id': 'q_2', 'answer': 'None/Mixed'},
        {'question_id': 'research_depth', 'answer': 'Surface Level'}
    ],
    'output_format': 'docx'
})
elapsed = time.time() - start
print(f"Refine took {elapsed:.1f}s")
data = r.json()
print(f"Success: {data.get('success')}")
vectors = data.get('vectors', [])
print(f"Vectors: {len(vectors)}")
for v in vectors:
    print(f"  - {v.get('id')}: {v.get('topic')}")
