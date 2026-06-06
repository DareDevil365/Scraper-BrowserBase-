import requests

session_id = "15e739fa"
url = f"http://127.0.0.1:5000/api/research/export/{session_id}?format=html"

print(f"Requesting HTML report for session {session_id}...")
r = requests.get(url)
print("Response status code:", r.status_code)
print("Content-type:", r.headers.get("Content-Type"))

if r.status_code == 200:
    content = r.text
    print("Downloaded successfully! Size:", len(content), "bytes")
    # Verify it has standard HTML structure and contains mermaid
    if "<!DOCTYPE html>" in content:
        print("PASS: Contains DOCTYPE declaration.")
    else:
        print("FAIL: Missing DOCTYPE declaration.")
        
    if "class=\"mermaid\"" in content or "mermaid.js" in content or "<div class=\"mermaid\">" in content:
        print("PASS: Contains mermaid rendering div/JS.")
    else:
        print("FAIL: No mermaid rendering classes found.")
        
    # Let's inspect a snippet of a mermaid block to see if it is sanitized (no unquoted labels with colons)
    import re
    mermaid_blocks = re.findall(r'<div class="mermaid">(.*?)</div>', content, re.DOTALL)
    print(f"Found {len(mermaid_blocks)} mermaid blocks in HTML.")
    for idx, block in enumerate(mermaid_blocks[:2]):
        print(f"\n--- Mermaid Block {idx+1} (first 300 chars) ---")
        print(block.strip()[:300])
        # Check for unquoted label syntax error, e.g. B{Beginner Level: 0-3 Months}
        # It should be B{"Beginner Level: 0-3 Months"} or similar
        unquoted_match = re.search(r'\b[a-zA-Z0-9_-]+\s*\{[^{}"]*:[^{}"]*\}', block)
        if unquoted_match:
            print("FAIL: Found unquoted label with colon inside braces:", unquoted_match.group(0))
        else:
            print("PASS: No unquoted labels with colons found inside braces.")
else:
    print("FAIL: Could not download HTML report!")
