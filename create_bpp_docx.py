import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_color):
    """Sets background color of a table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets cell padding."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_document():
    doc = docx.Document()
    
    # Page Setup - Margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
    # Styles Setup
    styles = doc.styles
    normal_style = styles['Normal']
    normal_style.font.name = 'Calibri'
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    
    # Colors
    PRIMARY_CYAN = RGBColor(0x00, 0x80, 0x99)
    SECONDARY_BLUE = RGBColor(0x00, 0x40, 0x80)
    DARK_TEXT = RGBColor(0x11, 0x18, 0x27)
    MUTED_TEXT = RGBColor(0x4B, 0x55, 0x63)
    BG_LIGHT_CYAN = "E6F7F9"
    BG_HEADER = "005C70"
    
    # --- TITLE / COVER BLOCK ---
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    run_title = title_p.add_run("APEXROVER: AUTONOMOUS CAMPUS LOGISTICS")
    run_title.font.name = 'Arial'
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = PRIMARY_CYAN
    
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(18)
    run_sub = sub_p.add_run("Formula Student Electric Motor Car Component Commercialization Plan\nFORMULA BHARAT STATIC EVENT — BUSINESS PLAN PRESENTATION (BPP)")
    run_sub.font.size = Pt(12)
    run_sub.font.bold = True
    run_sub.font.color.rgb = SECONDARY_BLUE
    
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    
    # --- EXECUTIVE SUMMARY CALLOUT BOX ---
    summary_table = doc.add_table(rows=1, cols=1)
    summary_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = summary_table.cell(0, 0)
    set_cell_background(cell, BG_LIGHT_CYAN)
    set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run("EXECUTIVE SUMMARY")
    r.font.bold = True
    r.font.color.rgb = PRIMARY_CYAN
    r.font.size = Pt(12)
    
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    r2 = p2.add_run(
        "Urban last-mile delivery accounts for over 53% of total logistics costs. In Indian university campuses, gated residential societies, and IT parks, "
        "commercial riders are prohibited past security gates, forcing residents to walk up to 1.5 km to collect parcels.\n\n"
        "ApexRover is a Level-4 autonomous, electric, all-terrain delivery robot built specifically for enclosed private campuses. "
        "By directly transferring custom Formula Student EV racecar technology—specifically our Modular Battery Management System (BMS), Dual-Motor Inverter/Drivetrain, "
        "Composite Monocoque Tooling, and Double-Wishbone Suspension—we reduce bot build CapEx by 42% compared to commercial competitors, achieving an industry-leading payback period of <9 months."
    )
    r2.font.size = Pt(10.5)
    r2.font.color.rgb = DARK_TEXT
    
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    # Function for Section Headings
    def add_section_heading(title_text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(title_text)
        r.font.name = 'Arial'
        r.font.size = Pt(15)
        r.font.bold = True
        r.font.color.rgb = PRIMARY_CYAN
        return h

    # --- SECTION 1 ---
    add_section_heading("1. Racecar to Commercial Bot Component Transfer Matrix")
    
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    p.add_run("Formula Bharat judges evaluate how effectively racecar engineering transfers into a viable commercial model. The matrix below demonstrates our hardware transition:")
    
    table1 = doc.add_table(rows=7, cols=3)
    table1.alignment = WD_TABLE_ALIGNMENT.CENTER
    table1.autofit = False
    
    col_widths = [Inches(2.0), Inches(2.2), Inches(2.6)]
    headers = ["Formula Student EV Component", "Adapted Delivery Bot Component", "Commercial Advantage & Unfair Moat"]
    
    # Format Table Header
    hdr_cells = table1.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].width = col_widths[i]
        set_cell_background(hdr_cells[i], BG_HEADER)
        set_cell_margins(hdr_cells[i], top=120, bottom=120, left=150, right=150)
        p = hdr_cells[i].paragraphs[0]
        r = p.add_run(title)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        r.font.size = Pt(10)
        
    matrix_data = [
        ("Custom 300V LiFePO4 / NMC Battery Pack & Smart BMS", "Scaled-down 48V Swappable Battery Module", "Cell-level thermal monitoring; 30-sec hot swap provides 24/7 fleet uptime without tethered charging delays."),
        ("Custom Dual-Motor Inverter & Differential Vectoring", "Dual-Motor Brushless DC Planetary Drivetrain", "96% energy conversion efficiency; climbs 25° slopes, speedbumps, and 15cm sidewalk curbs easily."),
        ("CAN-Bus Telemetry & High-Speed Logging Unit", "Fleet Telematics & IoT Edge Gateway (4G/5G)", "Real-time battery health diagnostics, remote compartment lock triggers, and live cloud telemetry."),
        ("Carbon/Glass Composite Monocoque Tooling", "IP67 Water-Tight Composite Cargo Shell", "Cuts body tooling CapEx by 65%; vandal-proof electromagnetic dual locking compartments."),
        ("Double-Wishbone Independent Suspension", "Independent Rocker-Bogie All-Terrain Suspension", "Prevents liquid spills and damage to fragile parcels (coffee, glassware, electronic items) over uneven paths."),
        ("Autonomous Sensor Stack (LiDAR, Cameras)", "Level-4 ROS2 Vision-SLAM Navigation System", "Multi-modal perception for dynamic pedestrian detection, speedbump handling, and indoor-outdoor navigation.")
    ]
    
    for row_idx, data_tuple in enumerate(matrix_data, start=1):
        row_cells = table1.rows[row_idx].cells
        bg = "F9FAFB" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(data_tuple):
            row_cells[col_idx].width = col_widths[col_idx]
            set_cell_background(row_cells[col_idx], bg)
            set_cell_margins(row_cells[col_idx], top=100, bottom=100, left=120, right=120)
            p = row_cells[col_idx].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text)
            r.font.size = Pt(9.5)
            if col_idx == 0:
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # --- SECTION 2 ---
    add_section_heading("2. Foundational Market Research (TAM / SAM / SOM)")
    
    p = doc.add_paragraph()
    p.add_run("Market Sizing Breakdown:").font.bold = True
    
    bullets = [
        ("Total Addressable Market (TAM): ", "Global Autonomous Last-Mile Delivery Market projected to reach $16.5 Billion USD by 2032 (22.4% CAGR)."),
        ("Serviceable Available Market (SAM): ", "Indian Campus & Gated Community Last-Mile Market valued at ₹3,200 Crore ($385M USD) across 1,200+ universities, 8,500+ premium residential complexes, and 450+ IT parks."),
        ("Serviceable Obtainable Market (SOM): ", "Phase 1 target of 350 deployed bots across 45 Universities and 25 Tech Parks generating ₹28.5 Crore ARR by Year 3.")
    ]
    for b_title, b_desc in bullets:
        bp = doc.add_paragraph(style='List Bullet')
        bp.paragraph_format.space_after = Pt(3)
        r1 = bp.add_run(b_title)
        r1.font.bold = True
        r1.font.color.rgb = SECONDARY_BLUE
        r2 = bp.add_run(b_desc)
        r2.font.size = Pt(10.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # --- SECTION 3 ---
    add_section_heading("3. Competitor Analysis & Technical Moat")
    
    table2 = doc.add_table(rows=5, cols=4)
    table2.alignment = WD_TABLE_ALIGNMENT.CENTER
    table2.autofit = False
    
    col_w2 = [Inches(1.7), Inches(1.8), Inches(1.7), Inches(1.6)]
    headers2 = ["Metric / Feature", "ApexRover (Our Model)", "Ottonomy.ai", "Starship Technologies"]
    
    for i, title in enumerate(headers2):
        table2.rows[0].cells[i].width = col_w2[i]
        set_cell_background(table2.rows[0].cells[i], BG_HEADER)
        set_cell_margins(table2.rows[0].cells[i], top=120, bottom=120, left=120, right=120)
        p = table2.rows[0].cells[i].paragraphs[0]
        r = p.add_run(title)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        r.font.size = Pt(9.5)
        
    comp_data = [
        ("CapEx Build Cost", "₹1.80 Lakh ($2,150)", "₹6.50 Lakh ($7,800)", "₹8.20 Lakh ($9,800)"),
        ("Target Infrastructure", "Indian Potholes & 15cm Curbs", "Airports & Indoor Retail", "Smooth US Walkways"),
        ("Per Delivery Cost", "₹8 – ₹12", "₹35 – ₹50", "$1.99 – $3.49"),
        ("Battery Uptime", "30-Sec Hot Swap (24/7)", "Tethered Plug Charging", "Tethered Plug Charging")
    ]
    
    for r_idx, tuple_d in enumerate(comp_data, start=1):
        row_c = table2.rows[r_idx].cells
        bg = "F9FAFB" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val_t in enumerate(tuple_d):
            row_c[c_idx].width = col_w2[c_idx]
            set_cell_background(row_c[c_idx], bg)
            set_cell_margins(row_c[c_idx], top=100, bottom=100, left=100, right=100)
            p = row_c[c_idx].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val_t)
            r.font.size = Pt(9)
            if c_idx == 1:
                r.font.bold = True
                r.font.color.rgb = PRIMARY_CYAN

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # --- SECTION 4 ---
    add_section_heading("4. Government Subsidies, Grants & Legal Framework")
    
    subsidies = [
        ("Startup India Seed Fund Scheme (SISFS): ", "Grants up to ₹20 Lakhs for prototype validation + ₹50 Lakhs convertible debt via recognized IIT/BITS incubation cells."),
        ("MeitY TIDE 2.0 & DST NIDHI PRAYAS: ", "Direct financial support up to ₹18 Lakhs for deep-tech hardware startups combining AI and EV robotics."),
        ("Low-Speed EV Exemption (<6 km/h): ", "Programmed to operate at walking pace (6 km/h) on pedestrian paths inside private boundaries, exempting the bot from public CMV road licensing requirements."),
        ("DPDP Act 2023 Data Privacy Compliance: ", "Onboard edge AI redacts facial features and vehicle license plates in real-time before streaming video telemetry to cloud servers.")
    ]
    for stitle, sdesc in subsidies:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(4)
        r1 = p.add_run(stitle)
        r1.font.bold = True
        r1.font.color.rgb = SECONDARY_BLUE
        r2 = p.add_run(sdesc)
        r2.font.size = Pt(10)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # --- SECTION 5 ---
    add_section_heading("5. Financial Model, Unit Economics & 3-Year P&L")
    
    p = doc.add_paragraph()
    p.add_run("Unit Economics Summary (Per Delivery Bot):").font.bold = True
    
    fin_bullets = [
        ("Total Build CapEx: ", "₹1,80,000 ($2,150 USD) utilizing in-house Formula Student tooling and component design."),
        ("Monthly Gross Revenue: ", "₹26,000 (₹8,000 B2B canteen subscription + ₹10,500 delivery micro-fees + ₹7,500 on-bot ad wraps)."),
        ("Monthly OpEx: ", "₹5,800 (4G/5G connectivity, cloud hosting, battery electricity, maintenance allowance)."),
        ("Net Monthly EBITDA: ", "₹20,200 ($242 USD) yielding an estimated Payback Period of ~8.9 Months.")
    ]
    for ft, fd in fin_bullets:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        r1 = p.add_run(ft)
        r1.font.bold = True
        r2 = p.add_run(fd)
        r2.font.size = Pt(10)

    p_table_title = doc.add_paragraph()
    p_table_title.paragraph_format.space_before = Pt(8)
    p_table_title.paragraph_format.space_after = Pt(4)
    p_table_title.add_run("3-Year Financial Forecast (₹ INR)").font.bold = True

    table3 = doc.add_table(rows=4, cols=4)
    table3.alignment = WD_TABLE_ALIGNMENT.CENTER
    table3.autofit = False
    
    col_w3 = [Inches(2.2), Inches(1.5), Inches(1.5), Inches(1.6)]
    headers3 = ["Financial Metric", "Year 1 (15 Bots)", "Year 2 (120 Bots)", "Year 3 (500 Bots)"]
    
    for i, title in enumerate(headers3):
        table3.rows[0].cells[i].width = col_w3[i]
        set_cell_background(table3.rows[0].cells[i], BG_HEADER)
        set_cell_margins(table3.rows[0].cells[i], top=100, bottom=100, left=100, right=100)
        p = table3.rows[0].cells[i].paragraphs[0]
        r = p.add_run(title)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        r.font.size = Pt(9.5)
        
    pnl_data = [
        ("Gross Revenue", "₹46.8 Lakhs", "₹3.74 Crore", "₹15.60 Crore"),
        ("CapEx (Bot Manufacturing)", "₹27.0 Lakhs", "₹1.92 Crore", "₹6.50 Crore"),
        ("Net EBITDA Margin", "₹9.4 Lakhs (20.1%)", "₹98.5 Lakhs (26.3%)", "₹5.62 Crore (36.0%)")
    ]
    
    for r_idx, tuple_p in enumerate(pnl_data, start=1):
        row_c = table3.rows[r_idx].cells
        bg = "F9FAFB" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val_p in enumerate(tuple_p):
            row_c[c_idx].width = col_w3[c_idx]
            set_cell_background(row_c[c_idx], bg)
            set_cell_margins(row_c[c_idx], top=90, bottom=90, left=100, right=100)
            p = row_c[c_idx].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(val_p)
            r.font.size = Pt(9.5)
            if c_idx == 0:
                r.font.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # --- SECTION 6 ---
    add_section_heading("6. Formula Bharat Judges Q&A Simulator")
    
    qa_list = [
        ("Q1: How can your team manufacture this bot at ₹1.80 Lakh when commercial competitors spend $7,000+?",
         "Answer: Competitors pay high commercial markups for off-the-shelf industrial BMS, motor drives, and outsourced composite moulding. We leverage our Formula Student team's existing composite vacuum bagging infrastructure, component vendor links, and in-house designed BMS PCB boards, cutting non-recurring R&D and markup costs by 65%."),
        ("Q2: What prevents theft or vandalism when operating unattended inside campuses?",
         "Answer: The bot features active GPS tracking, dual-compartment electromagnetic locks, anti-tamper acoustic sirens, and live cellular telemetry. If lifted or moved unnaturally, edge IMU sensors trigger high-decibel alarms and broadcast live location and camera feeds to campus security and our teleoperation dashboard."),
        ("Q3: How do you handle Indian sidewalk obstacles, speedbumps, and uneven paths?",
         "Answer: Our bot runs on an independent double-wishbone suspension system directly derived from our racecar. Coupled with a 15cm ground clearance, planetary gear motors, and dynamic local path planning (ROS2 TEB planner), it easily climbs 15cm curbs and speedbreakers while protecting fragile food parcels."),
        ("Q4: How do you maintain fleet uptime during peak meal hours without long charging delays?",
         "Answer: We utilize hot-swappable 48V battery modules equipped with our custom EV racecar BMS. Instead of waiting 2 hours for tethered charging, campus operators swap depleted packs with pre-charged modules in under 30 seconds, maintaining 98%+ fleet uptime during peak meal hours.")
    ]
    
    for q_text, a_text in qa_list:
        qp = doc.add_paragraph()
        qp.paragraph_format.space_before = Pt(6)
        qp.paragraph_format.space_after = Pt(2)
        r_q = qp.add_run(q_text)
        r_q.font.bold = True
        r_q.font.color.rgb = SECONDARY_BLUE
        
        ap = doc.add_paragraph()
        ap.paragraph_format.space_after = Pt(8)
        r_a = ap.add_run(a_text)
        r_a.font.size = Pt(10)
        r_a.font.color.rgb = DARK_TEXT

    # --- FOOTER ---
    section = doc.sections[0]
    footer = section.footer
    f_p = footer.paragraphs[0]
    f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    f_run = f_p.add_run("ApexRover SAE Formula Student EV BPP Document | Page ")
    f_run.font.size = Pt(9)
    f_run.font.color.rgb = MUTED_TEXT

    doc.save("c:\\Users\\yasha\\Desktop\\scout\\ApexRover_Formula_Bharat_BPP_Report.docx")
    print("Successfully generated Word document: c:\\Users\\yasha\\Desktop\\scout\\ApexRover_Formula_Bharat_BPP_Report.docx")

if __name__ == "__main__":
    create_document()
