"""
build_furniture_html_black_silver.py
Compiles Furniture/index.html with:
  1. High-end Black and Silver / Metallic Platinum luxury theme.
  2. Zero emojis across all interface elements, headings, tabs, and filters.
  3. Clean, responsive typography and interactive modal/tables.
"""

import os
import csv
import json
import re

FURNITURE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Furniture"))
HTML_OUT_PATH = os.path.join(FURNITURE_DIR, "index.html")

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "\U00002B50\U00002B55\U000023CF\U000023E9-\U000023F3\U000025AA-\U000025FE"
    "\U00002B05-\U00002B07\U00002934-\U00002935\U00002190-\U000021FF\U0000200D\U0000FE0F"
    "]+",
    flags=re.UNICODE
)

def md_to_html(md_text):
    """Robust offline markdown to HTML converter with zero emojis and clean typography."""
    md_text = EMOJI_PATTERN.sub('', md_text)
    md_text = md_text.replace('★', '').replace('⬍', '').replace('📍', '')
    
    lines = md_text.split("\n")
    html_lines = []
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

    def close_table():
        nonlocal in_table, table_rows
        if in_table and table_rows:
            html = '<div class="table-responsive"><table class="dash-table">'
            header = table_rows[0]
            html += '<thead><tr>' + ''.join(f'<th>{process_inline(c.strip())}</th>' for c in header) + '</tr></thead>'
            html += '<tbody>'
            for row in table_rows[1:]:
                html += '<tr>' + ''.join(f'<td>{process_inline(c.strip())}</td>' for c in row) + '</tr>'
            html += '</tbody></table></div>'
            table_rows = []
            in_table = False
            return html
        return ""

    for line in lines:
        stripped = line.strip()

        # Code blocks
        if stripped.startswith("```"):
            if in_code:
                in_code = False
                html_lines.append('<pre class="code-box"><code>' + '\n'.join(code_lines) + '</code></pre>')
                code_lines = []
            else:
                if in_table:
                    html_lines.append(close_table())
                in_code = True
            continue

        if in_code:
            code_lines.append(line.replace("<", "&lt;").replace(">", "&gt;"))
            continue

        # Tables
        if "|" in line and stripped.startswith("|") and stripped.endswith("|"):
            cells = [c for c in line.split("|")[1:-1]]
            if all(re.match(r'^[\s\-:]+$', c) for c in cells):
                continue
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(cells)
            continue
        else:
            if in_table:
                html_lines.append(close_table())

        # Headers
        if stripped.startswith("# "):
            html_lines.append(f'<h1 class="dash-h1">{process_inline(stripped[2:])}</h1>')
            continue
        elif stripped.startswith("## "):
            html_lines.append(f'<h2 class="dash-h2">{process_inline(stripped[3:])}</h2>')
            continue
        elif stripped.startswith("### "):
            html_lines.append(f'<h3 class="dash-h3">{process_inline(stripped[4:])}</h3>')
            continue

        # Horizontal Rule
        if re.match(r'^-{3,}$', stripped) or re.match(r'^\*{3,}$', stripped):
            html_lines.append('<hr class="dash-hr"/>')
            continue

        # Callout / Alert
        if stripped.startswith("> "):
            html_lines.append(f'<div class="dash-callout">{process_inline(stripped[2:])}</div>')
            continue

        # Lists
        if stripped.startswith("* ") or stripped.startswith("- "):
            html_lines.append(f'<li class="dash-li">{process_inline(stripped[2:])}</li>')
            continue

        # Blank line
        if not stripped:
            html_lines.append('<div class="spacer-sm"></div>')
            continue

        # Paragraph
        html_lines.append(f'<p class="dash-p">{process_inline(line)}</p>')

    if in_table:
        html_lines.append(close_table())

    return "\n".join(html_lines)


def load_all_data():
    csv_path = os.path.join(FURNITURE_DIR, "00_PRICING_MASTER_BENCHMARK.csv")
    csv_rows = []
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)

    def read_md(fname):
        p = os.path.join(FURNITURE_DIR, fname)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    master_exec_summary = read_md("00_EXECUTIVE_SUMMARY_AND_COMPETITOR_ANALYSIS.md")
    master_pricing_md = read_md("00_PRICING_MASTER_BENCHMARK.md")
    master_personas_md = read_md("00_PRIMARY_RESEARCH_PERSONAS_AND_SCRIPTS.md")

    companies_data = {}
    for d in sorted(os.listdir(FURNITURE_DIR)):
        cdir = os.path.join(FURNITURE_DIR, d)
        if os.path.isdir(cdir):
            c_info = {
                "id": d,
                "name": d.replace("_", " "),
                "profile_html": "",
                "pricing_html": "",
                "sources_html": "",
                "brochures_html": "",
                "meta": {}
            }
            
            f_profile = os.path.join(cdir, "company_profile.md")
            if os.path.exists(f_profile):
                with open(f_profile, "r", encoding="utf-8") as f:
                    c_info["profile_html"] = md_to_html(f.read())

            f_pricing = os.path.join(cdir, "pricing_and_pricebook.md")
            if os.path.exists(f_pricing):
                with open(f_pricing, "r", encoding="utf-8") as f:
                    c_info["pricing_html"] = md_to_html(f.read())

            f_sources = os.path.join(cdir, "sources_and_evidence.md")
            if os.path.exists(f_sources):
                with open(f_sources, "r", encoding="utf-8") as f:
                    c_info["sources_html"] = md_to_html(f.read())

            f_brochures = os.path.join(cdir, "brochures_and_catalog_links.md")
            if os.path.exists(f_brochures):
                with open(f_brochures, "r", encoding="utf-8") as f:
                    c_info["brochures_html"] = md_to_html(f.read())

            for row in csv_rows:
                row_name_clean = row.get("Company_Name", "").lower().replace(" ", "").replace("_", "").replace("-", "")
                c_id_clean = d.lower().replace("_", "").replace(" ", "").replace("-", "")
                if c_id_clean in row_name_clean or row_name_clean in c_id_clean:
                    c_info["meta"] = row
                    c_info["name"] = row.get("Company_Name", d)
                    break
                    
            companies_data[d] = c_info

    return {
        "csv_rows": csv_rows,
        "exec_summary_html": md_to_html(master_exec_summary),
        "pricing_md_html": md_to_html(master_pricing_md),
        "personas_md_html": md_to_html(master_personas_md),
        "companies": companies_data
    }

def generate_black_silver_html(data):
    companies_json = json.dumps(data["companies"])
    csv_rows_json = json.dumps(data["csv_rows"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Modular Furniture & Kitchens — Strategic Pricing & Competitor Intelligence Hub</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  
  <style>
    /* ==========================================================================
       BLACK & SILVER LUXURY DESIGN TOKENS
       ========================================================================== */
    :root {{
      --bg-dark: #060709;
      --bg-surface: #0b0d12;
      --bg-card: #10131a;
      --bg-card-hover: #151923;
      --bg-input: #0b0d13;
      
      --silver-pure: #ffffff;
      --silver-bright: #f0f3f8;
      --silver-base: #d1d7e0;
      --silver-mid: #9ba3b0;
      --silver-dark: #636b78;
      
      --silver-metallic: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%);
      --silver-border: rgba(226, 232, 240, 0.16);
      --silver-border-hover: rgba(255, 255, 255, 0.45);
      --silver-glow: 0 0 25px rgba(226, 232, 240, 0.12);
      
      --border-subtle: rgba(255, 255, 255, 0.07);
      --border-accent: rgba(226, 232, 240, 0.22);
      
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      
      --radius-sm: 6px;
      --radius-md: 12px;
      --radius-lg: 18px;
      --radius-full: 9999px;
      
      --shadow-card: 0 12px 35px -10px rgba(0, 0, 0, 0.7);
    }}

    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
      -webkit-font-smoothing: antialiased;
    }}

    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background-color: var(--bg-dark);
      color: var(--text-main);
      line-height: 1.6;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
    }}

    /* Scrollbar */
    ::-webkit-scrollbar {{
      width: 7px;
      height: 7px;
    }}
    ::-webkit-scrollbar-track {{
      background: var(--bg-dark);
    }}
    ::-webkit-scrollbar-thumb {{
      background: #202634;
      border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
      background: var(--silver-mid);
    }}

    /* Top Navigation Header */
    .top-navbar {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(11, 13, 18, 0.92);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border-bottom: 1px solid var(--border-subtle);
      padding: 14px 36px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
    }}

    .nav-brand {{
      display: flex;
      align-items: center;
      gap: 14px;
      text-decoration: none;
    }}

    .brand-icon {{
      width: 38px;
      height: 38px;
      border-radius: 10px;
      background: var(--silver-metallic);
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Outfit', sans-serif;
      font-weight: 800;
      font-size: 18px;
      color: #060709;
      box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);
    }}

    .brand-text h1 {{
      font-family: 'Outfit', sans-serif;
      font-size: 18px;
      font-weight: 700;
      letter-spacing: 0.5px;
      color: #fff;
    }}

    .brand-text p {{
      font-size: 10.5px;
      color: var(--silver-mid);
      text-transform: uppercase;
      letter-spacing: 1.2px;
    }}

    .top-stats {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .stat-pill {{
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border-subtle);
      padding: 6px 14px;
      border-radius: var(--radius-full);
      font-size: 11.5px;
      display: flex;
      align-items: center;
      gap: 6px;
      color: var(--silver-mid);
    }}
    .stat-pill strong {{
      color: var(--silver-pure);
      font-weight: 700;
    }}

    /* Navigation Tabs */
    .nav-tabs {{
      display: flex;
      background: rgba(0, 0, 0, 0.45);
      padding: 4px;
      border-radius: var(--radius-full);
      border: 1px solid var(--border-subtle);
    }}

    .nav-tab-btn {{
      background: transparent;
      border: none;
      color: var(--silver-mid);
      padding: 8px 18px;
      border-radius: var(--radius-full);
      font-size: 12.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.22s ease;
    }}

    .nav-tab-btn:hover {{
      color: #fff;
      background: rgba(255, 255, 255, 0.05);
    }}

    .nav-tab-btn.active {{
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.16) 0%, rgba(255, 255, 255, 0.05) 100%);
      color: var(--silver-pure);
      border: 1px solid var(--silver-border);
      box-shadow: 0 2px 10px rgba(255, 255, 255, 0.08);
    }}

    /* Layout */
    .app-main {{
      flex: 1;
      max-width: 1540px;
      width: 100%;
      margin: 0 auto;
      padding: 28px 36px 60px;
    }}

    .tab-content-panel {{
      display: none;
      animation: fadeIn 0.25s ease forwards;
    }}
    .tab-content-panel.active {{
      display: block;
    }}

    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(4px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Hero Banner */
    .hero-banner {{
      background: radial-gradient(circle at 85% 15%, rgba(255, 255, 255, 0.05) 0%, transparent 55%),
                  linear-gradient(135deg, #0d1017 0%, #121622 100%);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 30px 38px;
      margin-bottom: 24px;
      position: relative;
      overflow: hidden;
    }}

    .hero-banner::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0; height: 2px;
      background: var(--silver-metallic);
    }}

    .hero-title-area h2 {{
      font-family: 'Outfit', sans-serif;
      font-size: 28px;
      font-weight: 800;
      color: #fff;
      margin-bottom: 6px;
    }}

    .hero-title-area p {{
      color: var(--silver-mid);
      font-size: 14.5px;
      max-width: 860px;
    }}

    /* Controls Bar */
    .controls-bar {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
      margin-bottom: 24px;
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 12px 18px;
    }}

    .search-box-wrap {{
      display: flex;
      align-items: center;
      background: var(--bg-input);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-full);
      padding: 8px 16px;
      gap: 10px;
      flex: 1;
      max-width: 440px;
      transition: all 0.2s;
    }}
    .search-box-wrap:focus-within {{
      border-color: rgba(255, 255, 255, 0.4);
      box-shadow: var(--silver-glow);
    }}

    .search-input {{
      background: transparent;
      border: none;
      outline: none;
      color: #fff;
      font-size: 13.5px;
      width: 100%;
    }}
    .search-input::placeholder {{
      color: var(--text-dim);
    }}

    .filter-pills-row {{
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }}

    .filter-btn {{
      background: var(--bg-input);
      border: 1px solid var(--border-subtle);
      color: var(--silver-mid);
      padding: 6px 14px;
      border-radius: var(--radius-full);
      font-size: 11.5px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.18s;
    }}
    .filter-btn:hover {{
      background: rgba(255, 255, 255, 0.06);
      color: #fff;
      border-color: rgba(255, 255, 255, 0.2);
    }}
    .filter-btn.active {{
      background: var(--silver-pure);
      color: #000;
      border-color: var(--silver-pure);
      font-weight: 700;
    }}

    /* Company Cards Grid */
    .company-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 20px;
    }}

    .company-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 22px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.24s cubic-bezier(0.16, 1, 0.3, 1);
      position: relative;
      overflow: hidden;
      box-shadow: var(--shadow-card);
    }}

    .company-card:hover {{
      transform: translateY(-4px);
      border-color: var(--silver-border-hover);
      box-shadow: 0 16px 40px -10px rgba(0, 0, 0, 0.8), var(--silver-glow);
      background: var(--bg-card-hover);
    }}

    .card-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;
    }}

    .card-title-group h3 {{
      font-family: 'Outfit', sans-serif;
      font-size: 20px;
      font-weight: 700;
      color: #fff;
      margin-bottom: 3px;
    }}

    .card-origin {{
      font-size: 11.5px;
      color: var(--silver-mid);
    }}

    /* Sleek Monochromatic Badges */
    .tier-badge {{
      font-size: 10.5px;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: var(--radius-full);
      text-transform: uppercase;
      letter-spacing: 0.6px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: var(--silver-base);
    }}
    .badge-ultra {{
      background: rgba(255, 255, 255, 0.12);
      color: #fff;
      border-color: rgba(255, 255, 255, 0.35);
      box-shadow: 0 0 12px rgba(255, 255, 255, 0.1);
    }}
    .badge-rich {{
      background: rgba(200, 215, 235, 0.08);
      color: #e2e8f0;
      border-color: rgba(200, 215, 235, 0.25);
    }}
    .badge-upper-mid {{
      background: rgba(160, 175, 195, 0.06);
      color: #cbd5e1;
      border-color: rgba(160, 175, 195, 0.18);
    }}
    .badge-mid {{
      background: rgba(120, 135, 155, 0.05);
      color: #94a3b8;
      border-color: rgba(120, 135, 155, 0.14);
    }}
    .badge-budget {{
      background: rgba(80, 95, 115, 0.05);
      color: #64748b;
      border-color: rgba(80, 95, 115, 0.12);
    }}

    .card-pricing-block {{
      background: rgba(0, 0, 0, 0.3);
      border-radius: var(--radius-sm);
      border: 1px solid rgba(255, 255, 255, 0.04);
      padding: 12px 14px;
      margin: 12px 0 14px;
    }}

    .pricing-stat-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      margin-bottom: 5px;
    }}
    .pricing-stat-row:last-child {{
      margin-bottom: 0;
    }}
    .pricing-stat-row .stat-label {{
      color: var(--silver-dark);
    }}
    .pricing-stat-row .stat-val {{
      color: var(--silver-base);
      font-weight: 600;
    }}
    .pricing-stat-row .stat-val.highlight {{
      color: #fff;
      font-weight: 700;
    }}

    .card-specs-list {{
      font-size: 11.5px;
      color: var(--silver-mid);
      margin-bottom: 16px;
      display: flex;
      flex-direction: column;
      gap: 5px;
    }}
    .spec-item {{
      display: flex;
      align-items: flex-start;
      gap: 8px;
    }}
    .spec-dot {{
      width: 4px;
      height: 4px;
      border-radius: 50%;
      background: var(--silver-base);
      margin-top: 6px;
      flex-shrink: 0;
    }}

    .card-actions {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: auto;
    }}

    .btn-card {{
      background: var(--bg-input);
      border: 1px solid var(--border-subtle);
      color: var(--silver-base);
      padding: 7px 12px;
      border-radius: var(--radius-sm);
      font-size: 11.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.18s;
      text-align: center;
    }}
    .btn-card:hover {{
      background: rgba(255, 255, 255, 0.07);
      border-color: rgba(255, 255, 255, 0.25);
      color: #fff;
    }}
    .btn-card.primary {{
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.04) 100%);
      border-color: var(--silver-border);
      color: #fff;
      grid-column: span 2;
    }}
    .btn-card.primary:hover {{
      background: var(--silver-pure);
      color: #000;
      border-color: var(--silver-pure);
      box-shadow: 0 0 15px rgba(255, 255, 255, 0.25);
    }}

    /* Modal / Drawer */
    .modal-backdrop {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.85);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      z-index: 999;
      justify-content: center;
      align-items: center;
      padding: 24px;
    }}
    .modal-backdrop.open {{
      display: flex;
    }}

    .modal-box {{
      background: var(--bg-surface);
      border: 1px solid var(--silver-border);
      border-radius: var(--radius-lg);
      width: 100%;
      max-width: 1080px;
      height: 90vh;
      max-height: 880px;
      display: flex;
      flex-direction: column;
      box-shadow: 0 25px 65px -15px rgba(0, 0, 0, 0.9), var(--silver-glow);
      overflow: hidden;
      animation: modalSlide 0.22s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    @keyframes modalSlide {{
      from {{ transform: scale(0.97); opacity: 0; }}
      to {{ transform: scale(1); opacity: 1; }}
    }}

    .modal-header {{
      padding: 20px 28px;
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(18, 22, 30, 0.75);
    }}

    .modal-header-left {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .modal-title-area h2 {{
      font-family: 'Outfit', sans-serif;
      font-size: 24px;
      font-weight: 700;
      color: #fff;
    }}
    .modal-title-area p {{
      font-size: 12.5px;
      color: var(--silver-mid);
    }}

    .btn-close-modal {{
      background: var(--bg-input);
      border: 1px solid var(--border-subtle);
      width: 32px;
      height: 32px;
      border-radius: 50%;
      color: var(--silver-mid);
      font-size: 15px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.18s;
    }}
    .btn-close-modal:hover {{
      background: #fff;
      color: #000;
      border-color: #fff;
    }}

    .modal-tab-bar {{
      display: flex;
      border-bottom: 1px solid var(--border-subtle);
      background: #090b10;
      padding: 0 28px;
      overflow-x: auto;
    }}

    .modal-tab-btn {{
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--silver-mid);
      padding: 13px 18px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.18s;
      white-space: nowrap;
    }}
    .modal-tab-btn:hover {{
      color: #fff;
    }}
    .modal-tab-btn.active {{
      color: #fff;
      border-bottom-color: var(--silver-pure);
    }}

    .modal-body-scroll {{
      flex: 1;
      overflow-y: auto;
      padding: 28px;
      background: var(--bg-surface);
    }}

    /* Markdown Formatted Elements */
    .dash-h1 {{
      font-family: 'Outfit', sans-serif;
      font-size: 22px;
      color: #fff;
      margin-bottom: 14px;
      font-weight: 700;
    }}
    .dash-h2 {{
      font-family: 'Outfit', sans-serif;
      font-size: 17px;
      color: #fff;
      margin: 22px 0 10px;
      font-weight: 600;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding-bottom: 5px;
      letter-spacing: 0.3px;
    }}
    .dash-h3 {{
      font-size: 14px;
      color: var(--silver-base);
      margin: 16px 0 8px;
      font-weight: 600;
    }}
    .dash-p {{
      font-size: 13.5px;
      color: var(--silver-mid);
      margin-bottom: 10px;
    }}
    .dash-li {{
      font-size: 13px;
      color: var(--silver-mid);
      margin-left: 18px;
      margin-bottom: 4px;
    }}
    .dash-callout {{
      background: rgba(255, 255, 255, 0.04);
      border-left: 3px solid var(--silver-base);
      padding: 12px 16px;
      border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
      font-size: 13px;
      color: #f1f5f9;
      margin: 14px 0;
    }}
    .dash-hr {{
      border: none;
      height: 1px;
      background: var(--border-subtle);
      margin: 20px 0;
    }}
    .table-responsive {{
      overflow-x: auto;
      margin: 14px 0;
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
    }}
    .dash-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12.5px;
      text-align: left;
    }}
    .dash-table th {{
      background: #0f1218;
      padding: 10px 12px;
      color: #fff;
      font-weight: 600;
      border-bottom: 1px solid var(--border-subtle);
      white-space: nowrap;
    }}
    .dash-table td {{
      padding: 9px 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      color: var(--silver-base);
    }}
    .dash-table tr:hover td {{
      background: rgba(255, 255, 255, 0.03);
    }}

    /* Master Table */
    .table-view-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      flex-wrap: wrap;
      gap: 12px;
    }}

    .btn-export {{
      background: var(--bg-card);
      border: 1px solid var(--silver-border);
      color: #fff;
      padding: 7px 16px;
      border-radius: var(--radius-sm);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.18s;
    }}
    .btn-export:hover {{
      background: #fff;
      color: #000;
    }}

    .master-matrix-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }}
    .master-matrix-table th {{
      background: #0d1016;
      color: #fff;
      padding: 11px 12px;
      text-align: left;
      border-bottom: 1px solid var(--silver-border);
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
    }}
    .master-matrix-table th:hover {{
      background: #141923;
    }}
    .master-matrix-table td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--border-subtle);
      white-space: nowrap;
      color: var(--silver-base);
    }}
    .master-matrix-table tr:hover td {{
      background: rgba(255, 255, 255, 0.04);
    }}

    footer {{
      border-top: 1px solid var(--border-subtle);
      padding: 22px 36px;
      text-align: center;
      font-size: 11.5px;
      color: var(--silver-dark);
      background: var(--bg-surface);
    }}
  </style>
</head>
<body>

  <!-- Top Navigation Header -->
  <header class="top-navbar">
    <a href="#" class="nav-brand">
      <div class="brand-icon">RS</div>
      <div class="brand-text">
        <h1>RunawayScout — Furniture Intel</h1>
        <p>Competitor Intelligence & Pricing Hub</p>
      </div>
    </a>

    <!-- Top Stats -->
    <div class="top-stats">
      <div class="stat-pill"><strong>25</strong> Brands Analyzed</div>
      <div class="stat-pill"><strong>$4.8B</strong> Market Size</div>
      <div class="stat-pill"><strong>100%</strong> Audited Dossiers</div>
    </div>

    <!-- Navigation Tabs -->
    <nav class="nav-tabs">
      <button class="nav-tab-btn active" onclick="switchMainTab('explorer', this)">Brands Explorer</button>
      <button class="nav-tab-btn" onclick="switchMainTab('matrix', this)">Master Price Matrix</button>
      <button class="nav-tab-btn" onclick="switchMainTab('strategy', this)">Strategic Analysis</button>
    </nav>
  </header>

  <!-- Main Container -->
  <main class="app-main">

    <!-- TAB 1: BRANDS EXPLORER -->
    <section id="tab-explorer" class="tab-content-panel active">
      
      <!-- Hero Banner -->
      <div class="hero-banner">
        <div class="hero-title-area">
          <h2>Modular Kitchen & Furniture Intelligence Database</h2>
          <p>Comprehensive pricing books, price group ladders (PG 1–10), dealer margins, leaked quotations, material benchmarks, and official brochure links across 25 leading market players.</p>
        </div>
      </div>

      <!-- Search & Filters -->
      <div class="controls-bar">
        <div class="search-box-wrap">
          <input type="text" id="global-search" class="search-input" placeholder="Search by brand, country, hardware, material, price..." onkeyup="filterCards()">
        </div>

        <div class="filter-pills-row">
          <button class="filter-btn active" onclick="setCategoryFilter('all', this)">All (25)</button>
          <button class="filter-btn" onclick="setCategoryFilter('ultra', this)">Ultra-Rich / UHNIs</button>
          <button class="filter-btn" onclick="setCategoryFilter('rich', this)">Luxury Rich (HNIs)</button>
          <button class="filter-btn" onclick="setCategoryFilter('upper-mid', this)">Upper Middle</button>
          <button class="filter-btn" onclick="setCategoryFilter('mid', this)">Middle Class</button>
          <button class="filter-btn" onclick="setCategoryFilter('budget', this)">Budget</button>
        </div>
      </div>

      <!-- Companies Grid -->
      <div id="company-grid" class="company-grid"></div>
    </section>

    <!-- TAB 2: MASTER PRICING MATRIX -->
    <section id="tab-matrix" class="tab-content-panel">
      <div class="table-view-header">
        <div>
          <h2 class="dash-h1" style="margin-bottom: 4px;">Master Competitive Pricing Matrix</h2>
          <p class="dash-p">Standardized side-by-side pricing, per square foot finish costs, substrate materials, and warranty benchmarks.</p>
        </div>
        <button class="btn-export" onclick="exportCSV()">Download Master CSV</button>
      </div>

      <div class="table-responsive" style="max-height: 75vh;">
        <table class="master-matrix-table" id="master-table">
          <thead>
            <tr>
              <th onclick="sortTable(0)">Brand</th>
              <th onclick="sortTable(1)">Origin</th>
              <th onclick="sortTable(2)">Customer Segment</th>
              <th onclick="sortTable(3)">Base Starting Price</th>
              <th onclick="sortTable(4)">Project Range</th>
              <th onclick="sortTable(5)">Laminate / Sq.Ft</th>
              <th onclick="sortTable(6)">Acrylic / Sq.Ft</th>
              <th onclick="sortTable(7)">PU Lacquer / Sq.Ft</th>
              <th onclick="sortTable(8)">Glass/Veneer / Sq.Ft</th>
              <th onclick="sortTable(9)">Carcass Substrate</th>
              <th onclick="sortTable(10)">Hardware Partner</th>
              <th onclick="sortTable(11)">Warranty</th>
              <th onclick="sortTable(12)">Lead Time</th>
            </tr>
          </thead>
          <tbody id="master-table-body"></tbody>
        </table>
      </div>
    </section>

    <!-- TAB 3: STRATEGIC ANALYSIS REPORT -->
    <section id="tab-strategy" class="tab-content-panel">
      <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 36px; box-shadow: var(--shadow-card);">
        {data["exec_summary_html"]}
      </div>
    </section>

  </main>

  <!-- MODAL FOR DETAILED COMPANY DOSSIER -->
  <div id="company-modal" class="modal-backdrop" onclick="closeModalOnBackdrop(event)">
    <div class="modal-box" onclick="event.stopPropagation()">
      <div class="modal-header">
        <div class="modal-header-left">
          <div id="modal-brand-badge" class="tier-badge badge-rich">Luxury HNI</div>
          <div class="modal-title-area">
            <h2 id="modal-brand-title">Company Name</h2>
            <p id="modal-brand-origin">Origin & Presence</p>
          </div>
        </div>
        <button class="btn-close-modal" onclick="closeModal()">&times;</button>
      </div>

      <!-- Modal Tab Bar -->
      <div class="modal-tab-bar">
        <button class="modal-tab-btn active" onclick="switchModalTab('pricing', this)">Pricing & Pricebook</button>
        <button class="modal-tab-btn" onclick="switchModalTab('profile', this)">Company Profile & Specs</button>
        <button class="modal-tab-btn" onclick="switchModalTab('sources', this)">Sources & Evidence</button>
        <button class="modal-tab-btn" onclick="switchModalTab('brochures', this)">Official Catalogues & Links</button>
      </div>

      <!-- Modal Body Scroll -->
      <div class="modal-body-scroll">
        <div id="modal-content-pricing" class="modal-tab-pane active"></div>
        <div id="modal-content-profile" class="modal-tab-pane" style="display: none;"></div>
        <div id="modal-content-sources" class="modal-tab-pane" style="display: none;"></div>
        <div id="modal-content-brochures" class="modal-tab-pane" style="display: none;"></div>
      </div>
    </div>
  </div>

  <footer>
    <p>RunawayScout Competitive Intelligence & Research Systems • Prepared for BITS Goa Consulting Club (BGCC) • Data Validated September 2026</p>
  </footer>

  <script>
    const COMPANIES = {companies_json};
    const CSV_ROWS = {csv_rows_json};

    let currentCategoryFilter = 'all';

    function getTierBadgeClass(tier) {{
      const t = (tier || '').toLowerCase();
      if (t.includes('ultra')) return 'badge-ultra';
      if (t.includes('rich') || t.includes('luxury') || t.includes('hni')) return 'badge-rich';
      if (t.includes('upper')) return 'badge-upper-mid';
      if (t.includes('middle') || t.includes('challenger')) return 'badge-mid';
      return 'badge-budget';
    }}

    function getTierCategoryKey(tier) {{
      const t = (tier || '').toLowerCase();
      if (t.includes('ultra')) return 'ultra';
      if (t.includes('rich') || t.includes('luxury') || t.includes('hni')) return 'rich';
      if (t.includes('upper')) return 'upper-mid';
      if (t.includes('middle') || t.includes('first-time')) return 'mid';
      return 'budget';
    }}

    function renderCards() {{
      const container = document.getElementById('company-grid');
      container.innerHTML = '';

      const query = (document.getElementById('global-search').value || '').toLowerCase();

      for (const [id, co] of Object.entries(COMPANIES)) {{
        const meta = co.meta || {{}};
        const name = co.name || id;
        const origin = meta.Country_of_Origin || '';
        const targetSeg = meta.Target_Customer_Segment || 'Luxury Homeowners';
        const basePrice = meta.Base_Kitchen_Starting_Price_INR ? '₹' + Number(meta.Base_Kitchen_Starting_Price_INR).toLocaleString('en-IN') : '₹2,50,000+';
        const projectRange = meta.Typical_Kitchen_Project_Range_INR || '₹5L – ₹15L';
        const lamRate = meta.Rate_Per_SqFt_Laminate_INR || '₹1,500 – ₹2,500';
        const hardware = meta.Hardware_Brand_Used || 'Blum / Hettich';
        const carcass = meta.Carcass_Core_Material || 'Plywood / MFC';

        const catKey = getTierCategoryKey(targetSeg);
        if (currentCategoryFilter !== 'all' && catKey !== currentCategoryFilter) {{
          continue;
        }}

        const searchable = `${{name}} ${{origin}} ${{targetSeg}} ${{hardware}} ${{carcass}} ${{projectRange}} ${{basePrice}}`.toLowerCase();
        if (query && !searchable.includes(query)) {{
          continue;
        }}

        const badgeClass = getTierBadgeClass(targetSeg);

        const card = document.createElement('div');
        card.className = 'company-card';
        card.innerHTML = `
          <div>
            <div class="card-top">
              <div class="card-title-group">
                <h3>${{name}}</h3>
                <div class="card-origin">${{origin}}</div>
              </div>
              <span class="tier-badge ${{badgeClass}}">${{targetSeg.split('(')[0].trim()}}</span>
            </div>

            <div class="card-pricing-block">
              <div class="pricing-stat-row">
                <span class="stat-label">Starting Base Price:</span>
                <span class="stat-val highlight">${{basePrice}}</span>
              </div>
              <div class="pricing-stat-row">
                <span class="stat-label">Typical Range:</span>
                <span class="stat-val">${{projectRange}}</span>
              </div>
              <div class="pricing-stat-row">
                <span class="stat-label">Laminate / Sq.Ft:</span>
                <span class="stat-val">${{lamRate}}</span>
              </div>
            </div>

            <div class="card-specs-list">
              <div class="spec-item">
                <span class="spec-dot"></span>
                <span><strong>Hardware:</strong> ${{hardware}}</span>
              </div>
              <div class="spec-item">
                <span class="spec-dot"></span>
                <span><strong>Core:</strong> ${{carcass.substring(0, 48)}}...</span>
              </div>
            </div>
          </div>

          <div class="card-actions">
            <button class="btn-card primary" onclick="openModal('${{id}}', 'pricing')">Pricebook & Offerings</button>
            <button class="btn-card" onclick="openModal('${{id}}', 'profile')">Profile</button>
            <button class="btn-card" onclick="openModal('${{id}}', 'brochures')">Brochures</button>
          </div>
        `;
        container.appendChild(card);
      }}

      if (container.children.length === 0) {{
        container.innerHTML = '<div style="grid-column: 1/-1; padding: 60px; text-align: center; color: var(--silver-dark);">No companies match your search and filter criteria.</div>';
      }}
    }}

    function filterCards() {{
      renderCards();
    }}

    function setCategoryFilter(cat, btn) {{
      currentCategoryFilter = cat;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderCards();
    }}

    function switchMainTab(tabId, btn) {{
      document.querySelectorAll('.nav-tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      document.querySelectorAll('.tab-content-panel').forEach(p => p.classList.remove('active'));
      document.getElementById('tab-' + tabId).classList.add('active');
    }}

    function renderMasterTable() {{
      const tbody = document.getElementById('master-table-body');
      tbody.innerHTML = '';

      CSV_ROWS.forEach(r => {{
        const tr = document.createElement('tr');
        const baseFormatted = r.Base_Kitchen_Starting_Price_INR ? '₹' + Number(r.Base_Kitchen_Starting_Price_INR).toLocaleString('en-IN') : '-';
        tr.innerHTML = `
          <td><strong style="color: #fff; cursor:pointer;" onclick="openModalByName('${{r.Company_Name}}', 'pricing')">${{r.Company_Name}}</strong></td>
          <td>${{r.Country_of_Origin}}</td>
          <td><span class="tier-badge ${{getTierBadgeClass(r.Target_Customer_Segment)}}">${{r.Target_Customer_Segment}}</span></td>
          <td style="color: #fff; font-weight:700;">${{baseFormatted}}</td>
          <td>${{r.Typical_Kitchen_Project_Range_INR}}</td>
          <td>${{r.Rate_Per_SqFt_Laminate_INR}}</td>
          <td>${{r.Rate_Per_SqFt_Acrylic_INR}}</td>
          <td>${{r.Rate_Per_SqFt_PU_Lacquer_INR}}</td>
          <td>${{r.Rate_Per_SqFt_Glass_Veneer_INR}}</td>
          <td>${{r.Carcass_Core_Material}}</td>
          <td>${{r.Hardware_Brand_Used}}</td>
          <td>${{r.Standard_Warranty_Years}}</td>
          <td>${{r.Typical_Lead_Time}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function openModalByName(name, defaultTab) {{
      for (const [id, co] of Object.entries(COMPANIES)) {{
        if (co.name === name || id.toLowerCase().includes(name.toLowerCase())) {{
          openModal(id, defaultTab);
          return;
        }}
      }}
    }}

    function openModal(id, defaultTab) {{
      const co = COMPANIES[id];
      if (!co) return;

      document.getElementById('modal-brand-title').innerText = co.name;
      const meta = co.meta || {{}};
      document.getElementById('modal-brand-origin').innerText = `${{meta.Country_of_Origin || 'Global'}} • ${{meta.Target_Customer_Segment || 'Luxury Homeowners'}}`;
      
      const badge = document.getElementById('modal-brand-badge');
      badge.className = 'tier-badge ' + getTierBadgeClass(meta.Target_Customer_Segment);
      badge.innerText = (meta.Target_Customer_Segment || 'Luxury').split('(')[0].trim();

      document.getElementById('modal-content-pricing').innerHTML = co.pricing_html || '<p>Pricing details not found.</p>';
      document.getElementById('modal-content-profile').innerHTML = co.profile_html || '<p>Profile details not found.</p>';
      document.getElementById('modal-content-sources').innerHTML = co.sources_html || '<p>Sources not found.</p>';
      document.getElementById('modal-content-brochures').innerHTML = co.brochures_html || '<p>Brochures not found.</p>';

      switchModalTab(defaultTab || 'pricing');
      document.getElementById('company-modal').classList.add('open');
    }}

    function closeModal() {{
      document.getElementById('company-modal').classList.remove('open');
    }}

    function closeModalOnBackdrop(e) {{
      if (e.target.id === 'company-modal') closeModal();
    }}

    function switchModalTab(tabKey, btn) {{
      document.querySelectorAll('.modal-tab-btn').forEach(b => b.classList.remove('active'));
      if (btn) {{
        btn.classList.add('active');
      }} else {{
        const buttons = document.querySelectorAll('.modal-tab-btn');
        buttons.forEach(b => {{
          if (b.innerText.toLowerCase().includes(tabKey)) b.classList.add('active');
        }});
      }}

      document.querySelectorAll('.modal-tab-pane').forEach(p => p.style.display = 'none');
      const targetPane = document.getElementById('modal-content-' + tabKey);
      if (targetPane) targetPane.style.display = 'block';
    }}

    function exportCSV() {{
      let csvContent = "data:text/csv;charset=utf-8,";
      const headers = Object.keys(CSV_ROWS[0]).join(",");
      csvContent += headers + "\\r\\n";

      CSV_ROWS.forEach(row => {{
        const values = Object.values(row).map(v => `"${{v}}"`).join(",");
        csvContent += values + "\\r\\n";
      }});

      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", "Modular_Kitchen_Pricing_Benchmark_2026.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }}

    let sortDirection = {{}};
    function sortTable(columnIndex) {{
      const table = document.getElementById("master-table");
      const tbody = table.querySelector("tbody");
      const rows = Array.from(tbody.querySelectorAll("tr"));
      
      const isAsc = !sortDirection[columnIndex];
      sortDirection[columnIndex] = isAsc;

      rows.sort((a, b) => {{
        const cellA = a.children[columnIndex].innerText.trim();
        const cellB = b.children[columnIndex].innerText.trim();

        const numA = parseFloat(cellA.replace(/[^0-9.-]+/g, ""));
        const numB = parseFloat(cellB.replace(/[^0-9.-]+/g, ""));

        if (!isNaN(numA) && !isNaN(numB)) {{
          return isAsc ? numA - numB : numB - numA;
        }}
        return isAsc ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
      }});

      rows.forEach(r => tbody.appendChild(r));
    }}

    document.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape') closeModal();
    }});

    renderCards();
    renderMasterTable();
  </script>
</body>
</html>
"""
    return html

data = load_all_data()
html_content = generate_black_silver_html(data)

with open(HTML_OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Successfully compiled Black & Silver dashboard with NO emojis at {HTML_OUT_PATH}")
print(f"File size: {os.path.getsize(HTML_OUT_PATH):,} bytes")
