"""
update_all_furniture_content.py
1. Cleans all emojis from all markdown files in Furniture/ (and its subfolders).
2. Converts blockquoted/malformed headings like '> ### 🎯 Target Wealth Classification'
   into standard, proper markdown headings: '## Target Wealth Classification'.
3. Replaces emojis across all headings, lists, tables, and text with clean typography.
"""

import os
import re

FURNITURE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Furniture"))

# Common emojis to strip
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "\U00002B50"
    "\U00002B55"
    "\U000023CF"
    "\U000023E9-\U000023F3"
    "\U000025AA-\U000025FE"
    "\U00002B05-\U00002B07"
    "\U00002934-\U00002935"
    "\U00002190-\U000021FF"
    "\U0000200D"
    "\U0000FE0F"
    "]+",
    flags=re.UNICODE
)

def clean_markdown_content(text):
    # 1. Remove blockquote before headings: '> ### Target' or '> ## Target' -> '## Target'
    text = re.sub(r'^>\s*#{1,4}\s*', '## ', text, flags=re.MULTILINE)
    
    # 2. Convert any remaining '> **Category:' lines to list items without blockquote
    text = re.sub(r'^>\s*(\*\*)', r'* \1', text, flags=re.MULTILINE)
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

    # 3. Strip all emojis
    text = EMOJI_PATTERN.sub('', text)

    # 4. Clean specific symbols like ★ or ⬍
    text = text.replace('★', '')
    text = text.replace('⬍', '')
    text = text.replace('📍', '')

    # 5. Clean extra whitespace around headings
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        if line.strip().startswith('##'):
            # ensure proper spacing after ##
            line = re.sub(r'^(#{1,6})\s*', r'\1 ', line)
        cleaned_lines.append(line.rstrip())

    # Collapse multiple consecutive blank lines into max 2
    cleaned_text = '\n'.join(cleaned_lines)
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    return cleaned_text

# Walk and update all .md and .csv files in Furniture
updated_files = 0
for root, dirs, files in os.walk(FURNITURE_DIR):
    for f in files:
        if f.endswith('.md') or f.endswith('.txt'):
            fpath = os.path.join(root, f)
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            cleaned = clean_markdown_content(content)
            with open(fpath, 'w', encoding='utf-8') as file:
                file.write(cleaned)
            updated_files += 1

print(f"Successfully cleaned and standardized headings across {updated_files} markdown files in {FURNITURE_DIR}")
