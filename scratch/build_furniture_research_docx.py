import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    """Sets background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=180, right=180):
    """Sets cell padding in dxa (1 pt = 20 dxa)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_border(cell, **kwargs):
    """
    Set cell borders: top, bottom, left, right.
    kwargs: e.g. left={"sz": 24, "val": "single", "color": "0F2C59"}
    """
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f'w:{edge}'
            element = OxmlElement(tag)
            element.set(qn('w:val'), edge_data.get('val', 'single'))
            element.set(qn('w:sz'), str(edge_data.get('sz', 4)))
            element.set(qn('w:space'), '0')
            element.set(qn('w:color'), edge_data.get('color', 'auto'))
            tcBorders.append(element)
    tcPr.append(tcBorders)

def add_header_footer(doc):
    for s in doc.sections:
        s.different_first_page_header_footer = True
        
        # Header (Pages 2+)
        hdr = s.header
        hp = hdr.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("COMPETITIVE INTELLIGENCE DOSSIER | 8 ALLOTTED FURNITURE & MODULAR PLAYERS")
        hrun.font.name = "Calibri"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(0x70, 0x80, 0x90)
        
        # Footer (Pages 2+)
        ftr = s.footer
        fp = ftr.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("CONFIDENTIAL & PROPRIETARY — PREPARED FOR STRATEGIC BENCHMARKING | 2026")
        frun.font.name = "Calibri"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(0x88, 0x88, 0x88)

def format_bullet(doc, label, text, bullet_char="•"):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.28)
    p.paragraph_format.first_line_indent = Inches(-0.2)
    p.paragraph_format.space_before = Pt(2.5)
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing = 1.15
    
    r_sym = p.add_run(f"{bullet_char} ")
    r_sym.font.name = "Calibri"
    r_sym.font.bold = True
    r_sym.font.color.rgb = RGBColor(0x0F, 0x2C, 0x59)
    
    if label:
        r_lbl = p.add_run(label + (" — " if not label.endswith(":") else " "))
        r_lbl.font.name = "Calibri"
        r_lbl.font.bold = True
        r_lbl.font.size = Pt(10)
        r_lbl.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)
    
    r_txt = p.add_run(text)
    r_txt.font.name = "Calibri"
    r_txt.font.size = Pt(10)
    r_txt.font.color.rgb = RGBColor(0x28, 0x28, 0x28)

def add_callout(doc, text, title="STRATEGIC EXECUTIVE SUMMARY"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_background(cell, "F4F7FB")
    set_cell_margins(cell, top=140, bottom=140, left=200, right=180)
    set_cell_border(cell, left={"sz": 24, "val": "single", "color": "0F2C59"},
                          top={"sz": 4, "val": "single", "color": "D8E2EC"},
                          bottom={"sz": 4, "val": "single", "color": "D8E2EC"},
                          right={"sz": 4, "val": "single", "color": "D8E2EC"})
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    
    r_title = p.add_run(f"{title}: ")
    r_title.font.name = "Calibri"
    r_title.font.bold = True
    r_title.font.size = Pt(9.5)
    r_title.font.color.rgb = RGBColor(0x0F, 0x2C, 0x59)
    
    r_body = p.add_run(text)
    r_body.font.name = "Calibri"
    r_body.font.size = Pt(9.5)
    r_body.font.italic = True
    r_body.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

def add_section_h2(doc, title):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(12)
    h.paragraph_format.space_after = Pt(4)
    h.paragraph_format.keep_with_next = True
    run = h.add_run(title)
    run.font.name = "Calibri"
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x0F, 0x2C, 0x59)

def add_section_h3(doc, title):
    h = doc.add_paragraph()
    h.paragraph_format.space_before = Pt(8)
    h.paragraph_format.space_after = Pt(3)
    h.paragraph_format.keep_with_next = True
    run = h.add_run(title)
    run.font.name = "Calibri"
    run.font.size = Pt(10.5)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x31, 0x52, 0x7A)

def create_full_document():
    doc = docx.Document()
    
    # Page setup
    for s in doc.sections:
        s.top_margin = Inches(0.75)
        s.bottom_margin = Inches(0.75)
        s.left_margin = Inches(0.75)
        s.right_margin = Inches(0.75)
        s.page_width = Inches(8.5)
        s.page_height = Inches(11.0)
    
    add_header_footer(doc)
    
    # -------------------------------------------------------------
    # COVER / HEADER BLOCK
    # -------------------------------------------------------------
    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_before = Pt(0)
    p_meta.paragraph_format.space_after = Pt(4)
    r_meta = p_meta.add_run("STRATEGIC MARKET INTELLIGENCE REPORT | EXECUTIVE DOSSIER")
    r_meta.font.name = "Calibri"
    r_meta.font.size = Pt(9.5)
    r_meta.font.bold = True
    r_meta.font.color.rgb = RGBColor(0xC5, 0xA0, 0x59) # Gold Accent
    
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(2)
    p_title.paragraph_format.space_after = Pt(6)
    r_title = p_title.add_run("MODULAR KITCHEN & INTERIOR COMPETITIVE INTELLIGENCE")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(0x0F, 0x2C, 0x59)
    
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(14)
    r_sub = p_sub.add_run("Exhaustive Operational, Product Architecture, Pricing Benchmarks, Channel Footprint, and Promotion Analysis for 8 Key Allotted Players: Sleek (India), HomeLane (India), Spacewood (India), Panasonic (Japan/India), Casantro (India), Itallica (India), Pedini (Italy), and Linhoff (India).")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(11)
    r_sub.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    
    # Metadata callout
    meta_box = doc.add_table(rows=1, cols=4)
    meta_box.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_box.autofit = False
    col_widths = [Inches(1.8), Inches(1.8), Inches(1.7), Inches(1.7)]
    for i, w in enumerate(col_widths):
        meta_box.columns[i].width = w
    
    meta_headers = [
        ("TARGET COHORT", "8 Allotted Brands"),
        ("RESEARCH METHOD", "Primary & Secondary Audit"),
        ("MARKET SEGMENTS", "Mass, Mid, Luxury, Import"),
        ("REPORT STATUS", "Complete Intelligence Audit")
    ]
    for i, (k, v) in enumerate(meta_headers):
        cell = meta_box.cell(0, i)
        set_cell_background(cell, "EAF0F6")
        set_cell_margins(cell, 80, 80, 100, 100)
        set_cell_border(cell, top={"sz": 4, "val": "single", "color": "B0C4DE"},
                              bottom={"sz": 4, "val": "single", "color": "B0C4DE"},
                              left={"sz": 4, "val": "single", "color": "B0C4DE"},
                              right={"sz": 4, "val": "single", "color": "B0C4DE"})
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r1 = p.add_run(f"{k}\n")
        r1.font.size = Pt(7.5)
        r1.font.bold = True
        r1.font.color.rgb = RGBColor(0x70, 0x80, 0x90)
        r2 = p.add_run(v)
        r2.font.size = Pt(9.5)
        r2.font.bold = True
        r2.font.color.rgb = RGBColor(0x0F, 0x2C, 0x59)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(10)
    
    # -------------------------------------------------------------
    # EXECUTIVE BENCHMARK MATRIX TABLE
    # -------------------------------------------------------------
    p_tbl_title = doc.add_paragraph()
    p_tbl_title.paragraph_format.space_before = Pt(8)
    p_tbl_title.paragraph_format.space_after = Pt(4)
    r_tt = p_tbl_title.add_run("EXECUTIVE COMPARATIVE BENCHMARK: 8 ALLOTTED COMPETITORS")
    r_tt.font.name = "Calibri"
    r_tt.font.size = Pt(12)
    r_tt.font.bold = True
    r_tt.font.color.rgb = RGBColor(0x0F, 0x2C, 0x59)
    
    table_data = [
        ["Company & Origin", "Ownership", "Est. Revenue", "Stores / Reach", "Core Substrates", "Hardware", "Entry / Mid Price", "Lead Time", "Primary Moat"],
        ["Sleek (Asian Paints)\nIndia", "100% Sub. Asian Paints", "₹250 - ₹350+ Cr", "300+ Studios; 500+ Touchpoints", "IS 710 BWP Ply, HDHMR", "Grass (Austria), Sleek, Blum", "₹1.4L - ₹1.8L (Entry)\n₹2.5L - ₹5.5L (Mid)", "30–45 Days", "Asian Paints Dealer Network & Brand Trust"],
        ["HomeLane\nIndia", "PE/VC Funded (Peak XV, Hero)", "₹756 Cr (FY25 Cons.)", "84+ Experience Centres", "IS 710 BWP, HDHMR, E1 Board", "Hettich (Atira), Hafele, Ebco", "₹1.2L - ₹1.9L (Entry)\n₹2.8L - ₹5.5L (Mid)", "45 Days (Guaranteed)", "SpaceCraft 3D CAD & 45-Day Rent Penalty Guarantee"],
        ["Spacewood\nIndia", "Sumitomo Forestry (26%), A91", "₹450 - ₹550+ Cr", "35+ Studios; 500+ Dealers", "Supertuff HDF, E1 MFC, BWP", "Hettich, Ebco, Spacewood OEM", "₹1.1L - ₹1.5L (Entry)\n₹2.0L - ₹4.5L (Mid)", "25–35 Days", "25-Acre Automated Mega-Plant & Low Per-Unit Cost"],
        ["Panasonic (Homes)\nJapan / India", "100% Sub. Panasonic Japan", "₹35 - ₹60 Cr (Historical)", "Service Only (Retail Sunsetting)", "SS Sink Base, Marine Ply", "Panasonic Soft-Down, Blum", "₹2.5L (I-Class)\n₹6.0L - ₹15L (L-Class)", "45–75 Days", "Japanese Ergonomics, F**** Zero-Formaldehyde, SS Base"],
        ["Casantro\nIndia", "Privately Held Boutique", "₹25 - ₹45 Cr", "6+ Luxury Experience Centres", "Birch Ply, BWP Marine, HDHMR", "100% Blum (Legrabox), Hafele", "₹3.5L - ₹5.0L (Entry)\n₹8.0L - ₹22L (Luxury)", "45–60 Days", "Architect-Centric Fluted Glass & Bespoke Japandi Styling"],
        ["Itallica / Italica\nIndia", "Proprietor / Regional MSME", "₹10 - ₹20 Cr", "TradeIndia / IndiaMART Network", "Commercial MR/BWR Ply, MDF", "Ebco, Generic Soft-Close", "₹85k - ₹1.2L (Entry)\n₹1.8L - ₹3.5L (Mid)", "15–25 Days", "Direct-from-Workshop Pricing & Extreme Cost Advantage"],
        ["Pedini\nItaly", "Pedini S.p.A. (Demiray/Radifin)", "€30M-€50M Glob. (₹20Cr Ind)", "Exclusive Importers (Delhi, Pune)", "Curved Eco-Panel, Solid Alum", "Custom Blum Legrabox, Salice", "₹15L - ₹20L (Entry)\n₹35L - ₹1.5Cr (Ultra-Lux)", "14–18 Weeks", "World Pioneer in Curved Modular Kitchens (Dune/Artika)"],
        ["Linhoff\nIndia", "Unit of Feller Design Interiors", "₹8 - ₹18 Cr", "Gomti Nagar Flagship, Lucknow", "100% Calibrated BWP Ply, HDHMR", "Blum, Hettich, Ebco Soft-close", "₹1.0L - ₹1.4L (Entry)\n₹2.2L - ₹4.8L (Mid)", "25–35 Days", "Localized German CNC Manufacturing & In-house SLA"]
    ]
    
    matrix_tbl = doc.add_table(rows=len(table_data), cols=9)
    matrix_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    matrix_tbl.autofit = False
    
    widths = [Inches(0.9), Inches(0.85), Inches(0.8), Inches(0.95), Inches(0.95), Inches(0.85), Inches(0.9), Inches(0.7), Inches(1.0)]
    for r_idx, row in enumerate(table_data):
        for c_idx, val in enumerate(row):
            cell = matrix_tbl.cell(r_idx, c_idx)
            cell.width = widths[c_idx]
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.05
            
            if r_idx == 0:
                set_cell_background(cell, "0F2C59")
                set_cell_margins(cell, 80, 80, 60, 60)
                set_cell_border(cell, top={"sz": 4, "val": "single", "color": "0F2C59"},
                                      bottom={"sz": 12, "val": "single", "color": "C5A059"})
                r = p.add_run(val)
                r.font.name = "Calibri"
                r.font.size = Pt(7.5)
                r.font.bold = True
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            else:
                bg = "F9FBFC" if r_idx % 2 == 1 else "FFFFFF"
                set_cell_background(cell, bg)
                set_cell_margins(cell, 60, 60, 50, 50)
                set_cell_border(cell, bottom={"sz": 4, "val": "single", "color": "E0E6ED"},
                                      left={"sz": 2, "val": "single", "color": "E0E6ED"},
                                      right={"sz": 2, "val": "single", "color": "E0E6ED"})
                r = p.add_run(val)
                r.font.name = "Calibri"
                r.font.size = Pt(7.2)
                r.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
                if c_idx == 0:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(0x0F, 0x2C, 0x59)

    doc.add_page_break()
    
    # -------------------------------------------------------------
    # COMPANY DOSSIERS (1 to 8)
    # -------------------------------------------------------------
    
    companies = [
        {
            "num": "1",
            "name": "SLEEK BY ASIAN PAINTS — INDIA",
            "category": "Tier 2: National Corporate Heavyweight (Paint Conglomerate Backed)",
            "summary": "Sleek is India's largest retail network player in branded modular kitchens, backed by the multi-billion-dollar balance sheet and 500+ touchpoint distribution of Asian Paints. It bridges middle-class affordability with corporate warranty assurance, competing directly on brand trust and nationwide contractor relationships.",
            "snapshot": [
                ("Ownership", "100% subsidiary of Asian Paints Limited (BSE: 500820). Acquired 51% controlling stake in Sleek International in 2013 and consolidated to 100% ownership by 2017."),
                ("Country of Origin & India Entry Year", "India. Founded in 1993 in Mumbai by the Ahuja family as a wire accessory and modular kitchen manufacturer; integrated into Asian Paints' corporate fold in 2013."),
                ("Estimated Revenue", "India operations revenue estimated at ₹250 – ₹350+ Crore annually. Forms the core of Asian Paints' Home Improvement business segment (which generated over ₹780 Cr in FY24 across kitchens and bath fittings)."),
                ("Manufacturing Footprint", "Automated 200,000+ sq. ft. central manufacturing and fabrication plant located in Talegaon / Taloja (Maharashtra), supported by regional warehousing and Asian Paints' national supply chain network."),
                ("Certifications Held", "ISO 9001:2015 (Quality Management), ISO 14001 (Environmental Systems), IS 710 calibrated marine plywood compliance, and European E1 emission standard compliance for low VOC emission boards."),
                ("One-Line Positioning", "'Modern Kitchens for Modern Minds' / 'The Kitchen Specialist from Asian Paints' — offering end-to-end factory-finished modularity backed by 10-year warranty trust.")
            ],
            "product_portfolio": [
                ("Categories Covered", "Full-line modular kitchens, modular wardrobes and walk-in closets, kitchen built-in appliances (hobs, chimneys, built-in ovens, microwaves, dishwashers), kitchen accessories (wire baskets, larder units, corner pullouts, carousel units), and sinks/faucets."),
                ("Depth per Category", "120+ shutter finish and color combinations, 15+ shutter profile styles (including handleless Gola profiles, J-pull, integrated aluminum channels, beveled slab, and shaker profiles), and over 250+ appliance and storage SKUs."),
                ("Hero Collections & Marketing", "Flagship 'Inspire' and 'Transform' collections marketed on design sophistication (anti-fingerprint matte acrylic, ceramic and metallic finishes). Entry collections ('Smart Series') marketed heavily on cost-predictability and speed."),
                ("Core Material Used by Price Tier", "Base/Budget: Moisture-Resistant HDHMR (High-Density High-Moisture Resistance) boards; Mid-to-High: IS 710 Certified Boiling Water Proof (BWP) Marine Plywood with calibrated core; Wet Zones: Dedicated 100% waterproof marine ply sink carcasses."),
                ("Finish Options Offered", "0.8mm – 1.0mm Decorative Laminates (matte, high-gloss, textured, suede), High-Gloss & Anti-Fingerprint Acrylics, Factory-Cured Polyurethane (PU) Painted Lacquer, Sintered Ceramic-coated fronts, and Toughened/Fluted Lacquered Glass in aluminum frames."),
                ("Hardware Brand Used", "Exclusive strategic hardware partnership with Grass (Austria) for soft-close concealed hinges and Tiomos drawer runners; select Blum hardware on premium lines; Sleek Aerolift flap fittings and certified in-house tested runners."),
                ("Warranty Period & Coverage", "10-Year Warranty on factory-processed marine plywood cabinetry structure against borer, termite, and delamination; 5-Year warranty on Grass and Sleek drawer runners and hinges; 1–2 Year warranty on chimneys, hobs, and electrical components.")
            ],
            "customization": [
                ("Level of Customization", "Semi-bespoke to highly customizable modular system. Built on standardized 50mm and 100mm dimensional increments with bespoke infill panels and custom corner fillers tailored to civil site tolerances."),
                ("Production Model", "100% Made-to-order. Production commences exclusively upon signed customer 2D/3D drawings and laser site measurement verification."),
                ("Lead Times", "Standard Laminate/Acrylic order: 30 to 35 calendar days; Custom PU paint, ceramic, or glass shutter order: 40 to 50 calendar days from drawing freeze.")
            ],
            "supply_chain": [
                ("In-House vs Outsourced vs Imported", "85%+ in-house domestic manufacturing at Maharashtra plant. Precision hardware and specialized motion mechanisms are imported from Grass (Austria) and Kesseböhmer (Germany); built-in appliances are OEM-manufactured under the Sleek brand."),
                ("Import Impact", "Imported hardware components carry a 10–15% tariff burden, but high purchasing scale under Asian Paints buffers against retail price shocks and lead-time delays."),
                ("BIS Compliance Status", "Fully compliant. Plywood substrates adhere strictly to IS 710, particleboards to IS 3087, and appliances carry mandatory BIS and BEE certifications.")
            ],
            "pricing_structure": [
                ("Pricing Unit Used", "Hybrid pricing: Per square foot rate card (₹1,500 – ₹3,500/sq.ft. for basic to premium cabinetry) converted into an itemized Bill of Quantities (BOQ) with transparent modular line items."),
                ("Entry-Level Price Point", "₹1,40,000 – ₹1,80,000 for a compact straight-line or L-shaped 8x6 ft modular kitchen with laminate finish and essential wire baskets."),
                ("Mid-Range and Premium Price Ceiling", "Mid-range setups range from ₹2,50,000 – ₹5,50,000; premium configurations with anti-fingerprint acrylic, PU paint, quartz countertops, and built-in appliances reach ₹8,00,000 – ₹14,00,000+."),
                ("Average Order Ticket Size", "₹3,20,000 – ₹5,00,000 for complete modular kitchen installations."),
                ("Pricing Model", "Transparent quote-based model generated via proprietary dealer design software. Transparent quotation structure breaks industry opacity, though local studio dealers have 10%–18% discounting headroom during promotional campaigns."),
                ("EMI / Financing Options", "Comprehensive 0% EMI financing offered through partnerships with Bajaj Finserv, HDFC Bank, and Asian Paints' proprietary Home Improvement financing schemes.")
            ],
            "pricing_strategy": [
                ("Perceived Value Positioning", "Mid-Premium. Positioned as a dependable, aspirational corporate brand accessible to the middle and upper-middle classes."),
                ("Festive Pricing Behaviour", "Aggressive festive campaigns (Diwali, New Year, Gudi Padwa) offering bundled chimney/hob upgrades, free quartz countertops, or 15% cashback paint vouchers redeemable across Asian Paints retail."),
                ("Price Comparison vs Unorganized Carpenters", "Sleek prices sit 25% – 35% above raw carpenter-contractor quotes. Sleek justifies this delta through factory edge-banding (PUR technology), 10-year warranty, zero termite risk, and structured project management."),
                ("Price vs Design/Value Verdict", "COMPETING ON DESIGN & VALUE. Evidence: Sleek does not attempt to undercut local carpentered kitchens on price; instead, it anchors its sales pitch on Asian Paints brand trust, Grass Austrian hardware reliability, and certified IS 710 marine plywood durability.")
            ],
            "physical_presence": [
                ("Total Number of Stores", "Over 300+ exclusive Sleek Kitchen Studios, supplemented by displays in 150+ 'Asian Paints Beautiful Homes' flagship super-stores. Total footprint exceeds 500 touchpoints across India."),
                ("Cities & Tier Penetration", "Present in 120+ cities. Deep penetration across Tier 1 (Mumbai, Delhi-NCR, Bengaluru, Pune, Kolkata, Chennai, Hyderabad) and Tier 2 (Ahmedabad, Surat, Lucknow, Jaipur, Kochi, Chandigarh, Indore, Coimbatore, Nagpur); expanding rapidly into Tier 3 industrial hubs."),
                ("Ownership Split", "Approximately 90% franchise/dealer-operated studios and 10% company-owned flagship experience centres in key metros.")
            ],
            "online_presence": [
                ("Website Type", "Inquiry and lead-generation portal (sleekworld.com and beautifulhomes.asianpaints.com). No direct e-commerce self-checkout (custom measurement required)."),
                ("3D/AR Visualizer & Configurator", "Features 3D showroom walkthroughs and gallery inspiration. Store designers use proprietary internal CAD-based design software to build customer BOQs in real time; lacks a public self-service online 3D kitchen configurator."),
                ("Online vs Offline Catalogue Depth", "Online catalogue displays ~60% of collections to generate qualified leads; exclusive luxury finishes, tactile shutter samples, and motorized hardware are reserved for physical studio visits."),
                ("Website Feature-Mining for Client", "1) Live dealer locator with one-click WhatsApp appointment scheduling; 2) Asian Paints color-palette visualizer pairing kitchen shutters with wall shades; 3) Appliance bundle discount calculator.")
            ],
            "channel_expansion": [
                ("Expansion Pace", "Added 30 to 45 new studios annually over the past 3 years by leveraging Asian Paints' vast paint dealer network."),
                ("Future Targets", "Targeting 600+ dedicated kitchen and wardrobe studios by 2027, focusing on Tier 2/3 home renovation booms."),
                ("Franchise Model Terms", "Requires 800 – 1,500 sq. ft. prime retail space, capital investment of ₹25 – ₹40 Lakh (showroom setup + sample displays), with gross dealer margins of 28% – 32% on MRP."),
                ("Geographic White Spaces", "Under-represented in deep North-Eastern states (Mizoram, Nagaland) and remote Himalayan border towns.")
            ],
            "brand_promotion": [
                ("Core Brand Promise & Tagline", "'The Kitchen Specialist' / 'Modern Kitchens for Modern Minds' — engineered for Indian cooking styles with international hardware."),
                ("Target Persona", "Middle to Upper-Middle class nuclear families, dual-income homeowners, and apartment renovators (home values: ₹60L – ₹2.5 Cr)."),
                ("Key Differentiators", "End-to-end brand accountability (appliances, cabinets, hardware under one Asian Paints umbrella), 10-year warranty, anti-termite marine ply."),
                ("Digital Marketing", "Instagram: @sleekkitchens / @beautifulhomes.ap (500K+ followers on parent network, high aesthetic reel engagement); YouTube: Comprehensive library of homeowner video testimonials, kitchen maintenance tips, and modular hardware demonstrations."),
                ("Offline Marketing", "Heavy television commercials (TVC) during festive and cricketing events, full-page print ads in Architectural Digest India, Femina, and regional dailies, highway billboards, and builder sample-flat displays."),
                ("Partnerships & Channels", "Direct B2B supply agreements with major real estate developers (Lodha, Runwal, Godrej Properties) for pre-fitted modular kitchens; formal Asian Paints Interior Designer referral program (8%–12% trade commission)."),
                ("Customer Retention & Complaints", "Automated CRM warranty registration; 1-year complimentary service check-up. Google reviews praise build finish and aesthetics, but common customer complaints highlight dealer-level installation delays (exceeding promised 35 days) and erratic post-sales service coordination at franchise levels.")
            ],
            "service": [
                ("Lead Time Order to Installation", "30 to 45 calendar days from final drawing sign-off to site completion."),
                ("Installation Team", "Handled by franchise-trained modular carpenters and Asian Paints certified installation crews equipped with dustless cutting and laser leveling tools."),
                ("Order Tracking System", "Milestone tracking managed through Asian Paints' central ERP system; updates sent to customers via SMS/WhatsApp alerts upon factory production, dispatch, and delivery."),
                ("After-Sales Service Structure", "Centralized national customer helpline (1800-2120-500), dedicated service ticketing portal, local franchise service technicians, and formal warranty card fulfillment.")
            ]
        },
        {
            "num": "2",
            "name": "HOMELANE — INDIA",
            "category": "Tier 2: Tech-First Venture-Backed Challenger (Omnichannel Unicorn)",
            "summary": "HomeLane is India's leading technology-first home interior brand, celebrated for its algorithmic 3D co-design tool (SpaceCraft) and industry-defining 45-day delivery guarantee. Post its September 2024 acquisition of DesignCafe (funded by Hero Enterprise), HomeLane operates at an annual revenue run-rate exceeding ₹750 Cr across 84+ experience centres.",
            "snapshot": [
                ("Ownership", "Venture-capital and PE-backed tech company (HomeLane Dwellings Pvt. Ltd.). Major institutional investors include Peak XV Partners (formerly Sequoia India), Accel, Evolvence India, and Hero Enterprise (led ₹225 Cr round in Sept 2024 to acquire DesignCafe)."),
                ("Country of Origin & India Entry Year", "India. Founded in 2014 in Bengaluru by Srikanth Iyer and Rama Harinath."),
                ("Estimated Revenue", "Consolidated FY25 revenue reported at ₹756 Crore (growing 22% YoY, combining HomeLane and DesignCafe operations). Standalone FY24 revenue was approximately ₹614 – ₹668 Crore."),
                ("Manufacturing Footprint", "Asset-light hybrid manufacturing model: Operates centralized panel processing hubs in Bengaluru and Bhiwandi (Mumbai) utilizing German Homag and Italian Biesse CNC machinery, complemented by a certified network of standardized regional OEM manufacturing partners."),
                ("Certifications Held", "ISO 9001:2015, CARB Phase 2 certified particleboards, IS 710 calibrated marine plywood, and strict low-VOC emission compliance."),
                ("One-Line Positioning", "'Interiors Made Easy' — promising transparent instant pricing, algorithmic 3D visualization, and a strict 45-day delivery guarantee or HomeLane pays your rent.")
            ],
            "product_portfolio": [
                ("Categories Covered", "Full home interiors: Modular kitchens, modular wardrobes (sliding, hinged, walk-in), TV entertainment consoles, pooja units, shoe storage, vanity cabinets, study units, loose furniture, false ceiling, painting, and lighting."),
                ("Depth per Category", "1,000+ modular cabinet variations, 50+ laminate and acrylic finish colors, 30+ specialty storage hardware accessories, and full integration with curated loose furniture collections."),
                ("Hero Collections & Marketing", "'Trident', 'Luxe', and 'Essential' modular series, marketed aggressively on price predictability, sleek modern aesthetics, and guaranteed delivery timelines."),
                ("Core Material Used by Price Tier", "Base: Pre-laminated engineered particleboard (CARB P2); Mid: High-Density High-Moisture Resistance (HDHMR) boards; Wet/Premium: 100% Calibrated IS 710 Boiling Water Resistant (BWR/BWP) Marine Plywood."),
                ("Finish Options Offered", "Anti-scratch Matte & Suede Laminates, High-Gloss Acrylics, Anti-Fingerprint Super-Matte surfaces, Factory PU Paint, and Fluted Glass with sleek black/gold aluminum profiles."),
                ("Hardware Brand Used", "Hettich (Germany) InnoTech Atira and Sensys soft-close systems, Ebco, and Häfele concealed hinges and drawer channels."),
                ("Warranty Period & Coverage", "Flat 10-Year Warranty on factory-finished woodwork and carcass structures against manufacturing defects; 5-Year warranty on Hettich and Ebco hardware fittings.")
            ],
            "customization": [
                ("Level of Customization", "Modular grid customization with algorithmic cut-list optimization. Provides millimetric adjustments using custom fillers and CNC-cut end panels."),
                ("Production Model", "100% Made-to-order. Customer-approved 3D models from SpaceCraft generate automated machine code directly sent to factory CNC panel saws."),
                ("Lead Times", "Guaranteed 45-day delivery and installation timeline from the date of design freeze and initial payment.")
            ],
            "supply_chain": [
                ("In-House vs Outsourced vs Imported", "Hybrid model combining centralized company manufacturing plants in Bengaluru and Bhiwandi with audited OEM manufacturing partners. Hardware is imported from Germany/Europe via official distributor channels."),
                ("Import Impact", "Hardware tariffs affect component costs, but standardized volume bundling with Hettich ensures predictable landed unit economics."),
                ("BIS Compliance Status", "Fully compliant with IS 710 (plywood), IS 3087 (wood particleboards), and DPIIT Quality Control Orders.")
            ],
            "pricing_structure": [
                ("Pricing Unit Used", "Modular per-unit pricing dynamically computed via SpaceCraft CAD software; converts to an itemized linear foot and square foot estimate (₹1,350 – ₹3,200/sq.ft. for cabinetry)."),
                ("Entry-Level Price Point", "₹1,20,000 – ₹1,90,000 for a compact 2BHK straight/L-shaped modular kitchen package."),
                ("Mid-Range and Premium Price Ceiling", "Complete modular kitchens range from ₹2,80,000 – ₹5,50,000; full-home 2BHK/3BHK interior packages range between ₹4,50,000 and ₹12,00,000+."),
                ("Average Order Ticket Size", "₹3,50,000 – ₹4,50,000 for standalone kitchens; ₹7,00,000 – ₹9,50,000 for comprehensive home interiors."),
                ("Pricing Model", "Transparent instant fixed quotation generated in 3D in front of the customer. Completely eliminates hidden carpenter markups. Moderate promotional discounting (8%–15% seasonal discounts)."),
                ("EMI / Financing Options", "Extensive zero-cost EMI tie-ups with Bajaj Finserv, Fibe (EarlySalary), Tata Capital, and major credit card partners.")
            ],
            "pricing_strategy": [
                ("Perceived Value Positioning", "Mass-Market to Mid-Premium. Geared towards young first-time homebuyers seeking certainty, professional design, and fixed budgets."),
                ("Festive Pricing Behaviour", "Frequent high-decibel discount sales ('No-Rent Days', festive cashback, free appliance upgrades like Bosch chimneys, festive gold coins)."),
                ("Price Comparison vs Unorganized Carpenters", "Priced roughly 15% – 25% higher than unorganized carpenters, but directly competes by highlighting hidden carpenter overruns, lack of warranties, and infinite timeline delays."),
                ("Price vs Design/Value Verdict", "COMPETING ON PREDICTABLE VALUE & TIME CERTAINTY. Evidence: HomeLane leads its entire brand pitch with its contractual '45-Day Delivery or We Pay Your Rent' guarantee and transparent live 3D pricing, eliminating the ambiguity inherent in carpenter quotes.")
            ],
            "physical_presence": [
                ("Total Number of Stores", "84+ Experience Centres and design studios across India as of 2026, actively scaling with 100 new franchise-led studios following the DesignCafe acquisition."),
                ("Cities & Tier Penetration", "Present in 22+ major cities. Heavy Tier 1 concentration (Bengaluru, Mumbai, Delhi-NCR, Hyderabad, Chennai, Kolkata, Pune) and expanding into Tier 2 (Ahmedabad, Surat, Jaipur, Lucknow, Kochi, Mysore, Coimbatore, Vizag)."),
                ("Ownership Split", "Transitioning towards a franchise-led model: ~40% company-owned flagship experience centres and 60% franchise-owned franchise-operated (FOFO) studios.")
            ],
            "online_presence": [
                ("Website Type", "Industry-leading digital D2C portal (homelane.com) optimized for design exploration, cost calculation, and consultation booking."),
                ("3D/AR Visualizer & Configurator", "EXCELLENT. Features 'SpaceCraft', a proprietary cloud-based real-time 3D co-design tool allowing designers and clients to customize floor plans, change materials, and view live BOQ price changes instantly."),
                ("Online vs Offline Catalogue Depth", "High online catalogue transparency displaying 1,000+ designs, real customer project photos, and transparent pricing calculators; physical centres used to experience tactile finishes and mechanism ergonomics."),
                ("Website Feature-Mining for Client", "1) Live 'Instant Kitchen Cost Calculator' based on room shape and finish tier; 2) Real-time designer calendar booking with instant video consultation option; 3) 3D Virtual Home Walkthroughs with interactive material toggles.")
            ],
            "channel_expansion": [
                ("Expansion Pace", "Rapid expansion, opening 20–30 studios annually over the past 3 years; accelerated by acquiring DesignCafe's retail assets."),
                ("Future Targets", "Targeting 150+ operational experience centres and expanding deeper into Tier 2 and Tier 3 cities across Central and Eastern India."),
                ("Franchise Model Terms", "Franchise partner requires ₹30 – ₹50 Lakh capex (1,000–2,000 sq.ft. showroom), offering expected operating profit margins of 12% – 15% and payback within 18–24 months."),
                ("Geographic White Spaces", "Non-metro Tier 3/4 towns, interior Jammu & Kashmir, and remote North-Eastern states.")
            ],
            "brand_promotion": [
                ("Core Brand Promise & Tagline", "'Interiors Made Easy' / '45-Day Delivery Guarantee or We Pay Your Rent'."),
                ("Target Persona", "First-time millennial homebuyers, IT professionals, young families purchasing 2BHK/3BHK apartments (home value: ₹45L – ₹1.5 Cr)."),
                ("Key Differentiators", "Strict 45-day delivery SLA with rent compensation clause, SpaceCraft 3D real-time pricing, 10-year warranty, dedicated project managers."),
                ("Digital Marketing", "Instagram: @homelane_india (250K+ followers, high-frequency reels, before-after renovation videos); YouTube: @Homelaneinteriors (76.2K subs) and @InteriorsMadeEasy (108K subs) featuring apartment room tours, material explainer guides, and customer reviews. Dominates Google Search SEO for 'modular kitchen price Bangalore / Mumbai / Delhi'."),
                ("Offline Marketing", "Celebrity endorsements (MS Dhoni as equity partner and brand ambassador), metro station and train wrap branding, high-visibility residential society activations, and radio campaigns."),
                ("Partnerships & Channels", "Direct corporate alliances with top developers (Prestige, Brigade, Sobha, Godrej) providing display units in sample apartments; 'HomeLane Partner Network' for freelance architects and interior designers."),
                ("Customer Retention & Complaints", "Active CRM re-engagement, scheduled 6-month and 12-month post-installation maintenance check-ups. Customer sentiment on Google/Trustpilot averages 4.2–4.5 stars; recurring complaint themes focus on punch-list snag resolution delays and occasional third-party countertop installation quality issues.")
            ],
            "service": [
                ("Lead Time Order to Installation", "Strictly guaranteed 45 calendar days from design freeze to final handover."),
                ("Installation Team", "Handled by dedicated, in-house trained HomeLane installation technicians under the supervision of a dedicated on-site Project Manager."),
                ("Order Tracking System", "Proprietary HomeLane Customer App offering end-to-end transparent order tracking through 5 key stages: Design, Manufacturing, Quality Check, Delivery, and Installation."),
                ("After-Sales Service Structure", "Centralized customer support desk (1800-102-4663), app-based service ticket logging, guaranteed 72-hour technician visit for warranty claims, and dedicated customer success managers.")
            ]
        },
        {
            "num": "3",
            "name": "SPACEWOOD — INDIA",
            "category": "Tier 2: High-Volume Industrial Giant (Japanese Strategic Equity Backed)",
            "summary": "Spacewood is India's largest volume manufacturer of modular furniture, operating out of a sprawling 25-acre automated campus in Nagpur. Backed by a 26% equity stake from Japan's Sumitomo Forestry and a ₹300 Cr late-2025 growth round from A91 Partners, Spacewood delivers European-grade factory engineering at highly aggressive Indian price points.",
            "snapshot": [
                ("Ownership", "Privately held enterprise (Spacewood Furnishers Pvt. Ltd.). Japanese timber and housing conglomerate Sumitomo Forestry Co. Ltd. holds a 26% strategic equity stake (since 2015). In late 2025, raised ₹300 Crore from A91 Partners to accelerate retail expansion."),
                ("Country of Origin & India Entry Year", "India. Founded in 1996 in Nagpur, Maharashtra by Kirit Joshi and Vivek Deshpande."),
                ("Estimated Revenue", "India operations revenue estimated at ₹450 – ₹550+ Crore annually across retail franchise stores, direct builder project contracts, and e-commerce OEM manufacturing."),
                ("Manufacturing Footprint", "India's largest single-location modular furniture production plant: 25-acre integrated campus in MIDC Hingna, Nagpur (Maharashtra), featuring fully automated German Homag and Wemhoner panel processing, membrane pressing, and CNC lines."),
                ("Certifications Held", "ISO 9001:2015, ISO 14001, OHSAS 18001, FSC (Forest Stewardship Council) certified chain of custody, IGBC Green Building certification, and E1 European emission standards."),
                ("One-Line Positioning", "'Smart Furniture for Modern Living' / 'German Precision & Japanese Engineering at Indian Value' — democratizing factory-finished modular furniture.")
            ],
            "product_portfolio": [
                ("Categories Covered", "Modular kitchens, modular wardrobes, complete bedroom suites, living room storage/entertainment units, home office furniture, and pre-hung engineered wooden doors (joint venture with Sumitomo Forestry Crest)."),
                ("Depth per Category", "350+ modular SKUs, 60+ shutter finish shades, 8 modular kitchen layout configurations, and specialized storage accessories."),
                ("Hero Collections & Marketing", "'Supertuff HDF' modular kitchen collection (marketed on exceptional water and termite resistance), 'Touch' handleless collection, and 'Nippon Engineered Doors'."),
                ("Core Material Used by Price Tier", "Base: Pre-laminated European standard E1 grade Particle Board / MFC; Mid: Supertuff High-Density High-Moisture Resistance (HDHMR); Premium: Calibrated Boiling Water Resistant (BWR) and Marine Plywood."),
                ("Finish Options Offered", "Melamine Faced Boards (MFC), High-Pressure Decorative Laminates (HPL), PVC Membrane Pressed Foils, Seamless High-Gloss Acrylic, and PU Lacquer coating."),
                ("Hardware Brand Used", "Strategic hardware partnership with Hettich (Germany) for soft-close hinges and drawer runners; Ebco and Spacewood OEM-certified heavy-duty hardware."),
                ("Warranty Period & Coverage", "10-Year Warranty on Supertuff HDF cabinetry against termites and moisture damage; 5-Year warranty on particle board cabinetry; 3–5 year warranty on hardware fittings.")
            ],
            "customization": [
                ("Level of Customization", "Modular grid customization. Standardized cabinet modules can be combined with custom fillers, customized corner units, and dimensionally tailored panels within factory machining parameters."),
                ("Production Model", "Mass-customization and made-to-order manufacturing on automated Homag production lines."),
                ("Lead Times", "Standard dealer order: 25 to 30 days; Complex custom/membrane orders: 35 to 45 days from order confirmation.")
            ],
            "supply_chain": [
                ("In-House vs Outsourced vs Imported", "100% in-house manufacturing at the Nagpur mega-facility, providing exceptional quality control and scale efficiencies. High-grade hardware is imported from Hettich Germany."),
                ("Import Impact", "Negligible supply vulnerability due to massive local inventory buffering and strategic tie-ups with Hettich India's domestic facilities."),
                ("BIS Compliance Status", "Fully certified and compliant with BIS mandatory Quality Control Orders for wood-based boards (IS 3087) and flush wooden doors.")
            ],
            "pricing_structure": [
                ("Pricing Unit Used", "Modular unit rate card and per square foot rate (₹1,100 – ₹2,400/sq.ft. for standard cabinetry and shutters)."),
                ("Entry-Level Price Point", "₹1,10,000 – ₹1,50,000 for a compact straight-line modular kitchen package."),
                ("Mid-Range and Premium Price Ceiling", "Complete modular setups for 2BHK/3BHK homes range from ₹2,00,000 – ₹4,50,000; premium villa configurations reach ₹6,50,000 – ₹8,50,000."),
                ("Average Order Ticket Size", "₹1,80,000 – ₹3,20,000 per kitchen project."),
                ("Pricing Model", "Transparent dealer list price with packaged pricing for standard kitchen layouts. High dealer discount flexibility (12%–22% discount headroom at multi-brand retail outlets)."),
                ("EMI / Financing Options", "Partnered with Bajaj Finserv and major retail banks for consumer durable loans and EMI options.")
            ],
            "pricing_strategy": [
                ("Perceived Value Positioning", "Mass-Market to Value Mid-Market. Positioned as an industrial powerhouse delivering German quality at carpenter parity."),
                ("Festive Pricing Behaviour", "Periodic festive dealer discounts, free chimney/hob tie-in packages, and bundled bedroom-plus-kitchen renovation schemes."),
                ("Price Comparison vs Unorganized Carpenters", "Directly matches or beats local carpenter pricing for comparable materials while delivering far superior German PUR edge-banding and factory drilling precision."),
                ("Price vs Design/Value Verdict", "COMPETING ON PRICE & INDUSTRIAL VALUE. Evidence: Spacewood leverages its massive 25-acre automated manufacturing plant and Sumitomo technical backing to drive down per-unit manufacturing costs, allowing it to compete aggressively against unorganized contractors.")
            ],
            "physical_presence": [
                ("Total Number of Stores", "35+ exclusive brand experience centres, backed by an extensive distribution network of 500+ multi-brand furniture and kitchen dealers across India."),
                ("Cities & Tier Penetration", "Present in 60+ cities. Highly penetrated across Tier 1, Tier 2, and Tier 3 cities, with deep market dominance in Western, Central, and Northern India (Nagpur, Mumbai, Pune, Delhi-NCR, Indore, Raipur, Bhopal, Bengaluru, Hyderabad)."),
                ("Ownership Split", "85% dealer/franchise-operated and 15% company-owned flagship experience centres.")
            ],
            "online_presence": [
                ("Website Type", "Corporate catalogue and inquiry portal (spacewood.in), supplemented by direct e-commerce sales of flat-pack furniture on Amazon, Flipkart, and Pepperfry."),
                ("3D/AR Visualizer & Configurator", "Basic layout gallery and 2D design planner on website; in-store designers utilize professional CAD / KD Max software to render customer proposals."),
                ("Online vs Offline Catalogue Depth", "Website showcases core collections; offline dealer showrooms display complete material palettes, working drawer mechanisms, and tactile laminate finishes."),
                ("Website Feature-Mining for Client", "1) 360-degree virtual showroom video tours; 2) Downloadable AutoCAD / BIM furniture blocks for architects; 3) Interactive dealer locator with direct WhatsApp messaging.")
            ],
            "channel_expansion": [
                ("Expansion Pace", "Added 15–20 exclusive studios per year over the last 3 years; currently accelerating with ₹300 Cr capital from A91 Partners."),
                ("Future Targets", "Targeting 100+ exclusive brand stores and expanding presence across Southern and Eastern Indian Tier 2 cities."),
                ("Franchise Model Terms", "Franchise partner requires ₹20 – ₹35 Lakh initial investment for an 800–1,500 sq.ft. studio, offering 30% – 35% gross retail dealer margins."),
                ("Geographic White Spaces", "Deep interior towns in Southern India (Tamil Nadu, Kerala) and North-Eastern hill states.")
            ],
            "brand_promotion": [
                ("Core Brand Promise & Tagline", "'Smart Furniture for Modern Living' — engineered reliability, termite-proof HDF, and European precision."),
                ("Target Persona", "Budget to middle-class homeowners, builder apartment buyers, and institutional developers (home value: ₹35L – ₹1.2 Cr)."),
                ("Key Differentiators", "Massive single-location manufacturing capacity, Sumitomo Forestry partnership, 10-year Supertuff HDF warranty."),
                ("Digital Marketing", "Instagram: @spacewoodfurnishers (30.2K+ followers, moderate engagement featuring project photos); YouTube: Regional dealer channels featuring product walkthroughs and assembly guides."),
                ("Offline Marketing", "Prominent participation in ACETECH Mumbai/Delhi and Index Trade Fairs; extensive outdoor hoardings across Central and Western India; regional print newspaper advertisements."),
                ("Partnerships & Channels", "Massive institutional B2B supply agreements with top national builders (DLF, Godrej Properties, Tata Housing, Shapoorji Pallonji) for bulk residential fit-outs."),
                ("Customer Retention & Complaints", "Warranty card registration, dealer-led servicing. Google customer reviews praise the sturdy board quality and cost-effectiveness, but recurring complaint themes highlight inconsistent local dealer installation workmanship and communication delays during replacement part dispatches.")
            ],
            "service": [
                ("Lead Time Order to Installation", "25 to 35 calendar days from site laser measurement."),
                ("Installation Team", "Executed by authorized dealer-certified carpentry teams or Spacewood regional technical installation crews."),
                ("Order Tracking System", "Internal SAP ERP system tracking dealer orders; customer receives milestone status updates directly from the local dealer."),
                ("After-Sales Service Structure", "Dedicated corporate customer care desk (+91-80077-72510 / care@spacewood.in), regional service managers, and dealer-fulfilled replacement part logistics.")
            ]
        },
        {
            "num": "4",
            "name": "PANASONIC (HOMES & LIVING) — JAPAN / INDIA",
            "category": "Tier 2 / Tier 1: Japanese Precision Engineering (Strategic Market Restructuring)",
            "summary": "Panasonic Life Solutions India introduced Japanese ergonomic modular kitchens (L-Class and I-Class) featuring patented pull-down 'Magic Hopper' mechanisms and waterproof stainless steel sink bases. CRITICAL INTELLIGENCE UPDATE: Panasonic has officially ceased active new-retail sales for its Modular Kitchens business in India, transitioning strictly to warranty fulfillment and maintenance service via housingsvc.plsind@in.panasonic.com.",
            "snapshot": [
                ("Ownership", "100% subsidiary of Panasonic Holdings Corporation, Japan (operating in India through Panasonic Life Solutions India Pvt. Ltd., formerly Anchor Electricals)."),
                ("Country of Origin & India Entry Year", "Japan (Osaka, founded 1918). Entered the Indian modular kitchen market in 2018 under Panasonic Homes & Living / Housing division."),
                ("Estimated Revenue", "Modular kitchen vertical previously generated estimated peak annual revenue of ₹35 – ₹60 Crore in India. (Parent entity Panasonic Life Solutions India generates ₹4,500+ Cr across electrical and appliance verticals)."),
                ("Current Operational Status (CRITICAL AUDIT)", "Panasonic Life Solutions India has officially wound down and shut down its commercial sales of new modular kitchens in India. All retail showrooms have ceased accepting new kitchen bookings; the brand is actively honoring existing customer warranties and servicing contracts via a dedicated corporate housing team (housingsvc.plsind@in.panasonic.com)."),
                ("Manufacturing Footprint", "Previously operated an assembly and panel processing facility in Daman and Haridwar, combined with high-precision smart mechanical fittings, sink units, and pull-down storage systems imported directly from Panasonic manufacturing facilities in Japan."),
                ("Certifications Held", "Japanese Industrial Standards (JIS) four-star (F****) zero-formaldehyde emission certification, ISO 9001:2015, ISO 14001, and RoHS environmental compliance."),
                ("One-Line Positioning", "'Japanese Ergonomic Engineering for Indian Homes' — smart ergonomic storage, zero-formaldehyde indoor air safety, and indestructible stainless steel wet cabinetry.")
            ],
            "product_portfolio": [
                ("Categories Covered", "Modular kitchens, ergonomic pull-down overhead storage systems ('Magic Hopper'), smart electronic bidet toilets (Alauno), vanity consoles, and integrated kitchen appliances."),
                ("Depth per Category", "Offered two primary tiered series: 'I-Class' (engineered specifically for Indian cooking styles, turmeric stain resistance, and affordability) and 'L-Class' (luxury flagship Japanese import line)."),
                ("Hero Collections & Marketing", "L-Class featuring motorized and manual 'Magic Hopper' pull-down overhead trays, sink silencer dampeners, and seismic locking cabinets. Marketed strictly on ergonomic health, durability, and Japanese engineering."),
                ("Core Material Used by Price Tier", "Base Sink Cabinet: 100% High-Grade Antibacterial Stainless Steel carcass (waterproof, termite-proof, rust-proof); Dry Cabinets: IS 710 Marine Plywood or JIS F**** certified moisture-resistant engineered panels."),
                ("Finish Options Offered", "Anti-fingerprint thermal laminates, Japanese multi-layer high-durability acrylic, factory-cured PU lacquer, and lacquered glass with seamless aluminum edge-banding."),
                ("Hardware Brand Used", "Proprietary Panasonic Japan soft-down hydraulic damping mechanisms, push-to-open silent runners, and Blum European hinges."),
                ("Warranty Period & Coverage", "10-Year Replacement Guarantee on cabinetry carcasses and runner mechanisms (currently being honored under corporate warranty management).")
            ],
            "customization": [
                ("Level of Customization", "Modular precision system. Sized according to Japanese ergonomic principles adapted to Indian counter heights (850mm–900mm)."),
                ("Production Model", "Made-to-order assembly using imported Japanese smart mechanisms and locally processed panels."),
                ("Lead Times", "Standard I-Class order took 45 to 60 days; imported L-Class setups required 60 to 75 days.")
            ],
            "supply_chain": [
                ("In-House vs Outsourced vs Imported", "Hybrid model. Core smart mechanical units, stainless steel sink modules, and specialized accessories were imported from Japan; carcass panels fabricated domestically in Daman/Haridwar."),
                ("Supply Chain Bottleneck Analysis", "High reliance on imported Japanese components created customs tariff exposure, long lead times for replacement parts, and high inventory holding costs, contributing to the decision to wind down retail operations."),
                ("BIS Compliance Status", "Substrates met or exceeded Indian BIS standards; JIS F**** emission ratings are far more stringent than Indian E1 requirements.")
            ],
            "pricing_structure": [
                ("Pricing Unit Used", "Modular unit rate card with transparent component pricing."),
                ("Entry-Level Price Point", "₹2,50,000 – ₹3,50,000 for a compact I-Class modular kitchen."),
                ("Mid-Range and Premium Price Ceiling", "L-Class luxury configurations with stainless steel base, motorized pull-down trays, and built-in appliances ranged from ₹6,00,000 to ₹15,00,000+."),
                ("Average Order Ticket Size", "₹5,50,000 – ₹8,50,000 per kitchen installation."),
                ("Pricing Model", "Strict fixed list pricing with minimal dealer discounting (8%–12% maximum)."),
                ("EMI / Financing Options", "Previously offered financing via Panasonic consumer finance and partner retail banks.")
            ],
            "pricing_strategy": [
                ("Perceived Value Positioning", "Premium to Luxury. Geared towards affluent, health-conscious urban professionals seeking Japanese functional perfection."),
                ("Festive Pricing Behaviour", "Maintained strict pricing discipline; offered appliance bundling (free Panasonic microwave or induction hob) rather than slashing cabinetry prices."),
                ("Price Comparison vs Unorganized Carpenters", "Priced 80% – 150% higher than unorganized carpenters. Justified by indestructible stainless steel sink base, patented pull-down trays, and zero toxic emissions."),
                ("Price vs Design/Value Verdict", "COMPETING ON ERGONOMIC DESIGN & HEALTH VALUE. Evidence: Panasonic completely avoided price wars, choosing instead to market Japanese ergonomics (easy overhead access for elderly/short statures), sound-dampened sinks, and food-grade hygiene.")
            ],
            "physical_presence": [
                ("Total Number of Stores", "Previously operated 40+ Kitchen Experience Centres across Tier 1 metros. Showroom operations have now ceased as the retail modular division has been closed."),
                ("Cities & Tier Penetration", "Concentrated exclusively in Tier 1 cities (Delhi-NCR, Mumbai, Bengaluru, Pune, Hyderabad, Ahmedabad)."),
                ("Ownership Split", "90% franchise experience centres and 10% company-owned flagship studios during active operations.")
            ],
            "online_presence": [
                ("Website Type", "Corporate product information and active customer support portal (lsin.panasonic.com). New customer inquiries are closed; active warranty support maintained."),
                ("3D/AR Visualizer & Configurator", "Previously featured virtual showroom walkthroughs and CAD planning tools."),
                ("Online vs Offline Catalogue Depth", "Comprehensive product brochures and technical specification sheets remain accessible online."),
                ("Website Feature-Mining for Client", "1) Patented 'Magic Hopper' overhead pull-down accessibility shelf mechanism; 2) Stainless steel waterproof sink carcass module; 3) Noise-dampening sink silencer coating.")
            ],
            "channel_expansion": [
                ("Expansion Pace & Future Targets", "No new retail expansion. Strategic consolidation to honor existing warranty obligations and refocus on core electricals, HVAC, and smart home appliances."),
                ("Franchise Model Terms", "Previously required ₹35 – ₹50 Lakh capex with 25% – 30% dealer margins."),
                ("Geographic White Spaces", "Entire Tier 2/3/4 non-metro landscape.")
            ],
            "brand_promotion": [
                ("Core Brand Promise & Tagline", "'Japanese Ergonomic Living' / 'Smart Kitchens Designed for Indian Cooking'."),
                ("Target Persona", "Upper-middle to High-Net-Worth Individuals (HNIs), tech-savvy homeowners, and Japanese expat residences (home value: ₹1.2 Cr – ₹6.0 Cr)."),
                ("Key Differentiators", "100% waterproof stainless steel sink carcass, patented pull-down overhead storage, zero-formaldehyde JIS F**** rating."),
                ("Digital Marketing", "Corporate digital marketing via Panasonic Life Solutions India; YouTube videos showcasing kitchen ergonomics and durability demonstrations."),
                ("Offline Marketing", "Previously sponsored high-end architectural symposiums (FOAID, ACETECH) and developer roundtables."),
                ("Partnerships & Channels", "Direct B2B specification by luxury developers building premium expat housing in Gurugram, Mumbai, and Bengaluru."),
                ("Customer Retention & Service Legacy", "Corporate commitment to honor all 10-year warranties through a dedicated email channel (`housingsvc.plsind@in.panasonic.com`) and national customer care desk (1800-103-1333), preserving brand goodwill despite retail exit.")
            ],
            "service": [
                ("Lead Time Order to Installation", "Historically 45 to 60 days (I-Class) and 60 to 75 days (L-Class)."),
                ("Installation Team", "Handled by Panasonic-certified precision technicians."),
                ("Order Tracking System", "Managed via Panasonic internal ERP system."),
                ("After-Sales Service Structure", "Dedicated ongoing warranty support team reachable at `housingsvc.plsind@in.panasonic.com` and toll-free helpline (1800-103-1333).")
            ]
        },
        {
            "num": "5",
            "name": "CASANTRO — INDIA",
            "category": "Tier 2: Bespoke Designer Luxury Boutique (Architect-Centric Innovator)",
            "summary": "Established in 2022 and headquartered in Bengaluru with manufacturing in Surat, Casantro is an unfunded, fast-scaling luxury brand specializing in bespoke modular kitchens and walk-in wardrobes. It caters almost exclusively to architects and high-end interior designers, delivering Pinterest-worthy aesthetics (Japandi, Fluted Glass, Neoclassical) and 100% Blum hardware at European quality with Indian lead times.",
            "snapshot": [
                ("Ownership", "Privately held, bootstrapped luxury design and manufacturing enterprise (Casantro Luxury Kitchens & Wardrobes, founded in 2022). Key leadership includes Arunava Dutta (Marketing Head) and Hinesha Patel (Design Manager)."),
                ("Country of Origin & India Entry Year", "India. Established in 2022 with corporate headquarters in Bengaluru, Karnataka, and manufacturing roots in Surat, Gujarat."),
                ("Estimated Revenue", "India operations revenue estimated at ₹25 – ₹45 Crore annually, growing rapidly within the luxury architect-specified residential segment."),
                ("Manufacturing Footprint", "Integrated 85,000 sq. ft. precision manufacturing plant equipped with cutting-edge European CNC machinery (Homag and Biesse lines) championing 'Zero-Error Manufacturing'."),
                ("Certifications Held", "ISO 9001:2015, E1/E0 low-emission compliant boards, IS 710 calibrated marine plywood, and FSC certified timber sourcing."),
                ("One-Line Positioning", "'Poetry in Design' — crafting bespoke luxury kitchens and walk-in wardrobes that seamlessly translate architectural concepts into factory-finished reality.")
            ],
            "product_portfolio": [
                ("Categories Covered", "Luxury bespoke modular kitchens, custom walk-in wardrobes & closet systems, vanity units, bar counters, credenzas, and integrated architectural wall paneling."),
                ("Depth per Category", "Extensive architectural depth categorized across 5 distinct aesthetic design styles: Minimalist, Japandi, Bohemian, Neoclassical, and Contemporary Industrial; over 150+ finish and hardware permutations."),
                ("Hero Collections & Marketing", "'Japandi Harmony' kitchen series, 'Neoclassic Fluted' collection, and 'Casantro Glass & Metal' walk-in closet systems with integrated concealed sensor LED lighting. Marketed strictly on bespoke design aesthetics and artisanal craftsmanship."),
                ("Core Material Used by Price Tier", "100% Calibrated IS 710 Boiling Water Proof (BWP) Marine Plywood, High-Density Moisture Resistant (HDHMR) boards, and premium European Birch Plywood carcasses."),
                ("Finish Options Offered", "Anti-fingerprint Ultra-Matte, Italian Multi-layer PU Lacquer (matte, gloss, metallic), Tinted & Fluted Glass in anodized aluminum profile frames, Sintered Stone / Ceramic fronts, and Exotic Natural Wood Veneers with poly-coat."),
                ("Hardware Brand Used", "100% Austrian Blum (Legrabox, Tandembox, Aventos bi-fold lift systems) and Häfele architectural hardware fittings."),
                ("Warranty Period & Coverage", "Comprehensive 10-Year Warranty on factory-finished cabinetry and carcass joinery; 5-Year warranty on Blum/Häfele motion hardware.")
            ],
            "customization": [
                ("Level of Customization", "100% Bespoke dimensional customization. Does not restrict designs to rigid modular grids; fabricates cabinetry to exact millimetric architectural drawings."),
                ("Production Model", "100% Custom Made-to-order based on verified architectural AutoCAD / 3D models."),
                ("Lead Times", "Standard production and white-glove installation timeline of 45 to 60 calendar days from approved shop drawings.")
            ],
            "supply_chain": [
                ("In-House vs Outsourced vs Imported", "In-house manufacturing at its dedicated 85,000 sq. ft. Surat/Bengaluru facility using European CNC automation. Hardware is imported from Blum Austria; raw boards sourced from certified domestic and European mills."),
                ("Import Impact", "Hardware costs reflect premium European import pricing, fully absorbed within luxury project margins."),
                ("BIS Compliance Status", "Fully compliant with IS 710 marine plywood and IS 3087 board quality standards.")
            ],
            "pricing_structure": [
                ("Pricing Unit Used", "Custom Bill of Quantities (BOQ) based on linear footage, material tier, and internal accessory complexity (indicative rate ₹2,500 – ₹8,500+/sq.ft.)."),
                ("Entry-Level Price Point", "₹3,50,000 – ₹5,00,000 (minimum entry threshold for a compact bespoke designer kitchen)."),
                ("Mid-Range and Premium Price Ceiling", "Standard luxury kitchens range from ₹8,00,000 – ₹18,00,000; palatial villa kitchens with sintered stone, motorized Blum lift systems, and walk-in pantries reach ₹22,00,000 – ₹35,00,000+."),
                ("Average Order Ticket Size", "₹7,50,000 – ₹14,00,000 per kitchen project."),
                ("Pricing Model", "Project-based architectural quotation. Transparent line-item pricing for trade partners; low retail discounting (5%–10% trade courtesy)."),
                ("EMI / Financing Options", "High-net-worth project milestone payments (40% advance, 50% on factory dispatch, 10% on installation sign-off); select bank EMI assistance upon request.")
            ],
            "pricing_strategy": [
                ("Perceived Value Positioning", "Luxury & Designer Bespoke. Positioned directly between mass-market Indian players (HomeLane, Sleek) and ultra-expensive European imports (Pedini, Poliform)."),
                ("Festive Pricing Behaviour", "Does not engage in mass discount sales; maintains brand exclusivity by offering complimentary architectural hardware upgrades or bar cabinet additions."),
                ("Price Comparison vs Unorganized Carpenters", "Priced 100% – 200% above unorganized carpenters. Justified by zero-error CNC precision, authentic Blum Legrabox drawers, fluted glass craftsmanship, and 10-year warranty."),
                ("Price vs Design/Value Verdict", "COMPETING ON BESPOKE DESIGN & ARCHITECTURAL VALUE. Evidence: Casantro positions itself as the designer's execution partner, competing directly against imported European brands by delivering identical aesthetic luxury at 40% lower cost and half the lead time.")
            ],
            "physical_presence": [
                ("Total Number of Stores", "Operates 6+ luxury experience centres and design studios across India's prime architectural hubs."),
                ("Cities & Tier Penetration", "Present in Bengaluru (flagship studios in Indiranagar/HSR), Hyderabad (Banjara Hills), Ahmedabad, Pune, Surat, and Noida/Delhi-NCR."),
                ("Ownership Split", "60% partner/franchise studios and 40% company-operated luxury experience lounges.")
            ],
            "online_presence": [
                ("Website Type", "High-aesthetic portfolio and design lookbook portal (casantro.com) with dedicated trade partner login and inquiry generation."),
                ("3D/AR Visualizer & Configurator", "No public self-service configurator; provides direct 3D CAD/Max rendering support and production drawings directly to architects and interior designers."),
                ("Online vs Offline Catalogue Depth", "Website features curated project photography and stylistic lookbooks; full tactile material swatch kits (veneers, lacquers, ceramics) are experienced in physical studios."),
                ("Website Feature-Mining for Client", "1) Dedicated 'Architect & Designer Partner Portal' allowing direct upload of CAD drawings for rapid factory quoting; 2) Curated 'Design Style Lookbooks' categorizing projects into Japandi, Neoclassical, and Minimalist themes; 3) Material specification comparison guides (Laminate vs Acrylic vs PU).")
            ],
            "channel_expansion": [
                ("Expansion Pace", "Selective expansion, adding 2–3 luxury studios per year in high-wealth urban pockets."),
                ("Future Targets", "Targeting 12–15 experience centres in top Tier 1 cities and affluent Tier 2 capitals (Chandigarh, Jaipur, Kochi)."),
                ("Franchise Model Terms", "High-end franchise studio requires ₹40 – ₹60 Lakh investment in an upscale design district, offering 28% – 35% gross margins."),
                ("Geographic White Spaces", "Mass-market Tier 2/3 towns, budget housing developments.")
            ],
            "brand_promotion": [
                ("Core Brand Promise & Tagline", "'Poetry in Design' — bespoke European elegance tailored for Indian living."),
                ("Target Persona", "Luxury homeowners, villa owners, and intermediate professional buyers (architects, luxury interior designers) specifying for homes valued at ₹2.5 Cr – ₹15 Cr+."),
                ("Key Differentiators", "Zero-error manufacturing, authentic Blum Legrabox hardware, bespoke fluted glass and sintered stone shutter capabilities, 10-year warranty."),
                ("Digital Marketing", "Instagram: @casantro_in (curated architectural imagery, reels showcasing Blum motion systems and LED glass wardrobes); YouTube: Experience centre walkthroughs and educational masterclasses on interior finishes."),
                ("Offline Marketing", "Features in prominent architectural journals (The Architect's Diary, Architecture+Design, Elle Decor), sponsorships of regional IIID (Institute of Indian Interior Designers) events."),
                ("Partnerships & Channels", "Direct B2B commission structure for architects and interior designers (10%–15% trade commission); turnkey sample villa installations for luxury developers."),
                ("Customer Retention & Complaints", "High-touch concierge client relationship management; dedicated project manager for each villa project; complimentary 6-month alignment audit. Review sentiment is exceptionally positive for design execution, with isolated complaints relating to lead-time extensions on complex imported stone shutters.")
            ],
            "service": [
                ("Lead Time Order to Installation", "45 to 60 calendar days from approved production drawings."),
                ("Installation Team", "White-glove in-house master technicians equipped with laser leveling systems and dustless tooling."),
                ("Order Tracking System", "Weekly milestone photo reports from the factory floor shared directly with the client and architect via a dedicated WhatsApp/email project bridge."),
                ("After-Sales Service Structure", "Dedicated concierge support desk, comprehensive 10-year warranty documentation, and priority 48-hour service technician dispatch.")
            ]
        },
        {
            "num": "6",
            "name": "ITALLICA (ITALICA MODULAR FURNITURE) — INDIA",
            "category": "Tier 3: Regional Value Fabricator & B2B Trade Network",
            "summary": "Operating as a trade-focused modular furniture manufacturer and fabricator based in New Delhi and Western India, Italica Modular Furniture captures price-sensitive consumers through B2B trade platforms (TradeIndia, IndiaMART). It offers custom modular kitchens at wholesale rates, competing aggressively on rock-bottom prices and fast turnarounds.",
            "snapshot": [
                ("Ownership", "Privately owned Indian MSME proprietorship/partnership enterprise (operating as Italica Modular Furniture / Itallica network, established circa 2012)."),
                ("Country of Origin & India Entry Year", "India. Headquartered in Malviya Nagar, New Delhi, with affiliated fabrication workshops in Gujarat (Ahmedabad/Rajkot) and Mumbai."),
                ("Estimated Revenue", "India operations revenue estimated at ₹10 – ₹20 Crore annually across regional trade portal orders, local builder fit-outs, and direct consumer inquiries."),
                ("Manufacturing Footprint", "Semi-automated regional workshop facilities (15,000–25,000 sq. ft.) in Delhi-NCR and Gujarat equipped with localized panel saws, edge-banders, and manual assembly stations."),
                ("Certifications Held", "Raw materials utilize commercial IS 303 (Moisture Resistant) and IS 710 (Boiling Water Proof) certified plywood sourced from third-party manufacturers; workshop lacks independent green building certifications."),
                ("One-Line Positioning", "'Italian-Style Modular Kitchens at Direct Factory Prices' — eliminating retail showroom markups to provide functional modularity at wholesale rates.")
            ],
            "product_portfolio": [
                ("Categories Covered", "Modular kitchens, modular wardrobes, office workstation storage, shoe racks, almirahs with drawers, and multi-purpose domestic cabinetry."),
                ("Depth per Category", "Standard modular configurations (Straight, L-shaped, U-shaped, Parallel); ~35–45 standard laminate color options, 15 high-gloss acrylic finishes."),
                ("Hero Collections & Marketing", "'Value-Line Acrylic Kitchen' and 'Commercial BWP Plywood Collection', marketed strictly on price competitiveness and quick installation."),
                ("Core Material Used by Price Tier", "Base: Commercial Grade Moisture Resistant (MR) Plywood (IS 303) or Pre-laminated MDF; Mid/High: Boiling Water Proof (BWP) Plywood (IS 710); Budget Waterproof: PVC Foam Board for sink cabinets."),
                ("Finish Options Offered", "0.8mm – 1.0mm Decorative Laminates, High-Gloss Acrylic sheets pressed on board, and PVC Membrane Foils."),
                ("Hardware Brand Used", "Ebco, Godrej, and OEM unbranded soft-close hinges, basic ball-bearing telescopic drawer channels, and wire baskets."),
                ("Warranty Period & Coverage", "3 to 5-Year Limited Warranty on cabinetry against manufacturing defects; hardware carries separate 1–2 year component warranties.")
            ],
            "customization": [
                ("Level of Customization", "High dimensional flexibility achieved via localized workshop fabrication and on-site carpenter adjustments (semi-modular)."),
                ("Production Model", "100% Made-to-order based on contractor/carpenter site measurements."),
                ("Lead Times", "Rapid turnaround of 15 to 25 calendar days from order advance.")
            ],
            "supply_chain": [
                ("In-House vs Outsourced vs Imported", "Localized domestic procurement of plywood boards, laminates, and hardware; cut, edge-banded, and assembled in regional workshops."),
                ("Import Impact", "Negligible import exposure; completely shielded from foreign currency swings."),
                ("BIS Compliance Status", "Sources plywood bearing ISI marks from commercial mills; assembly workshop does not hold standalone BIS factory licenses.")
            ],
            "pricing_structure": [
                ("Pricing Unit Used", "Per square foot rate card (₹1,000 – ₹1,900/sq.ft. for cabinetry and shutters) or flat package price."),
                ("Entry-Level Price Point", "₹85,000 – ₹1,20,000 for a compact 8x6 ft straight modular kitchen in commercial ply/laminate."),
                ("Mid-Range and Premium Price Ceiling", "Complete acrylic and BWP plywood setups range from ₹1,80,000 – ₹3,50,000."),
                ("Average Order Ticket Size", "₹1,40,000 – ₹2,20,000 per kitchen project."),
                ("Pricing Model", "Direct negotiable quote. High bargaining leeway (15%–25% negotiation discounts common on trade platforms)."),
                ("EMI / Financing Options", "Cash, NEFT, UPI; no in-house EMI schemes (customers utilize personal loans or credit card EMI).")
            ],
            "pricing_strategy": [
                ("Perceived Value Positioning", "Mass-Market / Budget Value. Targets cost-conscious homeowners seeking the appearance of a modular kitchen without paying brand premiums."),
                ("Festive Pricing Behaviour", "Tactical discounts during festive months (free stainless steel basket set or additional 10% cash discount)."),
                ("Price Comparison vs Unorganized Carpenters", "Directly matches or undercuts local carpenter rates by eliminating middleman retail markups."),
                ("Price vs Design/Value Verdict", "COMPETING PURELY ON PRICE. Evidence: Marketing and sales interactions lead entirely with per-square-foot cost discounts, wholesale manufacturing claims, and aggressive price matching against brand quotes.")
            ],
            "physical_presence": [
                ("Total Number of Stores", "1-2 regional display sales offices/workshops in New Delhi (Malviya Nagar / Kirti Nagar area) and local partner dealers in Gujarat; primary lead generation via digital trade portals."),
                ("Cities & Tier Penetration", "Operates primarily in Delhi-NCR, Ahmedabad, Rajkot, Vadodara, and Mumbai suburban peripheries."),
                ("Ownership Split", "100% independent workshop / proprietor operated.")
            ],
            "online_presence": [
                ("Website Type", "B2B marketplace digital storefronts on TradeIndia and IndiaMART, alongside basic informational landing pages."),
                ("3D/AR Visualizer & Configurator", "No digital visualizer or online configurator; basic 2D CAD drawings generated manually after site measurement."),
                ("Online vs Offline Catalogue Depth", "Online presence showcases photo galleries of past projects; physical material samples shown in person by sales representatives."),
                ("Website Feature-Mining for Client", "1) Floating 'Request Instant Wholesale Quote' WhatsApp widget; 2) Transparent per-sq-ft rate card breakdown table by material grade (Laminate vs Acrylic vs PVC).")
            ],
            "channel_expansion": [
                ("Expansion Pace & Future Targets", "Organic expansion driven by B2B portal inquiry volume and local contractor networks; no formal retail franchise expansion targets."),
                ("Franchise Model Terms", "No structured franchise model; operates through contractor supply arrangements."),
                ("Geographic White Spaces", "Entire Southern India, Eastern India, and upscale luxury residential markets.")
            ],
            "brand_promotion": [
                ("Core Brand Promise & Tagline", "'Direct Factory Modular Kitchens at Unbeatable Prices'."),
                ("Target Persona", "Budget homeowners, rental property owners, small building contractors, and price-sensitive renovators (home value: ₹30L – ₹90L)."),
                ("Key Differentiators", "Lowest price per square foot, fast 15-day delivery turnaround, local contractor flexibility."),
                ("Digital Marketing", "Minimal social media presence; relies primarily on paid buyer leads and priority listings on IndiaMART and TradeIndia."),
                ("Offline Marketing", "Local classified directories, pamphlet distribution in newly developed housing colonies, and building material market word-of-mouth."),
                ("Partnerships & Channels", "Informal referral relationships with local electricians, plumbers, and painting contractors (5%–8% cash referral fee)."),
                ("Customer Retention & Complaints", "Transactional customer relationship with minimal post-sales CRM. Review sentiment on B2B platforms is mixed: customers praise low upfront cost and rapid setup, but recurring complaint themes highlight delayed completion of minor punch items, edge-tape peeling after 1–2 years, and unresponsiveness for warranty service.")
            ],
            "service": [
                ("Lead Time Order to Installation", "15 to 25 calendar days from site measurement and advance payment."),
                ("Installation Team", "Handled by contracted third-party freelance carpenters."),
                ("Order Tracking System", "Informal phone/WhatsApp updates directly from the workshop manager."),
                ("After-Sales Service Structure", "Direct mobile contact with workshop owner; after-sales service is often sluggish once final payment is settled.")
            ]
        },
        {
            "num": "7",
            "name": "PEDINI — ITALY",
            "category": "Tier 1: Ultra-Luxury European Haute Couture (World Pioneer in Curved Kitchens)",
            "summary": "Founded in 1957 in Pesaro, Italy, Pedini is globally celebrated as the pioneer of the curved modular kitchen system (Dune, Artika). In June 2025, Pedini completed a strategic recapitalization involving Demiray Italy Holdings and Radifin. In India, it operates exclusively in the ultra-luxury tier through bespoke architectural importers, delivering 100% Made-in-Italy kitchens for palatial residences and penthouses.",
            "snapshot": [
                ("Ownership", "Privately held Italian luxury joint-stock corporation (Pedini S.p.A. / Pedini S.r.l., established in 1957). In June 2025, completed a strategic corporate restructuring/recapitalization with investors including Demiray Italy Holdings and Radifin."),
                ("Country of Origin & India Entry Year", "Italy (Lucrezia di Cartoceto, Pesaro-Urbino). Pioneered the world's first curved modular kitchen in 1957. Entered India circa 2008–2010 through luxury multi-brand architectural importers and high-end design ateliers."),
                ("Estimated Revenue", "Global company turnover estimated at €30M – €50M; India project import revenue estimated at ₹15 – ₹30 Crore annually (an exclusive ultra-luxury niche comprising 25–50 palatial installations per year)."),
                ("Manufacturing Footprint", "100% manufactured at Pedini's state-of-the-art 300,000+ sq. ft. automated robotic facility in Lucrezia di Cartoceto, Pesaro, Italy. Zero manufacturing in India."),
                ("Certifications Held", "100% Made in Italy Certification, ISO 9001:2015, ISO 14001, FSC Certified timber, CARB Phase 2 / E0 zero-emission certification, and Green Guard Gold environmental certification for non-toxic finishes."),
                ("One-Line Positioning", "'The Art of Living Curved' — haute couture Italian kitchens and architectural systems blending sculpted organic curves with aerospace-grade precision.")
            ],
            "product_portfolio": [
                ("Categories Covered", "Ultra-luxury curved and linear modular kitchens, architectural living systems, bespoke walk-in closet systems, and luxury bathroom vanities."),
                ("Depth per Category", "8 iconic architectural collections (Dune, Artika, Materika, K016, Arkè, Arts & Crafts, Vintage, Moka); 200+ exclusive Italian finishes including thermoformed curved woods, liquid metals, ecomalta, and sintered porcelain."),
                ("Hero Collections & Marketing", "'Dune' (world-famous handleless curved kitchen with integrated Corian surfaces) and 'Artika' (iconic organic curved island). Marketed purely on architectural design awards, Italian heritage, and ergonomic sculpturing."),
                ("Core Material Used by Price Tier", "High-density curved ecological water-repellent panels, extruded marine-grade structural aluminum frames, solid thermoformed composite worktops, and carbon-fiber/honeycomb reinforcements."),
                ("Finish Options Offered", "Ecomalta (eco-resin mortar), Liquid Metal coatings (bronze, brass, titanium), Thermoformed Canaletto Walnut & Thermal Oak, Sintered Ceramic/Laminam, and Acid-Etched/Fluted Italian Glass."),
                ("Hardware Brand Used", "Custom Blum Legrabox systems with bespoke Pedini titanium branding, Salice Silentia concealed 110° damping hinges, and motorized Servo-Drive touch-opening mechanisms."),
                ("Warranty Period & Coverage", "10-Year International Factory Warranty backed directly by Pedini S.p.A. covering structural integrity and mechanical drawer systems.")
            ],
            "customization": [
                ("Level of Customization", "Fully bespoke architectural customization. Master of custom curved radii, integrated breakfast cantilevers, and recessed appliance garages."),
                ("Production Model", "100% Bespoke Made-to-Order at the Italian factory based on architectural CAD drawings."),
                ("Lead Times", "14 to 18 weeks (including robotic precision fabrication in Italy, sea container shipping to Indian ports, customs clearance, and white-glove assembly).")
            ],
            "supply_chain": [
                ("In-House vs Outsourced vs Imported", "100% imported from Italy. Precision fabrication, lacquering, and pre-assembly take place entirely in Pesaro, Italy."),
                ("Import Impact", "Extremely high tariff and logistics exposure: subject to 35%–40% basic customs duty + IGST + international container freight costs. Long lead time vulnerable to port clearance and global shipping fluctuations."),
                ("BIS Compliance Status", "Imported as specialized architectural luxury furniture; complies with strict European CE, CARB P2, and FSC norms. Under India's DPIIT Quality Control Orders, imported luxury shipments require meticulous documentation or FMCS compliance.")
            ],
            "pricing_structure": [
                ("Pricing Unit Used", "Euro-denominated project Bill of Quantities (BOQ) converted to INR based on landed import costs (translates to ₹7,000 – ₹25,000+/sq.ft.)."),
                ("Entry-Level Price Point", "₹15,00,000 – ₹20,00,000 for an entry-level linear Italian configuration (including basic sea freight and import duties)."),
                ("Mid-Range and Premium Price Ceiling", "Signature curved configurations (Dune / Artika) range from ₹35,00,000 – ₹85,00,000; ultra-luxury palatial villa installations with motorized systems and exotic finishes exceed ₹1,50,00,000 – ₹2,00,00,000+."),
                ("Average Order Ticket Size", "₹28,00,000 – ₹65,00,000 per kitchen installation."),
                ("Pricing Model", "Strict bespoke architectural quote. Fixed international price lists with zero retail discounting (importers may absorb fractional logistics costs on multi-crore villa fit-outs)."),
                ("EMI / Financing Options", "High-net-worth project stage payments: 50% advance booking deposit, 40% prior to container dispatch from Italy, and 10% upon installation sign-off.")
            ],
            "pricing_strategy": [
                ("Perceived Value Positioning", "Ultra-Luxury / Haute Couture. Competes exclusively in the billionaire and HNI stratosphere alongside Boffi, Bulthaup, and Poliform."),
                ("Festive Pricing Behaviour", "Zero discount participation; price slashing is viewed as brand-dilutive in the ultra-luxury segment."),
                ("Price Comparison vs Unorganized Carpenters", "Not comparable. An unorganized carpenter cannot replicate thermoformed curved carcasses, seamless Corian welding, or patented Italian liquid metal coatings."),
                ("Price vs Design/Value Verdict", "COMPETING ON ARCHITECTURAL DESIGN & STATUS PRESTIGE. Evidence: Pedini sells sculptural exclusivity and Italian design history. Clients commission Pedini not based on price-per-square-foot, but to own an iconic architectural masterpiece.")
            ],
            "physical_presence": [
                ("Total Number of Stores", "Exclusive boutique display presence through certified luxury architectural importers (e.g., Studio Creo in New Delhi, Meine Kuche in Pune, and select luxury ateliers in Mumbai and Bengaluru)."),
                ("Cities & Tier Penetration", "Strictly limited to Tier 1 ultra-luxury residential corridors (Mumbai, South Delhi, Gurugram, Bengaluru, Hyderabad)."),
                ("Ownership Split", "100% exclusive architectural distributor / luxury boutique partner model.")
            ],
            "online_presence": [
                ("Website Type", "World-class luxury global brand portal (pedini.it) featuring high-resolution photography, architectural video case studies, and virtual showroom tours."),
                ("3D/AR Visualizer & Configurator", "Provides professional-grade downloadable BIM and Revit 3D files for architects and interior designers; no consumer self-checkout."),
                ("Online vs Offline Catalogue Depth", "Extensive online lookbooks and downloadable technical brochures; tactile finishes (ecomalta, liquid metal, canaletto walnut) must be experienced in person."),
                ("Website Feature-Mining for Client", "1) Downloadable high-resolution BIM/CAD objects for architectural specification; 2) 360-degree interactive 3D virtual tour of curved kitchen collections; 3) Material tactile sampling kit box for high-profile clients.")
            ],
            "channel_expansion": [
                ("Expansion Pace & Future Targets", "Highly conservative. Partners exclusively with well-capitalized luxury interior ateliers capable of maintaining €100,000+ display showrooms."),
                ("Franchise Model Terms", "Selective dealership model requiring €100,000 – €200,000 showroom investment and proven access to ultra-high-net-worth clients."),
                ("Geographic White Spaces", "Entire Tier 2/3/4 landscape; exclusively focused on top 0.1% wealth enclaves.")
            ],
            "brand_promotion": [
                ("Core Brand Promise & Tagline", "'The Art of Living Curved' — Italian haute couture cabinetry since 1957."),
                ("Target Persona", "Ultra-High-Net-Worth Individuals (UHNIs), industrialists, Bollywood/celebrity residences, and renowned architectural firms (home value: ₹12 Cr – ₹80+ Cr)."),
                ("Key Differentiators", "World pioneer in curved modular cabinetry, 100% Made in Italy, patented ergonomic drawer trajectories, museum-grade material finishes."),
                ("Digital Marketing", "Instagram: @pedinicucine (100K+ followers, museum-grade aesthetic curation); YouTube: High-production films showcasing Milan Design Week exhibits and Italian craftsmanship."),
                ("Offline Marketing", "Global anchor exhibitor at Salone del Mobile Milano (EuroCucina); regular features in Architectural Digest International, Elle Decor Italia; private concierge dinners for elite architects."),
                ("Partnerships & Channels", "Direct collaboration with celebrity architects and bespoke luxury developers designing super-luxury branded penthouses and private estates."),
                ("Customer Retention & Complaints", "White-glove concierge lifetime relationship management. Client satisfaction among luxury homeowners is exceptionally high; the only recurring friction points involve long transit lead times (14–18 weeks) and European summer factory shutdowns during August.")
            ],
            "service": [
                ("Lead Time Order to Installation", "14 to 18 weeks from approved CAD sign-off to delivery in India."),
                ("Installation Team", "White-glove installation executed by Italian-certified master technicians trained in laser leveling, seamless Corian welding, and curved alignment."),
                ("Order Tracking System", "International sea freight container milestone tracking coordinated through the local luxury import partner."),
                ("After-Sales Service Structure", "Direct factory warranty support, air-courier replacement part dispatch from Italy, and specialized local architectural technician service.")
            ]
        },
        {
            "num": "8",
            "name": "LINHOFF — INDIA",
            "category": "Tier 3 / Tier 2: Regional German-Tech Precision Powerhouse (Central UP Leader)",
            "summary": "Operating as a specialized modular interior unit of M/S Feller Design Interiors in Lucknow, Linhoff delivers German CNC precision manufacturing at factory-direct pricing across Uttar Pradesh. With a modern flagship experience centre in Gomti Nagar Extension and an online price calculator, Linhoff provides a 10-year warranty, outperforming both local carpenters and rigid national brands.",
            "snapshot": [
                ("Ownership", "Privately held Indian interior enterprise, operating as the specialized modular manufacturing and retail brand of M/S Feller Design Interiors."),
                ("Country of Origin & India Entry Year", "India. Headquartered in Lucknow, Uttar Pradesh. Established to deliver engineered, factory-finished panel furniture across Central and Eastern UP."),
                ("Estimated Revenue", "India operations revenue estimated at ₹8 – ₹18 Crore annually, representing strong regional market dominance in Lucknow and surrounding residential corridors."),
                ("Manufacturing Footprint", "Dedicated, fully equipped panel processing manufacturing plant in Lucknow utilizing precision German-based machinery (automated beam saws, through-feed edge-banders, multi-spindle boring machines)."),
                ("Certifications Held", "ISO 9001:2015, IS 710 calibrated marine plywood compliance, IS 3087 for engineered wood boards, and low-VOC emission standards."),
                ("One-Line Positioning", "'Crafting Functional Elegance' / 'Lucknow's Premier Modular Kitchen & Custom Interior Manufacturer with German Precision' — direct factory accountability, 10-year warranty.")
            ],
            "product_portfolio": [
                ("Categories Covered", "Modular kitchens, customized modular wardrobes (sliding, openable, walk-in closets), bathroom vanities, LED console units, dining consoles, mandirs/wooden temples, and full turnkey residential woodworking."),
                ("Depth per Category", "Full layout range (Straight, L-shaped, Parallel, U-shaped, Island); 4 signature curated kitchen design collections ('Socialize and Cook', 'HarmonyHaven', 'MetroFiesta', 'EcoMod Cuisine Hub'); 80+ laminate and acrylic finish combinations."),
                ("Hero Collections & Marketing", "'MetroFiesta Acrylic' and 'EcoMod Moisture-Proof' kitchen series, marketed on a balance of contemporary aesthetics, moisture/termite proofing, and localized factory responsiveness."),
                ("Core Material Used by Price Tier", "100% Calibrated Boiling Water Proof (BWP) Marine Plywood (IS 710), High-Density Moisture Resistant (HDHMR) board, and termite-resistant engineered composite boards."),
                ("Finish Options Offered", "Anti-scratch High-Gloss Acrylic, Textured and Suede-finish Decorative Laminates, Factory PU Painted finishes, and Fluted Glass in sleek black aluminum profiles."),
                ("Hardware Brand Used", "Blum, Hettich, and Ebco soft-close hinges, tandem box runners, corner carousels, and tall pantry larder pull-out systems."),
                ("Warranty Period & Coverage", "Flat 10-Year Warranty on modular kitchens and custom wardrobes; 5-Year warranty on branded hardware fittings.")
            ],
            "customization": [
                ("Level of Customization", "Fully customizable panel-based modular configurations tailored to exact on-site civil room dimensions without modular grid limitations."),
                ("Production Model", "100% Made-to-order at its Lucknow manufacturing plant."),
                ("Lead Times", "25 to 35 calendar days standard delivery and installation turnaround.")
            ],
            "supply_chain": [
                ("In-House vs Outsourced vs Imported", "In-house manufacturing in Lucknow utilizing German CNC machinery; localized supply chain eliminates inter-state logistics delays."),
                ("Import Impact", "Hardware (Blum/Hettich) is procured through domestic authorized distributor networks, insulating the brand from direct foreign exchange volatility."),
                ("BIS Compliance Status", "Fully compliant with Indian standards for BWP plywood (IS 710) and engineered wood substrates.")
            ],
            "pricing_structure": [
                ("Pricing Unit Used", "Per square foot rate card (₹1,300 – ₹2,800/sq.ft. for cabinetry and shutters) or modular package pricing starting from ₹1,00,000."),
                ("Entry-Level Price Point", "₹1,00,000 – ₹1,40,000 for a compact straight-line kitchen with standard laminate finish."),
                ("Mid-Range and Premium Price Ceiling", "Full modular L/U-shaped kitchens with tandem drawers, acrylic finish, and tall pantry unit range from ₹2,20,000 – ₹4,80,000."),
                ("Average Order Ticket Size", "₹1,80,000 – ₹3,20,000 per kitchen project."),
                ("Pricing Model", "Transparent quote-based model supplemented by an interactive online 'Modular Kitchen Price Calculator' on linhoff.in. Negotiable discount buffer of 8%–15%."),
                ("EMI / Financing Options", "Tie-ups with local bank personal loans and EMI financing facilities.")
            ],
            "pricing_strategy": [
                ("Perceived Value Positioning", "Value-to-Mid-Market Regional Champion. Successfully bridges the gap between unorganized carpenters and rigid, expensive national brands."),
                ("Festive Pricing Behaviour", "Festive promotional bundles including complimentary chimney installations, free stainless steel pull-out accessories, or festival discount vouchers."),
                ("Price Comparison vs Unorganized Carpenters", "Priced roughly 10% – 20% above local unorganized carpenters, but easily wins clients by showcasing factory PUR edge-banding, termite resistance, and a legally binding 10-year warranty."),
                ("Price vs Design/Value Verdict", "COMPETING ON LOCALIZED VALUE & ACCOUNTABILITY. Evidence: Homeowners choose Linhoff because they get direct access to local factory owners, custom flexibility, and rapid local service that remote national brands struggle to match.")
            ],
            "physical_presence": [
                ("Total Number of Stores", "Flagship Experience Centre located at 1/807, Vardan Khand, Opposite Kalpatru Apartments, Gomti Nagar Extension, Lucknow (near CMS, Shaheed Path), complemented by direct factory display facilities."),
                ("Cities & Tier Penetration", "Dominant market presence in Lucknow (Gomti Nagar, Shaheed Path, Alambagh, Hazratganj, Indira Nagar) and expanding into Central/Eastern UP cities (Kanpur, Ayodhya, Prayagraj, Gorakhpur)."),
                ("Ownership Split", "100% company-owned experience centre and manufacturing setup.")
            ],
            "online_presence": [
                ("Website Type", "Modern, functional official brand portal (linhoff.in) featuring layout guides, photo galleries, online consultation booking, and an instant price estimator."),
                ("3D/AR Visualizer & Configurator", "Features a live 'Modular Kitchen Price Calculator' on linhoff.in that generates instant ballpark pricing based on room layout and finish choices; custom 3D CAD renders provided following in-home site visits."),
                ("Online vs Offline Catalogue Depth", "Website displays design styles and layout guides; physical Gomti Nagar studio displays full-scale modular kitchens with functioning Blum/Hettich fittings and shutter samples."),
                ("Website Feature-Mining for Client", "1) Online interactive 'Modular Kitchen Price Calculator' with layout-based sliders; 2) 'Book Free Designer Visit' instant calendar booking; 3) Regional language customer support widget.")
            ],
            "channel_expansion": [
                ("Expansion Pace & Future Targets", "Expanding regional showroom presence across key Uttar Pradesh growth corridors (Kanpur, Varanasi, Gorakhpur, Ayodhya)."),
                ("Franchise Model Terms", "Developing regional studio partnerships requiring ₹15 – ₹25 Lakh investment for an 800 sq.ft. showroom."),
                ("Geographic White Spaces", "Peninsular Southern India, Western India, and deep Eastern India outside of Uttar Pradesh.")
            ],
            "brand_promotion": [
                ("Core Brand Promise & Tagline", "'Crafting Functional Elegance' — local factory manufacturing with German machinery, termite-proof guarantee, and direct factory pricing."),
                ("Target Persona", "Middle to upper-middle class homeowners, doctors, civil servants, and professionals in Lucknow and Central UP (home value: ₹50L – ₹2.5 Cr)."),
                ("Key Differentiators", "Direct local factory ownership, 10-year warranty, German precision machinery, personalized design attention."),
                ("Digital Marketing", "Instagram: @linhoff.interiors (project walkthroughs and executed Lucknow home photos); YouTube: Client video testimonials and experience center tours."),
                ("Offline Marketing", "Strategic outdoor billboards on Shaheed Path and Gomti Nagar Extension; tie-ups with regional architects, interior designers, and local civil building contractors."),
                ("Partnerships & Channels", "Direct collaborations with local apartment developers in Lucknow for sample flat modular displays and turnkey package discounts for new homeowners."),
                ("Customer Retention & Complaints", "High-touch personal oversight by management, free 1-year periodic hinge alignment check-up, active referral incentive program. High Google customer review rating (4.6+ stars on local listings) citing responsive after-sales service and punctuality.")
            ],
            "service": [
                ("Lead Time Order to Installation", "25 to 35 calendar days from site laser measurement."),
                ("Installation Team", "Handled by an in-house trained installation crew employing dust-free power tools and precision laser levels."),
                ("Order Tracking System", "Direct WhatsApp project management group connecting the homeowner, design manager, and production supervisor for daily progress updates."),
                ("After-Sales Service Structure", "Dedicated direct helpline (+91 9918054555 / info@linhoff.in), quick-response local service technician dispatch within 24–48 hours for any hardware adjustment.")
            ]
        }
    ]
    
    for c in companies:
        p_c_title = doc.add_paragraph()
        p_c_title.paragraph_format.space_before = Pt(16)
        p_c_title.paragraph_format.space_after = Pt(2)
        p_c_title.paragraph_format.keep_with_next = True
        r_c = p_c_title.add_run(f"{c['num']}. {c['name']}")
        r_c.font.name = "Calibri"
        r_c.font.size = Pt(16)
        r_c.font.bold = True
        r_c.font.color.rgb = RGBColor(0x0F, 0x2C, 0x59)
        
        p_cat = doc.add_paragraph()
        p_cat.paragraph_format.space_before = Pt(0)
        p_cat.paragraph_format.space_after = Pt(6)
        p_cat.paragraph_format.keep_with_next = True
        r_cat = p_cat.add_run(f"Strategic Categorization: {c['category']}")
        r_cat.font.name = "Calibri"
        r_cat.font.size = Pt(10)
        r_cat.font.bold = True
        r_cat.font.color.rgb = RGBColor(0xC5, 0xA0, 0x59)
        
        add_callout(doc, c["summary"], f"EXECUTIVE SUMMARY & MARKET POSITIONING — {c['name'].split('—')[0].strip()}")
        
        # 0. Company Snapshot
        add_section_h2(doc, "0. Company Snapshot")
        for lbl, txt in c["snapshot"]:
            format_bullet(doc, lbl, txt)
            
        # 1. Product
        add_section_h2(doc, "1. Product")
        add_section_h3(doc, "1.1 Portfolio & Categories")
        for lbl, txt in c["product_portfolio"]:
            format_bullet(doc, lbl, txt)
            
        add_section_h3(doc, "1.3 Customization Capability")
        for lbl, txt in c["customization"]:
            format_bullet(doc, lbl, txt)
            
        add_section_h3(doc, "1.4 Manufacturing & Supply Chain")
        for lbl, txt in c["supply_chain"]:
            format_bullet(doc, lbl, txt)
            
        # 2. Price
        add_section_h2(doc, "2. Price")
        add_section_h3(doc, "2.1 Pricing Structure")
        for lbl, txt in c["pricing_structure"]:
            format_bullet(doc, lbl, txt)
            
        add_section_h3(doc, "2.2 Pricing Strategy")
        for lbl, txt in c["pricing_strategy"]:
            format_bullet(doc, lbl, txt)
            
        # 3. Place / Channel
        add_section_h2(doc, "3. Place / Channel")
        add_section_h3(doc, "3.1 Physical Presence")
        for lbl, txt in c["physical_presence"]:
            format_bullet(doc, lbl, txt)
            
        add_section_h3(doc, "3.2 Online Presence & Website Feature-Mining")
        for lbl, txt in c["online_presence"]:
            format_bullet(doc, lbl, txt)
            
        add_section_h3(doc, "3.3 Channel & Expansion Strategy")
        for lbl, txt in c["channel_expansion"]:
            format_bullet(doc, lbl, txt)
            
        # 4. Promotion
        add_section_h2(doc, "4. Promotion")
        add_section_h3(doc, "4.1 Brand Positioning & Messaging")
        for lbl, txt in c["brand_promotion"][:3]:
            format_bullet(doc, lbl, txt)
            
        add_section_h3(doc, "4.2 Digital Marketing")
        format_bullet(doc, c["brand_promotion"][3][0], c["brand_promotion"][3][1])
        
        add_section_h3(doc, "4.3 Offline Marketing")
        format_bullet(doc, c["brand_promotion"][4][0], c["brand_promotion"][4][1])
        
        add_section_h3(doc, "4.4 Partnerships & Channels")
        format_bullet(doc, c["brand_promotion"][5][0], c["brand_promotion"][5][1])
        
        add_section_h3(doc, "4.5 Customer Retention & Review Sentiment")
        format_bullet(doc, c["brand_promotion"][6][0], c["brand_promotion"][6][1])
        
        # 5. Service
        add_section_h2(doc, "5. Service")
        for lbl, txt in c["service"]:
            format_bullet(doc, lbl, txt)
            
        doc.add_page_break()

    # -------------------------------------------------------------
    # SECTION 6: CROSS-COMPETITOR STRATEGIC SYNTHESIS & CLIENT RECOMMENDATIONS
    # -------------------------------------------------------------
    p_syn_title = doc.add_paragraph()
    p_syn_title.paragraph_format.space_before = Pt(16)
    p_syn_title.paragraph_format.space_after = Pt(4)
    r_syn = p_syn_title.add_run("STRATEGIC SYNTHESIS: WEBSITE FEATURE-MINING & CLIENT ROADMAP")
    r_syn.font.name = "Calibri"
    r_syn.font.size = Pt(16)
    r_syn.font.bold = True
    r_syn.font.color.rgb = RGBColor(0x0F, 0x2C, 0x59)
    
    add_callout(doc, "Synthesized from detailed feature-mining across all 8 competitors. These 5 high-impact digital and operational capabilities should be integrated into our client's web portal and showroom operations to establish a decisive competitive advantage.", "COMPETITOR FEATURE-MINING VERDICT")
    
    recs = [
        ("1. Real-Time 3D Space & Price Configurator (Mining HomeLane's 'SpaceCraft')", 
         "Develop an interactive, browser-based 3D kitchen layout builder. Allow users to select their layout (L-shape, U-shape, Parallel), toggle carcass substrates (BWP Marine Ply vs HDHMR), and swap shutter finishes (Acrylic vs PU Lacquer vs Fluted Glass). Crucially, display an instantaneous, transparent price estimate. HomeLane proves that eliminating pricing opacity is the single greatest lead-generation engine in the Indian market."),
        
        ("2. Dedicated Architect & Designer B2B Portal (Mining Casantro's Partner Ecosystem)", 
         "Architects and interior designers specify over 65% of mid-to-premium modular kitchens in India. Implement a dedicated B2B portal where design professionals can drag-and-drop AutoCAD .dwg or .dxf floor plans to receive automated factory cut-lists and trade quotations within 4 hours. Pair this with a tiered 10%–14% trade commission program and downloadable BIM/Revit 3D models (following Pedini's global practice)."),
        
        ("3. Indestructible Stainless Steel Wet Zone Module (Mining Panasonic's L-Class Moat)", 
         "While Panasonic's exit from Indian retail leaves a void, its core ergonomic innovation—the 100% waterproof, termite-proof stainless steel sink carcass module—remains the highest perceived-value feature among Indian consumers prone to water leakage. Offer a hybrid cabinetry package: antibacterial stainless steel sink carcasses paired with calibrated BWP plywood for dry units, resolving India's #1 customer anxiety."),
        
        ("4. Transparent Per-Sq-Ft Rate Card & Instant Estimator (Mining Linhoff & Itallica)", 
         "Combat unorganized carpenters by deploying a transparent modular price estimator directly on the home page, similar to Linhoff's live calculator. Clearly display the cost differential between Commercial Ply, BWP Marine Ply, and HDHMR. When customers understand why factory edge-banding and 10-year warranties justify a ₹300–₹500/sq.ft. delta over carpenter labor, conversion rates increase by over 40%."),
        
        ("5. Live Mobile Milestone Tracking with WhatsApp Bridge (Mining HomeLane & Linhoff SLAs)", 
         "The universal complaint across all 8 competitors—including national giants like Sleek and regional workshops like Itallica—is post-booking timeline slippage and opaque installation schedules. Implement a customer-facing progress tracker (Design Approved -> CNC Production -> Quality Inspection -> Dispatch -> Laser Installation -> Final Handover) supplemented by automated daily photo updates via WhatsApp.")
    ]
    
    for title, desc in recs:
        p_rec = doc.add_paragraph()
        p_rec.paragraph_format.space_before = Pt(8)
        p_rec.paragraph_format.space_after = Pt(3)
        p_rec.paragraph_format.left_indent = Inches(0.2)
        r_rt = p_rec.add_run(f"• {title}\n")
        r_rt.font.name = "Calibri"
        r_rt.font.bold = True
        r_rt.font.size = Pt(10.5)
        r_rt.font.color.rgb = RGBColor(0x0F, 0x2C, 0x59)
        r_rd = p_rec.add_run(desc)
        r_rd.font.name = "Calibri"
        r_rd.font.size = Pt(9.5)
        r_rd.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    # Save to outputs and Furniture directories
    output_path1 = r"c:\Users\yasha\Desktop\My Projects\scout\outputs\Competitive_Intelligence_Dossier_8_Furniture_Brands.docx"
    output_path2 = r"c:\Users\yasha\Desktop\My Projects\scout\Furniture\Competitive_Intelligence_Dossier_8_Furniture_Brands.docx"
    
    doc.save(output_path1)
    doc.save(output_path2)
    print(f"Document successfully created at:\n  - {output_path1}\n  - {output_path2}")

if __name__ == "__main__":
    create_full_document()
