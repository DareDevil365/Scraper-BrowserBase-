from google import genai
import os

def _load_api_keys():
    keys = []
    keys_file = os.path.join(os.path.dirname(__file__), "api_keys.txt")
    if os.path.exists(keys_file):
        with open(keys_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    keys.extend([k.strip() for k in line.split(",") if k.strip()])
    env_keys = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY") or ""
    if env_keys:
        keys.extend([k.strip() for k in env_keys.split(",") if k.strip()])
    seen = set()
    return [k for k in keys if not (k in seen or seen.add(k))]

keys = _load_api_keys()
if not keys:
    raise RuntimeError("Set GEMINI_API_KEYS in environment or add keys to api_keys.txt.")
client = genai.Client(api_key=keys[0])
for m in client.models.list():
    name = m.name
    if "gemini" in name.lower():
        print(name)
