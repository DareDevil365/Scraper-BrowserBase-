"""Analyze source counts in recent outputs."""
import json, os

out_dir = r"c:\Users\yasha\Desktop\scout\outputs"
for folder in sorted(os.listdir(out_dir)):
    path = os.path.join(out_dir, folder)
    if not os.path.isdir(path):
        continue
    
    print(f"\n=== {folder[:60]}... ===")
    
    # scrape_queue
    sq = os.path.join(path, "scrape_queue.json")
    if os.path.exists(sq):
        data = json.load(open(sq, "r", encoding="utf-8"))
        vids = set(s.get("vector_id", "?") for s in data)
        print(f"  scrape_queue.json: {len(data)} sources across {len(vids)} vectors")
        for vid in sorted(vids):
            count = sum(1 for s in data if s.get("vector_id") == vid)
            print(f"    {vid}: {count} sources")
    
    # sources.json
    sj = os.path.join(path, "sources.json")
    if os.path.exists(sj):
        sources = json.load(open(sj, "r", encoding="utf-8"))
        print(f"  sources.json: {len(sources)} total sources used")
    
    # state.json
    st = os.path.join(path, "state.json")
    if os.path.exists(st):
        state = json.load(open(st, "r", encoding="utf-8"))
        print(f"  state: total_vectors={state.get('total_vectors')}, completed={state.get('completed_vectors')}, status={state.get('status')}")
    
    # run_log
    rl = os.path.join(path, "run_log.jsonl")
    if os.path.exists(rl):
        lines = open(rl, "r", encoding="utf-8").readlines()
        for line in lines:
            try:
                entry = json.loads(line)
                print(f"  run_log: {entry}")
            except:
                pass
    
    # sources_log.csv line count
    sl = os.path.join(path, "sources_log.csv")
    if os.path.exists(sl):
        line_count = sum(1 for _ in open(sl, "r", encoding="utf-8")) - 1  # minus header
        print(f"  sources_log.csv: {line_count} entries")
