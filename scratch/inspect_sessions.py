import sqlite3
import json

db_path = r"c:\Users\yasha\Desktop\scout\scout_results.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT id, original_query, sources_used, vector_results FROM research_sessions;")
rows = cursor.fetchall()
print(f"Found {len(rows)} sessions.")

for row in rows:
    session_id, q, sources_used, vector_results = row
    print(f"\nSession: {session_id} - Query: {q[:50]}")
    
    if sources_used:
        try:
            su = json.loads(sources_used)
            print(f"  sources_used count: {len(su)}")
            for idx, item in enumerate(su[:5]):
                print(f"    {idx+1}: {item}")
        except Exception as e:
            print("  Error loading sources_used:", e)
            
    if vector_results:
        try:
            vr = json.loads(vector_results)
            print(f"  vector_results count: {len(vr)}")
            # Show a snippet of one result
            if vr:
                first_k = list(vr.keys())[0] if isinstance(vr, dict) else 0
                val = vr[first_k] if isinstance(vr, dict) else vr[0]
                print(f"    First result keys/keys: {list(val.keys()) if isinstance(val, dict) else 'non-dict'}")
                if isinstance(val, dict) and 'sources' in val:
                    print(f"    First result sources (up to 3): {val['sources'][:3]}")
        except Exception as e:
            print("  Error loading vector_results:", e)

conn.close()
