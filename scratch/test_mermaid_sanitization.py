import re

def sanitize_line(line: str) -> str:
    bracket_pairs = [
        ("([", "])"),
        ("[[", "]]"),
        ("[(", ")]"),
        ("((", "))"),
        ("{{", "}}"),
        ("[", "]"),
        ("(", ")"),
        ("{", "}"),
        (">", "]")
    ]
    
    pos = 0
    result = []
    
    while pos < len(line):
        best_match = None
        best_match_start = -1
        best_open = None
        best_close = None
        
        for open_br, close_br in bracket_pairs:
            pattern = r'\b([a-zA-Z0-9_-]+)\s*' + re.escape(open_br)
            match = re.search(pattern, line[pos:])
            if match:
                start_idx = pos + match.start()
                if best_match is None or start_idx < best_match_start:
                    best_match = match
                    best_match_start = start_idx
                    best_open = open_br
                    best_close = close_br
                    
        if best_match is None:
            result.append(line[pos:])
            break
            
        node_id = best_match.group(1)
        open_br_pos = best_match_start + best_match.group(0).find(best_open)
        
        # Check if open_br_pos is inside quotes
        prefix = line[:open_br_pos]
        if prefix.count('"') % 2 == 1:
            # Inside quotes! Skip past the opening bracket to avoid infinite loop
            result.append(line[pos:open_br_pos + len(best_open)])
            pos = open_br_pos + len(best_open)
            continue
            
        label_start = open_br_pos + len(best_open)
        close_pos = line.find(best_close, label_start)
        if close_pos == -1:
            result.append(line[pos:label_start])
            pos = label_start
            continue
            
        label = line[label_start:close_pos]
        label_stripped = label.strip()
        if label_stripped.startswith('"') and label_stripped.endswith('"'):
            label_content = label_stripped[1:-1]
        elif label_stripped.startswith("'") and label_stripped.endswith("'"):
            label_content = label_stripped[1:-1]
        else:
            label_content = label_stripped
            
        clean_label = label_content.replace('"', "'").strip()
        
        result.append(line[pos:best_match_start])
        result.append(f'{node_id}{best_open}"{clean_label}"{best_close}')
        
        pos = close_pos + len(best_close)
        
    return "".join(result)

def sanitize_mermaid(code: str) -> str:
    if not isinstance(code, str):
        return code
        
    code_stripped = code.strip()
    if code_stripped.startswith("gantt"):
        return code.replace(" & ", " and ").replace("&", "and")
        
    if not (code_stripped.startswith("graph ") or code_stripped.startswith("flowchart ")):
        return code

    lines = code.splitlines()
    sanitized_lines = [sanitize_line(line) for line in lines]
    return "\n".join(sanitized_lines)

# Test it on a block
test_block = """graph TD
    A[Existing Basic Python Syntax Knowledge] --> B{Beginner Level: 0-3 Months}
    B --> C[Python Fundamentals & Basic Programming]
    C --> D[Basic Mathematics: Linear Algebra, Probability, Statistics]
    D --> E[Data Handling Fundamentals]
    E --> F[Key Libraries: Pandas for EDA]
    F --> G[Key Libraries: Matplotlib for Visualization]
    G --> H[Numerical Libraries: JAX for Vectorization]
    H --> I[Numerical Libraries: Numpyro for Regression & Classification]
    I --> J[Introduction to AI & Machine Learning Concepts]
    J --> K[Advanced AI/ML Concepts & Projects (e.g., Deep Neural Networks, Transformers)]
"""

print(sanitize_mermaid(test_block))
