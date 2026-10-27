import os
import re

furniture_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Furniture"))

count = 0
for root, dirs, files in os.walk(furniture_dir):
    for f in files:
        if f.endswith(".md"):
            filepath = os.path.join(root, f)
            with open(filepath, "r", encoding="utf-8") as file:
                lines = file.readlines()
            
            new_lines = []
            modified = False
            for line in lines:
                # Check if line contains search.mp or jindalstainless.com
                if "search.mp" in line or "jindalstainless.com" in line:
                    modified = True
                    count += 1
                    continue
                # Also clean any Justdial links with broken /nct- slugs
                if "justdial.com" in line and "/nct-" in line:
                    line = re.sub(r"/nct-\d+", "", line)
                    modified = True
                new_lines.append(line)
            
            if modified:
                with open(filepath, "w", encoding="utf-8") as file:
                    file.writelines(new_lines)
                print(f"Cleaned: {filepath}")

print(f"Total lines removed/cleaned: {count}")
