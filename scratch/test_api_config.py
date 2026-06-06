import requests
import os

url = "http://127.0.0.1:5000/api/config"
keys_file = "api_keys.txt"

# Read current keys
if os.path.exists(keys_file):
    with open(keys_file, "r", encoding="utf-8") as f:
        original_content = f.read()
else:
    original_content = ""

try:
    # Test 1: Only this time (persist=False)
    test_key_temp = "AIzaSyTestTempKeyOnlyThisTime12345"
    payload = {
        "gemini_key": test_key_temp,
        "persist": False
    }
    r = requests.post(url, json=payload)
    print("Test 1 (persist=False) response:", r.json())
    
    # Verify not in file
    with open(keys_file, "r", encoding="utf-8") as f:
        content = f.read()
    if test_key_temp in content:
        print("FAIL: Temp key was written to api_keys.txt!")
    else:
        print("PASS: Temp key was NOT written to api_keys.txt.")

    # Test 2: Add to database (persist=True)
    test_key_persist = "AIzaSyTestPersistKeyAddtoDatabase98765"
    payload = {
        "gemini_key": test_key_persist,
        "persist": True
    }
    r = requests.post(url, json=payload)
    print("Test 2 (persist=True) response:", r.json())
    
    # Verify in file
    with open(keys_file, "r", encoding="utf-8") as f:
        content = f.read()
    if test_key_persist in content:
        print("PASS: Persisted key was written to api_keys.txt.")
    else:
        print("FAIL: Persisted key was NOT written to api_keys.txt!")

finally:
    # Restore original content of api_keys.txt
    with open(keys_file, "w", encoding="utf-8") as f:
        f.write(original_content)
    print("Restored original api_keys.txt.")
