import re

def parse_markdown_with_clean_lists(md_text):
    lines = md_text.split('\n')
    output = []
    
    in_ul = False
    in_ol = False
    in_table = False
    table_rows = []
    in_code = False
    code_lines = []

    def process_inline(text):
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        return text

    def close_lists():
        nonlocal in_ul, in_ol
        res = ""
        if in_ul:
            res += "</ul>\n"
            in_ul = False
        if in_ol:
            res += "</ol>\n"
            in_ol = False
        return res

    def close_table():
        nonlocal in_table, table_rows
        if in_table and table_rows:
            html = '<div class="table-responsive"><table class="dash-table">'
            header = table_rows[0]
            html += '<thead><tr>' + ''.join(f'<th>{process_inline(c.strip())}</th>' for c in header) + '</tr></thead>'
            html += '<tbody>'
            for row in table_rows[1:]:
                html += '<tr>' + ''.join(f'<td>{process_inline(c.strip())}</td>' for c in row) + '</tr>'
            html += '</tbody></table></div>\n'
            table_rows = []
            in_table = False
            return html
        return ""

    for line in lines:
        stripped = line.strip()

        # Handle code fences
        if stripped.startswith("```"):
            if in_code:
                in_code = False
                output.append('<pre class="code-box"><code>' + '\n'.join(code_lines) + '</code></pre>\n')
                code_lines = []
            else:
                output.append(close_lists())
                output.append(close_table())
                in_code = True
            continue

        if in_code:
            code_lines.append(line.replace("<", "&lt;").replace(">", "&gt;"))
            continue

        # Handle tables
        if "|" in line and stripped.startswith("|") and stripped.endswith("|"):
            cells = [c for c in line.split("|")[1:-1]]
            if all(re.match(r'^[\s\-:]+$', c) for c in cells):
                continue
            output.append(close_lists())
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(cells)
            continue
        else:
            if in_table:
                output.append(close_table())

        # Empty lines
        if not stripped:
            output.append(close_lists())
            output.append('<div class="spacer-sm"></div>\n')
            continue

        # Headers
        if stripped.startswith("# "):
            output.append(close_lists())
            output.append(f'<h1 class="dash-h1">{process_inline(stripped[2:])}</h1>\n')
            continue
        elif stripped.startswith("## "):
            output.append(close_lists())
            output.append(f'<h2 class="dash-h2">{process_inline(stripped[3:])}</h2>\n')
            continue
        elif stripped.startswith("### "):
            output.append(close_lists())
            output.append(f'<h3 class="dash-h3">{process_inline(stripped[4:])}</h3>\n')
            continue

        # Horizontal rule
        if re.match(r'^-{3,}$', stripped) or re.match(r'^\*{3,}$', stripped):
            output.append(close_lists())
            output.append('<hr class="dash-hr"/>\n')
            continue

        # Callouts
        if stripped.startswith("> "):
            output.append(close_lists())
            output.append(f'<div class="dash-callout">{process_inline(stripped[2:])}</div>\n')
            continue

        # Unordered Lists
        if stripped.startswith("* ") or stripped.startswith("- "):
            is_sub = line.startswith("   ") or line.startswith("\t") or line.startswith("  ")
            if in_ol:
                output.append(close_lists())
            if not in_ul:
                output.append('<ul class="dash-ul">\n')
                in_ul = True
            item_content = process_inline(stripped[2:])
            cls = "sub-li" if is_sub else "main-li"
            output.append(f'  <li class="{cls}">{item_content}</li>\n')
            continue

        # Numbered Lists
        num_match = re.match(r'^(\d+)\.\s+(.*)$', stripped)
        if num_match:
            if in_ul:
                output.append(close_lists())
            if not in_ol:
                output.append('<ol class="dash-ol">\n')
                in_ol = True
            item_content = process_inline(num_match.group(2))
            output.append(f'  <li>{item_content}</li>\n')
            continue

        # Normal paragraph
        output.append(close_lists())
        output.append(f'<p class="dash-p">{process_inline(line)}</p>\n')

    output.append(close_lists())
    output.append(close_table())
    return "".join(output)

print("Parser defined successfully.")
