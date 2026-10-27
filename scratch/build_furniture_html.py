"""
build_furniture_html.py
Parses the entire Furniture/ directory (all 25 company folders, profiles, pricebooks,
sources, brochures, CSV benchmarks, and executive reports) and compiles it into an
ultra-premium, interactive, single-page application at Furniture/index.html.
"""

import os
import csv
import json
import re

FURNITURE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Furniture"))
HTML_OUT_PATH = os.path.join(FURNITURE_DIR, "index.html")

def md_to_html(md_text):
    """Simple robust markdown to HTML converter for offline dashboard rendering."""
    lines = md_text.split("\n")
    html_lines = []
    in_table = False
    table_rows = []
    in_code = False
    code_lines = []
    in_list = False

    def process_inline(text):
        # Links
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', text)
        # Bold
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        # Code inline
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
            # Check if separator row
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

        # Blockquote / Alert
        if stripped.startswith("> "):
            html_lines.append(f'<div class="dash-callout">{process_inline(stripped[2:])}</div>')
            continue

        # Unordered list
        if stripped.startswith("* ") or stripped.startswith("- "):
            html_lines.append(f'<li class="dash-li">{process_inline(stripped[2:])}</li>')
            continue

        # Empty line
        if not stripped:
            html_lines.append('<div class="spacer-sm"></div>')
            continue

        # Regular paragraph
        html_lines.append(f'<p class="dash-p">{process_inline(line)}</p>')

    if in_table:
        html_lines.append(close_table())

    return "\n".join(html_lines)


def load_all_data():
    """Reads all CSV rows, master reports, and individual company directories."""
    # 1. Master CSV
    csv_path = os.path.join(FURNITURE_DIR, "00_PRICING_MASTER_BENCHMARK.csv")
    csv_rows = []
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)

    # 2. Master Markdown Reports
    def read_md(fname):
        p = os.path.join(FURNITURE_DIR, fname)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    master_exec_summary = read_md("00_EXECUTIVE_SUMMARY_AND_COMPETITOR_ANALYSIS.md")
    master_pricing_md = read_md("00_PRICING_MASTER_BENCHMARK.md")
    master_personas_md = read_md("00_PRIMARY_RESEARCH_PERSONAS_AND_SCRIPTS.md")

    # 3. Company Directories
    companies_data = {}
    for d in sorted(os.listdir(FURNITURE_DIR)):
        cdir = os.path.join(FURNITURE_DIR, d)
        if os.path.isdir(cdir):
            c_info = {
                "id": d,
                "name": d.replace("_", " "),
                "profile_raw": "",
                "pricing_raw": "",
                "sources_raw": "",
                "brochures_raw": "",
                "profile_html": "",
                "pricing_html": "",
                "sources_html": "",
                "brochures_html": "",
                "meta": {}
            }
            
            f_profile = os.path.join(cdir, "company_profile.md")
            if os.path.exists(f_profile):
                with open(f_profile, "r", encoding="utf-8") as f:
                    c_info["profile_raw"] = f.read()
                    c_info["profile_html"] = md_to_html(c_info["profile_raw"])

            f_pricing = os.path.join(cdir, "pricing_and_pricebook.md")
            if os.path.exists(f_pricing):
                with open(f_pricing, "r", encoding="utf-8") as f:
                    c_info["pricing_raw"] = f.read()
                    c_info["pricing_html"] = md_to_html(c_info["pricing_raw"])

            f_sources = os.path.join(cdir, "sources_and_evidence.md")
            if os.path.exists(f_sources):
                with open(f_sources, "r", encoding="utf-8") as f:
                    c_info["sources_raw"] = f.read()
                    c_info["sources_html"] = md_to_html(c_info["sources_raw"])

            f_brochures = os.path.join(cdir, "brochures_and_catalog_links.md")
            if os.path.exists(f_brochures):
                with open(f_brochures, "r", encoding="utf-8") as f:
                    c_info["brochures_raw"] = f.read()
                    c_info["brochures_html"] = md_to_html(c_info["brochures_raw"])

            # Find matching row in CSV for metadata
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

def generate_html(data):
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
    :root {{
      --bg-dark: #080a0f;
      --bg-surface: #0e131d;
      --bg-card: #131a27;
      --bg-card-hover: #192335;
      --bg-input: #101623;
      --border-subtle: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(212, 175, 55, 0.25);
      
      --gold-primary: #d4af37;
      --gold-light: #f3ce5e;
      --gold-glow: rgba(212, 175, 55, 0.15);
      
      --cyan-tech: #00d2ff;
      --emerald-accent: #10b981;
      --purple-royal: #a855f7;
      --coral-badge: #f43f5e;
      
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
      --radius-full: 9999px;
      
      --shadow-card: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
      --shadow-glow: 0 0 25px rgba(212, 175, 55, 0.18);
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

    /* --- Custom Scrollbar --- */
    ::-webkit-scrollbar {{
      width: 8px;
      height: 8px;
    }}
    ::-webkit-scrollbar-track {{
      background: var(--bg-dark);
    }}
    ::-webkit-scrollbar-thumb {{
      background: #253047;
      border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
      background: var(--gold-primary);
    }}

    /* --- Top Navigation Header --- */
    .top-navbar {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(14, 19, 29, 0.88);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border-bottom: 1px solid var(--border-subtle);
      padding: 14px 32px;
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
      width: 42px;
      height: 42px;
      border-radius: 12px;
      background: linear-gradient(135deg, #d4af37 0%, #856314 100%);
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Outfit', sans-serif;
      font-weight: 800;
      font-size: 20px;
      color: #000;
      box-shadow: 0 4px 15px rgba(212, 175, 55, 0.35);
    }}

    .brand-text h1 {{
      font-family: 'Outfit', sans-serif;
      font-size: 19px;
      font-weight: 700;
      letter-spacing: 0.5px;
      color: #fff;
    }}

    .brand-text p {{
      font-size: 11px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1.2px;
    }}

    /* Top Stats Pills */
    .top-stats {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .stat-pill {{
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-subtle);
      padding: 6px 14px;
      border-radius: var(--radius-full);
      font-size: 12px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .stat-pill strong {{
      color: var(--gold-primary);
      font-weight: 700;
    }}

    /* Navigation Tabs */
    .nav-tabs {{
      display: flex;
      background: rgba(0, 0, 0, 0.35);
      padding: 4px;
      border-radius: var(--radius-full);
      border: 1px solid var(--border-subtle);
    }}

    .nav-tab-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 8px 18px;
      border-radius: var(--radius-full);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.25s ease;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .nav-tab-btn:hover {{
      color: #fff;
      background: rgba(255, 255, 255, 0.05);
    }}

    .nav-tab-btn.active {{
      background: linear-gradient(135deg, rgba(212, 175, 55, 0.25) 0%, rgba(212, 175, 55, 0.1) 100%);
      color: var(--gold-light);
      border: 1px solid var(--border-accent);
      box-shadow: 0 2px 10px rgba(212, 175, 55, 0.15);
    }}

    /* --- App Container & Layout --- */
    .app-main {{
      flex: 1;
      max-width: 1540px;
      width: 100%;
      margin: 0 auto;
      padding: 28px 32px 60px;
    }}

    .tab-content-panel {{
      display: none;
      animation: fadeIn 0.3s ease forwards;
    }}
    .tab-content-panel.active {{
      display: block;
    }}

    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* --- Hero Banner --- */
    .hero-banner {{
      background: radial-gradient(circle at 80% 20%, rgba(212, 175, 55, 0.08) 0%, transparent 60%),
                  linear-gradient(135deg, #0e1422 0%, #121929 100%);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 32px 40px;
      margin-bottom: 28px;
      position: relative;
      overflow: hidden;
    }}

    .hero-banner::before {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0; height: 3px;
      background: linear-gradient(90deg, #d4af37, #00d2ff, #10b981, #d4af37);
    }}

    .hero-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: 20px;
    }}

    .hero-title-area h2 {{
      font-family: 'Outfit', sans-serif;
      font-size: 30px;
      font-weight: 800;
      color: #fff;
      margin-bottom: 8px;
    }}

    .hero-title-area p {{
      color: var(--text-muted);
      font-size: 15px;
      max-width: 820px;
    }}

    /* --- Search & Filter Bar --- */
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
      padding: 14px 20px;
    }}

    .search-box-wrap {{
      display: flex;
      align-items: center;
      background: var(--bg-input);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-full);
      padding: 8px 18px;
      gap: 12px;
      flex: 1;
      max-width: 440px;
      transition: all 0.2s;
    }}
    .search-box-wrap:focus-within {{
      border-color: var(--gold-primary);
      box-shadow: 0 0 15px var(--gold-glow);
    }}

    .search-input {{
      background: transparent;
      border: none;
      outline: none;
      color: #fff;
      font-size: 14px;
      width: 100%;
    }}
    .search-input::placeholder {{
      color: var(--text-dim);
    }}

    .filter-pills-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}

    .filter-btn {{
      background: var(--bg-input);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      padding: 6px 14px;
      border-radius: var(--radius-full);
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .filter-btn:hover {{
      background: rgba(255, 255, 255, 0.08);
      color: #fff;
    }}
    .filter-btn.active {{
      background: var(--gold-primary);
      color: #000;
      border-color: var(--gold-primary);
      font-weight: 700;
    }}

    /* --- Company Cards Grid --- */
    .company-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 22px;
    }}

    .company-card {{
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 24px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1);
      position: relative;
      overflow: hidden;
      box-shadow: var(--shadow-card);
    }}

    .company-card:hover {{
      transform: translateY(-5px);
      border-color: rgba(212, 175, 55, 0.4);
      box-shadow: 0 14px 35px -10px rgba(0, 0, 0, 0.6), var(--shadow-glow);
      background: var(--bg-card-hover);
    }}

    .card-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 14px;
    }}

    .card-title-group h3 {{
      font-family: 'Outfit', sans-serif;
      font-size: 21px;
      font-weight: 700;
      color: #fff;
      margin-bottom: 4px;
    }}

    .card-origin {{
      font-size: 12px;
      color: var(--text-dim);
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    /* Badges */
    .tier-badge {{
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: var(--radius-full);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .badge-ultra {{
      background: rgba(168, 85, 247, 0.15);
      color: #c084fc;
      border: 1px solid rgba(168, 85, 247, 0.3);
    }}
    .badge-rich {{
      background: rgba(212, 175, 55, 0.15);
      color: var(--gold-light);
      border: 1px solid rgba(212, 175, 55, 0.3);
    }}
    .badge-upper-mid {{
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }}
    .badge-mid {{
      background: rgba(0, 210, 255, 0.15);
      color: #38bdf8;
      border: 1px solid rgba(0, 210, 255, 0.3);
    }}
    .badge-budget {{
      background: rgba(244, 63, 94, 0.15);
      color: #fb7185;
      border: 1px solid rgba(244, 63, 94, 0.3);
    }}

    /* Card Highlights & Pricing metrics */
    .card-pricing-block {{
      background: rgba(0, 0, 0, 0.25);
      border-radius: var(--radius-sm);
      border: 1px solid rgba(255, 255, 255, 0.04);
      padding: 12px 14px;
      margin: 12px 0 16px;
    }}

    .pricing-stat-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      margin-bottom: 6px;
    }}
    .pricing-stat-row:last-child {{
      margin-bottom: 0;
    }}
    .pricing-stat-row .stat-label {{
      color: var(--text-dim);
    }}
    .pricing-stat-row .stat-val {{
      color: #fff;
      font-weight: 600;
    }}
    .pricing-stat-row .stat-val.gold {{
      color: var(--gold-light);
      font-weight: 700;
    }}

    .card-specs-list {{
      font-size: 12px;
      color: var(--text-muted);
      margin-bottom: 18px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .spec-item {{
      display: flex;
      align-items: flex-start;
      gap: 8px;
    }}
    .spec-dot {{
      width: 5px;
      height: 5px;
      border-radius: 50%;
      background: var(--gold-primary);
      margin-top: 6px;
      flex-shrink: 0;
    }}

    /* Card Action Buttons */
    .card-actions {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: auto;
    }}

    .btn-card {{
      background: var(--bg-input);
      border: 1px solid var(--border-subtle);
      color: var(--text-main);
      padding: 8px 12px;
      border-radius: var(--radius-sm);
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      text-align: center;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }}
    .btn-card:hover {{
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.2);
      color: #fff;
    }}
    .btn-card.primary {{
      background: linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(212, 175, 55, 0.08) 100%);
      border-color: var(--border-accent);
      color: var(--gold-light);
      grid-column: span 2;
    }}
    .btn-card.primary:hover {{
      background: var(--gold-primary);
      color: #000;
      border-color: var(--gold-primary);
      box-shadow: 0 0 15px var(--gold-glow);
    }}

    /* --- Interactive Modal / Drawer --- */
    .modal-backdrop {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.82);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      z-index: 999;
      justify-content: center;
      align-items: center;
      padding: 30px;
    }}
    .modal-backdrop.open {{
      display: flex;
    }}

    .modal-box {{
      background: var(--bg-surface);
      border: 1px solid var(--border-accent);
      border-radius: var(--radius-lg);
      width: 100%;
      max-width: 1080px;
      height: 90vh;
      max-height: 900px;
      display: flex;
      flex-direction: column;
      box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.8), var(--shadow-glow);
      overflow: hidden;
      animation: modalSlide 0.28s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    @keyframes modalSlide {{
      from {{ transform: scale(0.96); opacity: 0; }}
      to {{ transform: scale(1); opacity: 1; }}
    }}

    .modal-header {{
      padding: 22px 30px;
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(19, 26, 39, 0.6);
    }}

    .modal-header-left {{
      display: flex;
      align-items: center;
      gap: 16px;
    }}

    .modal-title-area h2 {{
      font-family: 'Outfit', sans-serif;
      font-size: 26px;
      font-weight: 700;
      color: #fff;
    }}
    .modal-title-area p {{
      font-size: 13px;
      color: var(--text-muted);
    }}

    .btn-close-modal {{
      background: var(--bg-input);
      border: 1px solid var(--border-subtle);
      width: 36px;
      height: 36px;
      border-radius: 50%;
      color: var(--text-muted);
      font-size: 18px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
    }}
    .btn-close-modal:hover {{
      background: #f43f5e;
      color: #fff;
      border-color: #f43f5e;
    }}

    .modal-tab-bar {{
      display: flex;
      border-bottom: 1px solid var(--border-subtle);
      background: #0b0f17;
      padding: 0 30px;
      overflow-x: auto;
    }}

    .modal-tab-btn {{
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--text-muted);
      padding: 14px 20px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.2s;
      white-space: nowrap;
    }}
    .modal-tab-btn:hover {{
      color: #fff;
    }}
    .modal-tab-btn.active {{
      color: var(--gold-light);
      border-bottom-color: var(--gold-primary);
    }}

    .modal-body-scroll {{
      flex: 1;
      overflow-y: auto;
      padding: 30px;
      background: var(--bg-surface);
    }}

    /* Markdown Formatted Elements in Modal & Reports */
    .dash-h1 {{
      font-family: 'Outfit', sans-serif;
      font-size: 24px;
      color: #fff;
      margin-bottom: 16px;
      font-weight: 700;
    }}
    .dash-h2 {{
      font-family: 'Outfit', sans-serif;
      font-size: 19px;
      color: var(--gold-light);
      margin: 24px 0 12px;
      font-weight: 600;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      padding-bottom: 6px;
    }}
    .dash-h3 {{
      font-size: 15px;
      color: #fff;
      margin: 18px 0 8px;
      font-weight: 600;
    }}
    .dash-p {{
      font-size: 14px;
      color: var(--text-muted);
      margin-bottom: 10px;
    }}
    .dash-li {{
      font-size: 13.5px;
      color: var(--text-muted);
      margin-left: 20px;
      margin-bottom: 5px;
    }}
    .dash-callout {{
      background: rgba(212, 175, 55, 0.08);
      border-left: 4px solid var(--gold-primary);
      padding: 14px 18px;
      border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
      font-size: 13.5px;
      color: #fce7b2;
      margin: 16px 0;
    }}
    .dash-hr {{
      border: none;
      height: 1px;
      background: var(--border-subtle);
      margin: 24px 0;
    }}
    .table-responsive {{
      overflow-x: auto;
      margin: 16px 0;
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-sm);
    }}
    .dash-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      text-align: left;
    }}
    .dash-table th {{
      background: #111724;
      padding: 12px 14px;
      color: var(--gold-light);
      font-weight: 600;
      border-bottom: 1px solid var(--border-subtle);
      white-space: nowrap;
    }}
    .dash-table td {{
      padding: 10px 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      color: var(--text-main);
    }}
    .dash-table tr:hover td {{
      background: rgba(255, 255, 255, 0.03);
    }}

    /* --- Interactive Master Table View --- */
    .table-view-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
      flex-wrap: wrap;
      gap: 12px;
    }}

    .btn-export {{
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.08) 100%);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #34d399;
      padding: 8px 16px;
      border-radius: var(--radius-sm);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .btn-export:hover {{
      background: #10b981;
      color: #000;
    }}

    .master-matrix-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12.5px;
    }}
    .master-matrix-table th {{
      background: #101624;
      color: var(--gold-light);
      padding: 12px 14px;
      text-align: left;
      border-bottom: 1px solid var(--border-accent);
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
    }}
    .master-matrix-table th:hover {{
      background: #172033;
    }}
    .master-matrix-table td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--border-subtle);
      white-space: nowrap;
    }}
    .master-matrix-table tr:hover td {{
      background: rgba(212, 175, 55, 0.05);
    }}

    /* --- Primary Research Script Copy Boxes --- */
    .script-box {{
      background: #0f1522;
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 20px;
      margin-bottom: 20px;
      position: relative;
    }}
    .btn-copy-script {{
      position: absolute;
      top: 14px;
      right: 14px;
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      padding: 5px 12px;
      border-radius: var(--radius-sm);
      font-size: 11px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }}
    .btn-copy-script:hover {{
      color: var(--gold-light);
      border-color: var(--gold-primary);
    }}

    /* Footer */
    footer {{
      border-top: 1px solid var(--border-subtle);
      padding: 24px 32px;
      text-align: center;
      font-size: 12px;
      color: var(--text-dim);
      background: var(--bg-surface);
    }}
  </style>
</head>
<body>

  <!-- Top Navigation Header -->
  <header class="top-navbar">
    <a href="#" class="nav-brand">
      <div class="brand-icon">K</div>
      <div class="brand-text">
        <h1>RunawayScout — Furniture Intel</h1>
        <p>Competitor Intelligence & Pricing Hub</p>
      </div>
    </a>

    <!-- Top Stats -->
    <div class="top-stats">
      <div class="stat-pill"><strong>25</strong> Brands</div>
      <div class="stat-pill"><strong>$4.8B</strong> Market</div>
      <div class="stat-pill"><strong>100%</strong> Audited Dossiers</div>
    </div>

    <!-- Navigation Tabs -->
    <nav class="nav-tabs">
      <button class="nav-tab-btn active" onclick="switchMainTab('explorer', this)">
        <span>🏢</span> Brands Explorer
      </button>
      <button class="nav-tab-btn" onclick="switchMainTab('matrix', this)">
        <span>📊</span> Master Price Matrix
      </button>
      <button class="nav-tab-btn" onclick="switchMainTab('strategy', this)">
        <span>📈</span> Strategic Analysis
      </button>
      <button class="nav-tab-btn" onclick="switchMainTab('mystery', this)">
        <span>🎯</span> Mystery Shopping Kit
      </button>
    </nav>
  </header>

  <!-- Main Container -->
  <main class="app-main">

    <!-- TAB 1: BRANDS EXPLORER -->
    <section id="tab-explorer" class="tab-content-panel active">
      
      <!-- Hero Banner -->
      <div class="hero-banner">
        <div class="hero-header">
          <div class="hero-title-area">
            <h2>Modular Kitchen & Furniture Intelligence Database</h2>
            <p>Comprehensive pricing books, price group ladders (PG 1–10), dealer margins, leaked quotations, material benchmarks, and official brochure links across 25 leading market players.</p>
          </div>
        </div>
      </div>

      <!-- Search & Filters -->
      <div class="controls-bar">
        <div class="search-box-wrap">
          <span style="color: var(--text-dim);">🔍</span>
          <input type="text" id="global-search" class="search-input" placeholder="Search by brand, country, hardware, material, price..." onkeyup="filterCards()">
        </div>

        <div class="filter-pills-row">
          <button class="filter-btn active" onclick="setCategoryFilter('all', this)">All (25)</button>
          <button class="filter-btn" onclick="setCategoryFilter('ultra', this)">👑 Ultra-Rich / UHNIs</button>
          <button class="filter-btn" onclick="setCategoryFilter('rich', this)">💎 Luxury Rich (HNIs)</button>
          <button class="filter-btn" onclick="setCategoryFilter('upper-mid', this)">✨ Upper Middle</button>
          <button class="filter-btn" onclick="setCategoryFilter('mid', this)">🏠 Middle Class</button>
          <button class="filter-btn" onclick="setCategoryFilter('budget', this)">🏷️ Budget</button>
        </div>
      </div>

      <!-- Companies Grid -->
      <div id="company-grid" class="company-grid">
        <!-- Rendered by JavaScript -->
      </div>
    </section>

    <!-- TAB 2: MASTER PRICING MATRIX -->
    <section id="tab-matrix" class="tab-content-panel">
      <div class="table-view-header">
        <div>
          <h2 class="dash-h1" style="margin-bottom: 4px;">Master Competitive Pricing Matrix</h2>
          <p class="dash-p">Standardized side-by-side pricing, per square foot finish costs, substrate materials, and warranty benchmarks.</p>
        </div>
        <button class="btn-export" onclick="exportCSV()">📥 Download Master CSV</button>
      </div>

      <div class="table-responsive" style="max-height: 75vh;">
        <table class="master-matrix-table" id="master-table">
          <thead>
            <tr>
              <th onclick="sortTable(0)">Brand ⬍</th>
              <th onclick="sortTable(1)">Origin ⬍</th>
              <th onclick="sortTable(2)">Customer Segment ⬍</th>
              <th onclick="sortTable(3)">Base Starting Price ⬍</th>
              <th onclick="sortTable(4)">Project Range ⬍</th>
              <th onclick="sortTable(5)">Laminate / Sq.Ft ⬍</th>
              <th onclick="sortTable(6)">Acrylic / Sq.Ft ⬍</th>
              <th onclick="sortTable(7)">PU Lacquer / Sq.Ft ⬍</th>
              <th onclick="sortTable(8)">Glass/Veneer / Sq.Ft ⬍</th>
              <th onclick="sortTable(9)">Carcass Substrate ⬍</th>
              <th onclick="sortTable(10)">Hardware Partner ⬍</th>
              <th onclick="sortTable(11)">Warranty ⬍</th>
              <th onclick="sortTable(12)">Lead Time ⬍</th>
            </tr>
          </thead>
          <tbody id="master-table-body">
            <!-- Populated by JS -->
          </tbody>
        </table>
      </div>
    </section>

    <!-- TAB 3: STRATEGIC ANALYSIS REPORT -->
    <section id="tab-strategy" class="tab-content-panel">
      <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 40px; box-shadow: var(--shadow-card);">
        {data["exec_summary_html"]}
      </div>
    </section>

    <!-- TAB 4: MYSTERY SHOPPING & PRIMARY RESEARCH -->
    <section id="tab-mystery" class="tab-content-panel">
      <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); padding: 40px; box-shadow: var(--shadow-card);">
        {data["personas_md_html"]}
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
        <button class="btn-close-modal" onclick="closeModal()">✕</button>
      </div>

      <!-- Modal Tab Bar -->
      <div class="modal-tab-bar">
        <button class="modal-tab-btn active" onclick="switchModalTab('pricing', this)">
          <span>💰</span> Pricing & Pricebook
        </button>
        <button class="modal-tab-btn" onclick="switchModalTab('profile', this)">
          <span>🏢</span> Company Profile & Specs
        </button>
        <button class="modal-tab-btn" onclick="switchModalTab('sources', this)">
          <span>🔍</span> Sources & Evidence
        </button>
        <button class="modal-tab-btn" onclick="switchModalTab('brochures', this)">
          <span>📥</span> Official Catalogues & Links
        </button>
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

  <!-- Embedded Data & Interactive Scripts -->
  <script>
    const COMPANIES = {companies_json};
    const CSV_ROWS = {csv_rows_json};

    let currentCategoryFilter = 'all';
    let currentActiveCompanyId = null;

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

    // Render Grid Cards
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

        // Filtering
        const catKey = getTierCategoryKey(targetSeg);
        if (currentCategoryFilter !== 'all' && catKey !== currentCategoryFilter) {{
          continue;
        }}

        // Search matching
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
                <div class="card-origin"><span>📍</span> ${{origin}}</div>
              </div>
              <span class="tier-badge ${{badgeClass}}">${{targetSeg.split('(')[0].trim()}}</span>
            </div>

            <div class="card-pricing-block">
              <div class="pricing-stat-row">
                <span class="stat-label">Starting Base Price:</span>
                <span class="stat-val gold">${{basePrice}}</span>
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
            <button class="btn-card primary" onclick="openModal('${{id}}', 'pricing')">
              <span>📊</span> Pricebook & Offerings
            </button>
            <button class="btn-card" onclick="openModal('${{id}}', 'profile')">
              <span>🏢</span> Profile
            </button>
            <button class="btn-card" onclick="openModal('${{id}}', 'brochures')">
              <span>📥</span> Brochures
            </button>
          </div>
        `;
        container.appendChild(card);
      }}

      if (container.children.length === 0) {{
        container.innerHTML = '<div style="grid-column: 1/-1; padding: 60px; text-align: center; color: var(--text-dim);">No companies match your search and filter criteria.</div>';
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

    // Switch Main Tabs
    function switchMainTab(tabId, btn) {{
      document.querySelectorAll('.nav-tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      document.querySelectorAll('.tab-content-panel').forEach(p => p.classList.remove('active'));
      document.getElementById('tab-' + tabId).classList.add('active');
    }}

    // Master Table Population
    function renderMasterTable() {{
      const tbody = document.getElementById('master-table-body');
      tbody.innerHTML = '';

      CSV_ROWS.forEach(r => {{
        const tr = document.createElement('tr');
        const baseFormatted = r.Base_Kitchen_Starting_Price_INR ? '₹' + Number(r.Base_Kitchen_Starting_Price_INR).toLocaleString('en-IN') : '-';
        tr.innerHTML = `
          <td><strong style="color: var(--gold-light); cursor:pointer;" onclick="openModalByName('${{r.Company_Name}}', 'pricing')">${{r.Company_Name}}</strong></td>
          <td>${{r.Country_of_Origin}}</td>
          <td><span class="tier-badge ${{getTierBadgeClass(r.Target_Customer_Segment)}}">${{r.Target_Customer_Segment}}</span></td>
          <td style="color: var(--gold-light); font-weight:700;">${{baseFormatted}}</td>
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

    // Modal Handling
    function openModal(id, defaultTab) {{
      currentActiveCompanyId = id;
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
      if (e.target.id === 'company-modal') {{
        closeModal();
      }}
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

    // Export CSV directly in browser
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

    // Table Sorting
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

        // Check if numeric or currency
        const numA = parseFloat(cellA.replace(/[^0-9.-]+/g, ""));
        const numB = parseFloat(cellB.replace(/[^0-9.-]+/g, ""));

        if (!isNaN(numA) && !isNaN(numB)) {{
          return isAsc ? numA - numB : numB - numA;
        }}
        return isAsc ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
      }});

      rows.forEach(r => tbody.appendChild(r));
    }}

    // Keyboard support for ESC to close modal
    document.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape') closeModal();
    }});

    // Initialize on load
    renderCards();
    renderMasterTable();
  </script>
</body>
</html>
"""
    return html

# Execute compile
data = load_all_data()
html_content = generate_html(data)

with open(HTML_OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Successfully created ultra-premium interactive dashboard at {HTML_OUT_PATH}")
print(f"File size: {os.path.getsize(HTML_OUT_PATH):,} bytes")
