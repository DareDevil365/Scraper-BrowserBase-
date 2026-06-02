from google import genai
import os
import sys

def load_keys():
    keys = []
    keys_file = "api_keys.txt"
    if os.path.exists(keys_file):
        with open(keys_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    keys.extend([k.strip() for k in line.split(",") if k.strip()])
    return keys

keys = load_keys()
print(f"Loaded {len(keys)} keys from api_keys.txt")

for idx, key in enumerate(keys, 1):
    print(f"\n--- Testing Key #{idx}: {key[:10]}...{key[-5:]} ---")
    try:
        client = genai.Client(api_key=key)
        # Try a simple quick model call
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="say Hello"
        )
        print(f"Success! Response: {response.text.strip()}")
    except Exception as e:
        print(f"Failed: {e}")
