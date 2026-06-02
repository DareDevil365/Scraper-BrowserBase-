import os

skills_dir = "Skills"
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
}

for filename in os.listdir(skills_dir):
    if filename.endswith(".md"):
        path = os.path.join(skills_dir, filename)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        orig_content = content
        for k, v in replacements.items():
            content = content.replace(k, v)
            
        if content != orig_content:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Fixed encoding in {path}")
        else:
            print(f"No changes needed in {path}")
