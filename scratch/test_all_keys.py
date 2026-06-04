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

models_to_test = ["gemini-2.0-flash", "gemini-2.5-flash-lite"]

for idx, key in enumerate(keys, 1):
    print(f"\n--- Testing Key #{idx}: {key[:10]}...{key[-5:]} ---")
    for model in models_to_test:
        try:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model=model,
                contents="say Hello"
            )
            print(f"[{model}] Success! Response: {response.text.strip()}")
            break # If one model succeeds, go to next key
        except Exception as e:
            print(f"[{model}] Failed: {e}")

