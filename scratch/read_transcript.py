import json
import re

path = r"C:\Users\yasha\.gemini\antigravity-ide\brain\2ace2bcd-aa5d-4a21-a243-eab281269ef1\.system_generated\logs\transcript.jsonl"

print("Reading transcript...")
with open(path, "r", encoding="utf-8") as f:
    for line_idx, line in enumerate(f):
        try:
            data = json.loads(line)
            # Look for gemini_key or api_key or any key pattern
            content = str(data.get("content", ""))
            tool_calls = str(data.get("tool_calls", ""))
            
            # Check for AIzaSy or AQ. patterns
            keys = re.findall(r'(AIzaSy[a-zA-Z0-9_-]+|AQ\.[a-zA-Z0-9_-]+)', content + " " + tool_calls)
            if keys:
                print(f"Line {line_idx} type={data.get('type')} status={data.get('status')} keys={keys}")
                
            # Print if user input mentions keys
            if data.get("type") == "USER_INPUT":
                print(f"Line {line_idx} [USER_INPUT]: {content[:200]}")
        except Exception as e:
            print(f"Error parsing line {line_idx}: {e}")
