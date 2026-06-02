import os
from pathlib import Path

skills_dir = Path("Skills")
replacements = {
    "â€”": "—",
    "â†’": "→",
    "Â§": "§",
    "Ã—": "×",
    "Â·": "·",
    "â€¢": "•",
    "âœ”": "✔",
    "âš ": "⚠️",
    "â€¦": "…",
    "â€“": "–",
    "ï¸ ": "",  # Clean up the emoji variation selector mojibake
    "â‰¥": "≥",
    "â‡’": "⇒",
    "â‰ˆ": "≈",
}

for filepath in skills_dir.glob("*.md"):
    text = filepath.read_text(encoding="utf-8", errors="replace")
    orig_text = text
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    # Fix the typo in API_Limit_Tuning.md specifically:
    # "No new wall-clock pacing / T_total snuck in.S" -> "No new wall-clock pacing / T_total snuck in."
    if "pacing / T_total snuck in.S" in text:
        text = text.replace("pacing / T_total snuck in.S", "pacing / T_total snuck in.")
    
    if text != orig_text:
        filepath.write_text(text, encoding="utf-8")
        print(f"Fixed encoding and/or typos in {filepath}")
    else:
        print(f"No changes needed in {filepath}")
