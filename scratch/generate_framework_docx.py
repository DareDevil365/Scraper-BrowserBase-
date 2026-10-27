import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pathlib import Path

# --- XML Helper Functions for Styling ---
def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_borders(cell, color="E2E8F0", sz="4", val="single"):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for border_name in ['top', 'left', 'bottom', 'right']:
        border = OxmlElement(f'w:{border_name}')
        border.set(qn('w:val'), val)
        border.set(qn('w:sz'), sz)
        border.set(qn('w:space'), '0')
        border.set(qn('w:color'), color)
        tcBorders.append(border)
    tcPr.append(tcBorders)

def make_cell_header(cell, text, hex_color="1E293B"):
    set_cell_background(cell, hex_color)
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    set_cell_borders(cell, color="475569")
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    
    run = p.add_run(text)
    run.font.name = 'Arial'
    run.font.size = Pt(10)
    run.font.bold = True
    run.font.color.rgb = RGBColor(255, 255, 255)

def make_cell_data(cell, text, bg_color=None, is_bold=False, align_right=False):
    if bg_color:
        set_cell_background(cell, bg_color)
    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
    set_cell_borders(cell, color="E2E8F0")
    cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    
    p = cell.paragraphs[0]
    if align_right:
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    else:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    
    lines = text.split('\n')
    for idx, line in enumerate(lines):
        if idx > 0:
            p.add_run('\n')
        run = p.add_run(line)
        run.font.name = 'Arial'
        run.font.size = Pt(9.5)
        run.font.bold = is_bold
        run.font.color.rgb = RGBColor(15, 23, 42)

# --- Main Document Generation ---
def generate_document():
    doc = Document()
    
    # Configure margins (1 inch on all sides)
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    # Typography Styles
    def add_title(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(24)
        run.font.bold = True
        run.font.color.rgb = RGBColor(30, 41, 59) # Slate 800
        return p

    def add_subtitle(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(24)
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(100, 116, 139) # Slate 500
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(24)
        p.paragraph_format.space_after = Pt(10)
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(16)
        run.font.bold = True
        run.font.color.rgb = RGBColor(30, 41, 59) # Slate 800
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(18)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(12.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(16, 185, 129) # Emerald/Teal 500
        return p

    def add_body(text, bold=False, italic=False, before=0, after=6):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(10)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = RGBColor(15, 23, 42) # Slate 900
        return p
        
    def add_bullet(text, level=0, bold_prefix=""):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.left_indent = Inches(0.25 * (level + 1))
        
        if bold_prefix:
            run_p = p.add_run(bold_prefix)
            run_p.font.name = 'Arial'
            run_p.font.size = Pt(10)
            run_p.font.bold = True
            run_p.font.color.rgb = RGBColor(15, 23, 42)
            
        run = p.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(15, 23, 42)
        return p

    # --- Content Generation ---
    add_title("Silaai Escrow-Logistics & Dispute Management Framework")
    add_subtitle("Comprehensive Operational Blueprint: Product Transactions, Non-Escrow Operations, and Dispute Resolution")
    
    # 1. Executive Summary
    add_h1("1. Executive Summary: The Escrow-Logistics Framework")
    add_body("Silaai operates a hybrid marketplace model, incorporating standard retail apparel sales (B2C Products), raw material sourcing (B2B Fabrics & Trims), and custom tailoring/stitching services (B2C Services). To manage financial trust, reduce transaction friction, and eliminate operational overhead, Silaai implements an API-driven Escrow-like Split Payout Framework utilizing RBI-regulated Payment Aggregators (PG/PAs) integrated with real-time Third-Party Logistics (3PL) webhooks.")
    add_body("The matrix below illustrates the operational components of Silaai's escrow-logistics framework across its primary transaction classes:")
    
    # Table 1: Framework Core Components Matrix
    table1 = doc.add_table(rows=5, cols=5)
    table1.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    headers1 = ["Operational Vector", "Product Transactions (B2C/B2B)", "Service Transactions (Tailoring)", "Non-Escrow Transactions", "Key Recommendations"]
    for i, name in enumerate(headers1):
        make_cell_header(table1.cell(0, i), name)
        
    row_data1 = [
        ["Escrow Mechanism", 
         "API Split-and-Hold: Funds are held in a PG Nodal escrow account and split upon 3PL delivery confirmation.", 
         "Iterative Milestone Release: Funds are held through alteration loops, releasing only after final customer sign-off.", 
         "Direct Settlement (T+2): Instant bypass of escrow for pre-vetted entities, subscriptions, or ultra-low-value catalog items.", 
         "Integrate Razorpay Route or Cashfree Split to programmatically execute transaction-level locks and releases."],
        ["Logistics Integration", 
         "3PL Webhook Synchronization: Real-time carrier scans (dispatch, out-for-delivery, delivery) dictate escrow status.", 
         "Dual-Leg Logistics: Tracks fabric pickup (reverse) and finished garment delivery (forward) through unified AWB tracking.", 
         "Standard 3PL Manifests: Traditional tracking without API triggers or milestone locks on payment releases.", 
         "Implement Shiprocket API to auto-sync 3PL states with payment status, eliminating seller self-declaration."],
        ["COD Management", 
         "COD Ceiling & Verification: Orders capped at ₹2,000. WhatsApp OTP verification required. 3PL acts as temporary escrow.", 
         "Prepaid Only: No Cash-on-Delivery supported. 100% digital prepayment required due to tailor labor and fabric cutting.", 
         "Direct Cash Collection: For non-core physical events (e.g., designer popup stalls or local boutique pickups).", 
         "Mandate Prepaid Partial Deposits (₹150) on B2C COD orders to reduce Return-to-Origin (RTO) shipping losses."],
        ["Dispute Handling", 
         "Return Verification Window: 24-hour merchant verification post-reverse delivery before refund execution.", 
         "Rework Limits: Limit to 2 alteration iterations before triggering platform human arbitration.", 
         "Silaai Trust Fund Cover: Immediate refunds for low-value catalog items funded by a 0.5% transaction levy.", 
         "Establish an Evidence-Based Adjudication Portal requiring video proofs for B2B bulk and service disputes."]
    ]
    
    for row_idx, rdata in enumerate(row_data1, start=1):
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(rdata):
            is_bold = (col_idx == 0)
            make_cell_data(table1.cell(row_idx, col_idx), text, bg_color=bg, is_bold=is_bold)
            
    # Set widths roughly for columns
    widths1 = [Inches(1.2), Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.8)]
    for row in table1.rows:
        for idx, width in enumerate(widths1):
            row.cells[idx].width = width

    # 2. Product Transaction Flowchart
    doc.add_page_break()
    add_h1("2. Product Transaction Flowchart")
    add_body("The product transaction flow covers the end-to-end journey of a product order (standard apparel catalog, B2B wholesale fabrics, or materials) from initial purchase to final settlement. It details the operational paths for B2C Digital Prepaid, B2B Bulk Prepaid, and Cash-on-Delivery (COD) transactions.")
    
    add_h2("Operational Step-by-Step Logic:")
    add_bullet("Order Placement: Buyer places an order for a physical product.", level=0, bold_prefix="Step 1: ")
    add_bullet("Payment Route Decision:", level=0, bold_prefix="Step 2: ")
    add_bullet("For B2C Digital Prepaid, the platform locks 100% of the funds in the PG Nodal Escrow account.", level=1, bold_prefix="A. ")
    add_bullet("For B2B Bulk Prepaid, the platform locks 100% of the funds in the PG Nodal Escrow account.", level=1, bold_prefix="B. ")
    add_bullet("For Cash-on-Delivery (COD), the system validates if the order value is <= ₹2,000. If exceeded, COD is blocked. If valid, WhatsApp OTP verification is sent. Once verified, Silaai logs a virtual escrow ledger liability.", level=1, bold_prefix="C. ")
    add_bullet("Dispatch: Supplier packs and dispatches the fabric/materials via 3PL carrier.", level=0, bold_prefix="Step 3: ")
    add_bullet("Logistics Scan: The 3PL carrier scans the package, firing a PICKED_UP webhook. The status shifts to IN_TRANSIT.", level=0, bold_prefix="Step 4: ")
    add_bullet("Delivery Event Routing:", level=0, bold_prefix="Step 5: ")
    add_bullet("If the delivery fails or is rejected, the 3PL initiates Return to Origin (RTO) flow.", level=1, bold_prefix="A. ")
    add_bullet("If the delivery succeeds, the 3PL fires a DELIVERED webhook, initiating class-specific timelines.", level=1, bold_prefix="B. ")
    add_bullet("Class-Specific Delivery Actions:", level=0, bold_prefix="Step 6: ")
    add_bullet("B2C Prepaid starts a 7-day return window. If it expires without dispute, 100% of the payout is released to the seller.", level=1, bold_prefix="A. ")
    add_bullet("B2B Bulk triggers an immediate 50% release of the supplier's net payout to cover cost of goods sold (COGS), starting a 5-day inspection window. On day 6, the remaining 50% is released.", level=1, bold_prefix="B. ")
    add_bullet("COD leads to cash/UPI collection at the doorstep. The 3PL holds the cash on a T+5 reconciliation timeline, starting a 7-day return window. Funds are released to the seller's wallet after 7 days.", level=1, bold_prefix="C. ")
    add_bullet("Dispute Handling: If a dispute is raised in B2C, B2B, or COD flows, the funds are immediately frozen and reverse logistics are scheduled for platform arbitration.", level=0, bold_prefix="Step 7: ")

    # 3. Product Transaction Escrow Trigger Table
    add_h1("3. Product Transaction Escrow Trigger Table")
    add_body("This matrix provides a milestone-by-milestone breakdown of the financial triggers, release percentages, auto-release timers, risk profiles, and business logic governing product transactions on Silaai.")
    
    table2 = doc.add_table(rows=10, cols=8)
    table2.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    headers2 = ["Milestone ID", "Trigger Event / Name", "System Status", "Escrow Action", "Release % (to Seller)", "Auto-Release / Timer Rules", "Primary Risks & Safeguards", "Strategic Rationale / Why"]
    for i, name in enumerate(headers2):
        make_cell_header(table2.cell(0, i), name)
        
    row_data2 = [
        ["M-PROD-01", "Payment Authorized (Prepaid Checkout)", "LOCKED", 
         "PG collects and holds 100% of order value (including tax, delivery fees, and platform commission) in Nodal Account.", 
         "0%", "N/A (Funds held until delivery events).", 
         "Risk: Customer payment fraud or chargebacks.\nSafeguard: 3D-Secure 2.0 verification mandatory; UPI auto-validation.", 
         "Ensures full buyer commitment before the seller incurs fabric packaging or material procurement costs."],
        
        ["M-PROD-02", "COD Order Verified (Cash-on-Delivery)", "COD_PENDING_DISPATCH", 
         "Platform logs a virtual ledger liability of 100% of order value. No physical escrow exists yet.", 
         "0%", "12-Hour Cancellation Window: If WhatsApp OTP is not verified, the order is cancelled automatically.", 
         "Risk: Fake address, bogus buyers, high RTO rates.\nSafeguard: Address verification via GoKwik API; risk-profiling historical cancel rates.", 
         "Caps early shipping cost liabilities on Silaai by vetting buyer intent prior to warehouse dispatch."],
        
        ["M-PROD-03", "Logistics Dispatch Scan", "IN_TRANSIT", 
         "3PL carrier scans AWB at pickup. Webhook fires PICKED_UP.", 
         "0% (Exception: 70% for Platinum Tier sellers).", "N/A (Funds remain locked during shipping transit).", 
         "Risk: Seller shipping empty boxes or incorrect goods.\nSafeguard: Direct weight-matching at carrier hub; transit insurance covers loss.", 
         "Keeps 100% of standard seller payouts locked until delivery to prevent merchant fraud, while providing liquidity to pre-vetted top sellers."],
        
        ["M-PROD-04a", "B2C Delivery Confirmation (Prepaid)", "DELIVERED_INSPECTION", 
         "3PL Webhook fires DELIVERED. Starts return countdown timer.", 
         "0%", "7-Day Return Expiry: Auto-advances to M-PROD-05 after 168 hours if no return ticket is created.", 
         "Risk: Late delivery disputes, transit damage.\nSafeguard: Photo proof-of-delivery (POD) uploaded by 3PL agent at doorstep.", 
         "Consumer rights require a standard return window. Seller payouts are delayed to ensure funds are available if a return is executed."],
        
        ["M-PROD-04b", "B2B Bulk Delivery Confirmation", "DELIVERED_INSPECTION", 
         "3PL Webhook fires DELIVERED. Starts B2B inspection countdown.", 
         "50% of Seller Net Payout", "5-Day Inspection Expiry: Remaining 50% is held for 120 hours.", 
         "Risk: Bulk fabric quantity shortages, dye lot mismatch.\nSafeguard: Mandating photo proof and fabric sample cuts from suppliers.", 
         "B2B textile merchants operate on low margins. Immediate 50% release covers COGS and shipping, while the remaining 50% protects buyer quality."],
        
        ["M-PROD-04c", "COD Delivery & Collection", "COD_COLLECTED", 
         "3PL agent collects cash/UPI. Webhook fires COD_COLLECTED. Silaai updates ledger.", 
         "0%", "7-Day Return Expiry: Auto-advances to M-PROD-05 after 168 hours post-collection.", 
         "Risk: Cash loss, 3PL remittance delay.\nSafeguard: 3PL carrier contract guarantees remittance within T+5 days of collection.", 
         "Physical cash must reconcile through the 3PL's pipeline. Hold prevents Silaai from advancing capital on un-reconciled COD collections."],
        
        ["M-PROD-05", "Inspection Approval / Window Expiry", "COMPLETED", 
         "Silaai triggers PG Split API to release funds. Commission and fees are settled.", 
         "100% of Seller Net Payout (or remaining 50% for B2B).", "Instant Release: Triggered immediately upon buyer clicking 'Approve' OR at window expiration.", 
         "Risk: Post-settlement chargeback claims.\nSafeguard: Buyer terms state that final release waives return rights.", 
         "Final release completes Silaai's escrow obligation. The transaction is marked closed, and the seller can withdraw funds."],
        
        ["M-PROD-06", "Dispute / Return Triggered", "DISPUTED_HOLD", 
         "Escrow balances are frozen. Reverse AWB is generated via 3PL.", 
         "0%", "N/A (Funds held indefinitely in dispute pool until resolved).", 
         "Risk: Buyer returning damaged, worn, or swapped clothes.\nSafeguard: Reverse pickup requires photo verification by the courier agent.", 
         "Halts all automatic payout schedules. Protects Silaai from losing cash while determining who holds liability for the defect or return."],
        
        ["M-PROD-07", "Reverse Delivery & Verification", "RTO_VERIFIED", 
         "3PL scans return delivery to supplier (RTO_DELIVERED).", 
         "0% to Seller. 100% Refund to Buyer (minus reverse shipping).", "24-Hour Verification Window: Auto-refunds buyer if the supplier does not object within 24 hours of return receipt.", 
         "Risk: Seller stalling refunds by claiming returned goods are damaged.\nSafeguard: Unboxing video proof required from the supplier to dispute a return.", 
         "Returns the buyer's funds once the seller has reclaimed their physical inventory, minus shipping fees (unless seller error is proven)."]
    ]
    
    for row_idx, rdata in enumerate(row_data2, start=1):
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(rdata):
            is_bold = (col_idx == 0)
            make_cell_data(table2.cell(row_idx, col_idx), text, bg_color=bg, is_bold=is_bold)
            
    # Set widths for Table 2
    widths2 = [Inches(0.8), Inches(1.1), Inches(1.1), Inches(1.2), Inches(0.9), Inches(1.0), Inches(1.4), Inches(1.5)]
    for row in table2.rows:
        for idx, width in enumerate(widths2):
            row.cells[idx].width = width

    # 4. Non-Escrow Transaction Flowchart
    doc.add_page_break()
    add_h1("4. Non-Escrow Transaction Flowchart")
    add_body("Silaai identifies low-risk and immediate-settlement transactions that bypass traditional escrow locks to maintain platform agility and reduce operational compliance costs.")
    
    add_h2("Decision Tree Routing Logic:")
    add_bullet("If the transaction is a Platform Subscription or Advertisement Fee, it routes directly to Operational Collection, bypassing the escrow ledger entirely.", level=0, bold_prefix="Path 1: ")
    add_bullet("If the transaction is for Digital Goods (CAD patterns or vector files):", level=0, bold_prefix="Path 2: ")
    add_bullet("If download is completed, the payment routes directly to the seller's account on a standard T+2 settlement cycle.", level=1, bold_prefix="A. ")
    add_bullet("If download is not completed or is custom, it routes to the standard escrow pool.", level=1, bold_prefix="B. ")
    add_bullet("If the transaction is for Physical Catalog Products:", level=0, bold_prefix="Path 3: ")
    add_bullet("If the order value is < ₹299 (low-value trims, buttons, embellishments), the system bypasses escrow holds for Direct T+2 Settlement.", level=1, bold_prefix="A. ")
    add_bullet("If the order value is >= ₹299, the system checks if the supplier is a pre-vetted Platinum Tier Seller. If yes, it routes to Dispatch-Released Settlement (70% on dispatch, 30% on delivery). If no, it routes to the standard escrow pool.", level=1, bold_prefix="B. ")

    # 5. Non-Escrow Classification Table
    add_h1("5. Non-Escrow Classification Table")
    add_body("This table details the categories of transactions on Silaai that bypass traditional escrow locks, detailing their financial structures, associated risks, platform safeguards, and phased pilot launch parameters.")
    
    table3 = doc.add_table(rows=5, cols=5)
    table3.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    headers3 = ["Transaction Category", "Alternative Payment Mechanism", "Associated Risks", "Platform Safeguards & Risk Mitigation", "Pilot-Launch Recommendation"]
    for i, name in enumerate(headers3):
        make_cell_header(table3.cell(0, i), name)
        
    row_data3 = [
        ["Platform Services\n(Silaai Pro Subscriptions, Designer Shop Advertising, Featured Banner Listings)", 
         "Direct Operational Collection: Funds bypass the nodal escrow ledger completely, routing directly to Silaai's operational current account via standard payment gateway capture.", 
         "Risks: Card chargebacks due to designer dissatisfaction with platform traffic/leads.", 
         "Safeguard: Strict non-refundable terms in Designer Service Level Agreements (SLAs).", 
         "Phase 1 Launch: Implement immediately. Direct collections are highly standardized and have zero escrow requirements."],
        
        ["Low-Value Catalog Items\n(Trims, buttons, zippers, sewing threads, needles, < ₹299)", 
         "Direct Settlement (T+2): Funds are routed to the seller's ledger and settled on the next standard banking payout cycle (T+2 days post-payment), bypassing delivery triggers.", 
         "Risks: High logistics return costs exceeding the item value; seller shipping defects.", 
         "Safeguard: Customers are refunded instantly without requiring physical returns. Platform recovers costs from a 0.5% Silaai Trust Levy on all sales.", 
         "Phase 1 Launch: Restrict to certified hobbyist stores. Limit total monthly low-value direct settlements to ₹5,000 per merchant."],
        
        ["Platinum Tier Suppliers\n(Top-rated fabric suppliers and high-volume apparel sellers)", 
         "Dispatch-Released Settlement: 70% of payout is released to the supplier immediately upon 3PL dispatch scan (IN_TRANSIT status). The remaining 30% is released 3 days post-delivery.", 
         "Risks: Supplier fraud (swapping bulk fabric during transit); platform liquidity defaults.", 
         "Safeguard: Mandatory ₹25,000 security deposit held by Silaai. Exclude merchants with >3% RTO/dispute rates.", 
         "Phase 2 Launch: Launch only after establishing automated 3PL tracking APIs. Maintain manual credit limits for participating sellers."],
        
        ["Digital Services\n(CAD sewing patterns, digital embroidery vector files, tech pack templates)", 
         "Direct Settlement (T+2): Payment routes directly to the designer's payout ledger. Funds are released on T+2 days post-checkout.", 
         "Risks: Pirated file distribution; corrupted digital files; buyer claiming non-download.", 
         "Safeguard: Integrated download trackers logs exact IPs and timestamps. File checksum validation on upload.", 
         "Phase 1 Launch: Supported from day one. Digital downloads have no logistics component, rendering traditional shipping escrow obsolete."]
    ]
    
    for row_idx, rdata in enumerate(row_data3, start=1):
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(rdata):
            is_bold = (col_idx == 0)
            make_cell_data(table3.cell(row_idx, col_idx), text, bg_color=bg, is_bold=is_bold)
            
    # Set widths for Table 3
    widths3 = [Inches(1.5), Inches(1.5), Inches(1.5), Inches(1.8), Inches(1.7)]
    for row in table3.rows:
        for idx, width in enumerate(widths3):
            row.cells[idx].width = width

    # 6. Dispute Resolution & Fund Handling
    doc.add_page_break()
    add_h1("6. Dispute Resolution & Fund Handling")
    
    add_h2("6.1 Fund Holding Structure")
    add_body("All disputed transaction funds are immediately flagged inside the platform's database and isolated in the Payment Aggregator’s Nodal/Escrow Account. Silaai invokes the 'on_hold' split API to freeze seller settlements on the disputed transaction. No platform commission or designer fee is settled. Disputed funds remain in the secure nodal escrow account until formal resolution, protecting Silaai from working capital defaults.")
    
    add_h2("6.2 Evidence-Based Adjudication & Resolution Rules")
    add_body("Disputes are adjudicated based on empirical evidence provided by the buyer, the seller, and the 3PL shipping log. Silaai enforces the following evidence criteria:")
    
    table4 = doc.add_table(rows=4, cols=5)
    table4.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    headers4 = ["Dispute Claim Class", "Required Evidence from Buyer", "Required Evidence from Seller", "3PL Verification Point", "Escalation Outcome / Resolution"]
    for i, name in enumerate(headers4):
        make_cell_header(table4.cell(0, i), name)
        
    row_data4 = [
        ["Item Not Received (INR)", 
         "System log showing non-delivery; customer declaration form.", 
         "Proof of Dispatch (manifest signed by courier representative).", 
         "Carrier GPS log at delivery coordinates; physical recipient signature.", 
         "If 3PL confirms delivery: Dispute is resolved in seller's favor; 100% payout released.\nIf 3PL confirms package lost: Silaai files transit claim; buyer is refunded 100%."],
        
        ["Damaged / Missing Items", 
         "Mandatory unboxing video showing the shipping label and contents; photos of damage.", 
         "Pre-dispatch packaging photos/videos showing weight measurements.", 
         "Volumetric package weight logged at origin hub vs. weight at delivery hub.", 
         "If origin weight matches delivery weight, but item is damaged: Seller packed defective goods or packaging failed. Resolve for buyer. 100% refund.\nIf weights differ by >15%: Transit pilferage. Platform covers refund; files claim with 3PL."],
        
        ["Significant Quality Defect\n(Fabric or Catalog Products)", 
         "Photos comparing catalog specifications vs. delivered product; material tests.", 
         "Quality Assurance (QA) sheet; fabric batch certificates.", 
         "N/A (Inspected by platform quality agents).", 
         "If discrepancy is verified: 100% refund. Seller pays for return logistics. Repeat offenses (>2) results in seller store suspension."]
    ]
    
    for row_idx, rdata in enumerate(row_data4, start=1):
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(rdata):
            is_bold = (col_idx == 0)
            make_cell_data(table4.cell(row_idx, col_idx), text, bg_color=bg, is_bold=is_bold)
            
    # Set widths for Table 4
    widths4 = [Inches(1.3), Inches(1.6), Inches(1.6), Inches(1.5), Inches(2.0)]
    for row in table4.rows:
        for idx, width in enumerate(widths4):
            row.cells[idx].width = width

    add_h2("6.3 Partial Release Payout Math")
    add_body("In scenarios where disputes involve partial order issues (e.g., partial quantity missing or minor minor errors), Silaai implements a split-payout resolution based on the formulas:")
    add_body("Buyer Refund = ((Missing Quantity / Ordered Quantity) * Item Cost) + Pro-Rata Shipping Adjustments", italic=True)
    add_body("Seller Release = Total Order Value - Buyer Refund - Silaai Platform Commission (5-15%)", italic=True)
    add_body("Example Case: A buyer orders 10 meters of premium silk fabric (total cost ₹5,000, shipping ₹300). Upon delivery, the buyer proves that only 8 meters were delivered (20% missing).")
    add_bullet("Buyer Refund Calculation: (0.20 * ₹5,000) + ₹0 (shipping not refunded) = ₹1,000.", level=0)
    add_bullet("Platform Fee Calculation: Silaai takes 5% on the delivered value (₹4,000) = ₹200.", level=0)
    add_bullet("Seller Release Calculation: ₹5,300 (total collected) - ₹1,000 (buyer refund) - ₹200 (platform fee) - ₹300 (shipping paid to 3PL) = ₹3,800.", level=0)

    add_h2("6.4 Card Chargeback Handling")
    add_bullet("System Lockdown: Silaai's ledger locks the corresponding order value upon receiving card network notification.", level=0)
    add_bullet("Seller Hold: If the seller has already been paid, Silaai places a temporary negative balance on the seller's wallet.", level=0)
    add_bullet("Evidence Submission: Silaai auto-compiles and submits 3PL logs, geocodes, and buyer agreement histories to the card network.", level=0)
    add_bullet("Arbitration Settlement: If resolved in merchant's favor, negative balance is lifted. If lost, Silaai absorbs the chargeback or bills it to the seller if seller fault was proven.", level=0)

    add_h2("6.5 Adjudication & Escalation Workflow")
    add_bullet("Level 1: Automated In-App Mediation (First 48 Hours) - Buyer files dispute. Seller has 48 hours to offer resolution (refund/replacement) or contest. Silence triggers auto-resolution in buyer's favor.", level=0)
    add_bullet("Level 2: Platform Operations Review (Next 72 Hours) - If contested, Silaai operations agent reviews evidence and issues binding decision in 3 business days.", level=0)
    add_bullet("Level 3: Executive Arbitration Panel (Escrow > ₹50,000) - For large B2B orders, an executive panel (CFO, Head of Logistics, Legal) makes a final, non-appealable decision within 5 days.", level=0)

    # 7. Phased Implementation Roadmap
    doc.add_page_break()
    add_h1("7. Phased Implementation Roadmap")
    add_body("Silaai's escrow and logistics automation framework is designed to evolve in three distinct phases, transitioning from manual oversight to automated systems.")
    
    table5 = doc.add_table(rows=6, cols=4)
    table5.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    headers5 = ["Operational Dimension", "Phase 1: Provider-Managed Logistics (Months 1-6)", "Phase 2: Integrated 3PL & API Sync (Months 7-12)", "Phase 3: Platform-Controlled Workflow (Month 13+)"]
    for i, name in enumerate(headers5):
        make_cell_header(table5.cell(0, i), name)
        
    row_data5 = [
        ["Logistics Model", 
         "Provider-Managed (Self-Ship): Sellers pack and choose couriers. Sellers upload receipt manifests manually to Silaai.", 
         "Integrated 3PL: Shipping managed through platform accounts (e.g., Shiprocket API). Shipping labels and AWBs generated on Silaai.", 
         "Full Platform Logistics: Silaai handles warehousing, pre-sorting, and physical hubs for quality inspection (StockX model)."],
        
        ["Escrow Automation Level", 
         "Semi-Automated: Escrow splits locked via API, but releases triggered manually by Silaai operations based on seller-uploaded delivery proof.", 
         "Fully Automated: Webhook listeners automatically detect DELIVERED status and schedule the release API call without human intervention.", 
         "Smart-Contract Ledger: Dynamic, real-time ledger settlement that instantly splits, routes, and releases funds as delivery conditions are met."],
        
        ["Average Payout Speed", 
         "T+15 Days (Post-Delivery): Long buffer to ensure manual return processing is complete and to prevent chargeback losses.", 
         "T+8 Days (Post-Delivery): Escrow splits automatically release on day 8 (immediately following the 7-day return window).", 
         "Instant to T+2 Days: Platinum sellers get paid immediately on dispatch; standard sellers get paid on T+1 day post-delivery."],
        
        ["Transition Criteria", 
         "Baseline Launch Stage.", 
         "• 100+ active sellers.\n• >2,000 monthly transactions.\n• Stable API integrations with Razorpay Route and Shiprocket.", 
         "• >15,000 monthly transactions.\n• Dispute rates below 1.5% of total orders.\n• Established cash reserves to fund Platinum seller fast-tracks."],
        
        ["COD Management", 
         "Manual Verification: Platform team manually calls or WhatsApps every COD customer to confirm intent before shipping.", 
         "Automated OTP/WhatsApp: GoKwik or WhatsApp business API auto-verifies COD placement. High-risk pincodes blocked.", 
         "Dynamic COD Profiling: AI model analyzes buyer's purchase history and restricts COD dynamically on an individual account basis."]
    ]
    
    for row_idx, rdata in enumerate(row_data5, start=1):
        bg = "F8FAFC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(rdata):
            is_bold = (col_idx == 0)
            make_cell_data(table5.cell(row_idx, col_idx), text, bg_color=bg, is_bold=is_bold)
            
    # Set widths for Table 5
    widths5 = [Inches(1.5), Inches(1.8), Inches(2.3), Inches(2.4)]
    for row in table5.rows:
        for idx, width in enumerate(widths5):
            row.cells[idx].width = width

    # Save the document
    out_dir = Path("c:/Users/yasha/Desktop/scout/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "Escrow_Product_Dispute_NonEscrow_Framework.docx"
    doc.save(str(out_path))
    print(f"Document successfully saved to {out_path}")

if __name__ == "__main__":
    generate_document()
