const {
  Document, Packer, Paragraph, TextRun, PageBreak, LevelFormat, AlignmentType
} = require('docx');
const fs = require('fs');
const path = require('path');

const C = {
  brand: "1A3C5E",
  red: "DC2626"
};

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after ?? 100, before: opts.before ?? 0 },
    alignment: opts.align ?? AlignmentType.LEFT,
    children: [new TextRun({
      text,
      bold: opts.bold ?? false,
      italics: opts.italic ?? false,
      size: opts.size ?? 20,
      font: "Arial",
      ...(opts.underline ? { underline: {} } : {}),
    })]
  });
}

function h1(text) {
  return new Paragraph({
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text, bold: true, size: 32, font: "Arial", underline: {} })]
  });
}

// Subheading style
function h2(text) {
  return new Paragraph({
    spacing: { before: 180, after: 80 },
    children: [new TextRun({ text, bold: true, size: 26, font: "Arial" })]
  });
}

function labelParagraph(label, value) {
  const valueLines = value.split('\n');
  const children = [
    new TextRun({ text: label + ": ", bold: true, size: 20, font: "Arial" })
  ];
  valueLines.forEach((line, idx) => {
    children.push(new TextRun({
      text: (idx > 0 ? '\n' : '') + line,
      size: 20,
      font: "Arial"
    }));
  });
  return new Paragraph({
    spacing: { after: 120 },
    children: children
  });
}

// ─── PARSER ──────────────────────────────────────────────────────────────────
function parseTextFile(filePath) {
  if (!fs.existsSync(filePath)) {
    console.error(`File does not exist: ${filePath}`);
    return null;
  }
  const content = fs.readFileSync(filePath, 'utf-8');
  const sections = {};
  let currentSection = null;
  let currentKey = null;
  let currentVal = [];

  const lines = content.split(/\r?\n/);
  const headings = [
    "ESCROW MODEL",
    "RELEASE TRIGGERS",
    "AUTO-RELEASE",
    "DISPUTE HANDLING",
    "PROVIDER PROTECTION",
    "DISPUTE NUANCES & ACCOUNT CONTROLS",
    "KEY INSIGHT FOR SILAAI",
    "SOURCES USED"
  ];

  for (let line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    if (headings.includes(trimmed)) {
      if (currentSection && currentKey) {
        if (!sections[currentSection]) sections[currentSection] = [];
        sections[currentSection].push([currentKey, currentVal.join('\n')]);
      }
      currentSection = trimmed;
      if (!sections[currentSection]) sections[currentSection] = [];
      currentKey = null;
      currentVal = [];
      continue;
    }

    if (!currentSection) continue;

    // Check if line is a key-value line
    if (trimmed.includes(':') && !trimmed.startsWith('-') && !trimmed.startsWith('http') && !trimmed.startsWith('https')) {
      if (currentKey) {
        if (!sections[currentSection]) sections[currentSection] = [];
        sections[currentSection].push([currentKey, currentVal.join('\n')]);
      }
      const colonIdx = trimmed.indexOf(':');
      currentKey = trimmed.substring(0, colonIdx).trim();
      currentVal = [trimmed.substring(colonIdx + 1).trim()];
    } else {
      if (currentKey) {
        currentVal.push(trimmed);
      } else {
        currentKey = "Details";
        currentVal = [trimmed];
      }
    }
  }

  if (currentSection && currentKey) {
    if (!sections[currentSection]) sections[currentSection] = [];
    sections[currentSection].push([currentKey, currentVal.join('\n')]);
  }

  return sections;
}

// ─── TAKEAWAYS & COMPARATIVE MATRIX ──────────────────────────────────────────
const SilaaiTakeaways = {
  mechanismsToAdopt: [
    ["1. Video evidence for damaged/wrong returns (from GlowRoad)", "GlowRoad's mandatory unboxing-video-within-2-days rule is the most fraud-resistant returns evidence mechanism. Silaai should require this for any damage or wrong-item claim above ₹1,500. The video must begin with the return tracking label visible, followed by full unboxing."],
    ["2. Zero RTO charge for buyer-cancelled orders (from GlowRoad)", "Cash-constrained New Artisans cannot afford surprise logistics debits for orders the buyer cancelled. GlowRoad's zero-RTO-charge policy must be mirrored. Only charge the artisan if the return is their fault (wrong item, poor quality)."],
    ["3. Pre-dispatch quality photo as evidence layer (from Jaypore's QC philosophy)", "Jaypore's 4–5 layer QC before dispatch is impractical for an open marketplace, but the dispatch-photo requirement serves the same function. A mandatory dispatch photo (taken before handoff to 3PL) creates a timestamped record that protects the artisan if the buyer claims the wrong item was sent."],
    ["4. 48-hour damage evidence window (from Jaypore)", "Jaypore's 48-hour window for damage photo submission is stricter than Craftsvilla's 7 days and creates a more credible evidence trail (fresher, less likely to be staged). Silaai should adopt 48 hours for damage claims, with the video standard from GlowRoad."],
    ["5. Buyer-fault vs provider-fault determination framework (from GlowRoad)", "GlowRoad's explicit attribution of return shipping costs based on whether the fault was the buyer's or supplier's is the correct framework for Silaai. If a buyer returns an item in good condition because they changed their mind, the provider should not bear the cost. If the provider sent the wrong size, the provider bears both legs of shipping."]
  ],
  thingsToAvoid: [
    ["AVOID: Schedule-based payout without delivery confirmation (Craftsvilla's model)", "Craftsvilla pays sellers 15 days after shipment regardless of whether the buyer has received the item. For Silaai's artisan context — where inter-state shipping can take 10–12 days and delivery disputes are frequent — this creates a scenario where the artisan has been paid but the buyer hasn't received the item, making fund recovery harder and trust weaker. Silaai's OTP-on-delivery trigger is the correct replacement."],
    ["AVOID: Tier system that only affects shipping discounts (GlowRoad's tier design)", "GlowRoad's Gold/Silver/Bronze tiers reward higher-performing suppliers with shipping discounts and better support, but payout speed and escrow hold duration are identical across all tiers. This wastes the strongest incentive mechanism available. Silaai must make payout speed (72 hrs → 24 hrs → same-day) the primary tier reward."],
    ["AVOID: No explicit high-value order protection ceiling (all three platforms)", "None of the three platforms publicly state a coverage cap or special handling for high-value orders. This is a significant gap. A ₹40,000 bridal lehenga dispute is treated identically to a ₹500 cushion cover dispute on all three. Silaai must encode explicit coverage tiers and mandatory pre-dispatch quality inspection for orders above ₹8,000."]
  ]
};

const comparativeSummary = [
  ["Escrow type", "Craftsvilla: Platform-held, schedule-based | Jaypore: None (retail model) | GlowRoad: Platform-held, delivery-gated | Silaai Recommendation: Platform-held, OTP-gated"],
  ["Payout trigger", "Craftsvilla: 15 working days post-ship | Jaypore: Supplier contract (N/A) | GlowRoad: 7–10 days post-delivery | Silaai Recommendation: OTP confirmation + tier hold"],
  ["Buyer confirmation", "Craftsvilla: None required | Jaypore: None (retailer model) | GlowRoad: None required | Silaai Recommendation: REQUIRED — OTP at doorstep"],
  ["Return window", "Craftsvilla: 7 days from delivery | Jaypore: 10 days from delivery | GlowRoad: 7 days from delivery | Silaai Recommendation: 7 days from OTP-confirmed delivery"],
  ["Damage evidence", "Craftsvilla: Photos within 7 days | Jaypore: Photos + barcode within 48 hrs | GlowRoad: Video within 2 working days | Silaai Recommendation: Unboxing video within 48 hrs"],
  ["RTO charge to provider", "Craftsvilla: Not documented | Jaypore: N/A | GlowRoad: Zero charge | Silaai Recommendation: Zero charge — adopt GlowRoad"],
  ["Tier-linked payout?", "Craftsvilla: No | Jaypore: No | GlowRoad: No (tiers = shipping only) | Silaai Recommendation: YES — core Silaai differentiator"],
  ["High-value protection", "Craftsvilla: None documented | Jaypore: Full Jaypore absorption | GlowRoad: No cap stated | Silaai Recommendation: Coverage cap by tier (₹3K/₹8K/₹20K)"],
  ["Chargeback shield", "Craftsvilla: None documented | Jaypore: Jaypore absorbs (retailer) | GlowRoad: Amazon absorbs (partial) | Silaai Recommendation: Platform absorbs up to cap; above cap = seller risk"],
  ["COD handling", "Craftsvilla: Payout after pickup confirmed | Jaypore: N/A | GlowRoad: 7–10 days post-delivery | Silaai Recommendation: Same as prepaid — OTP triggers both"],
  ["KYC & Onboarding", "Craftsvilla: Requires PAN/Aadhaar/GSTIN & Bank check | Jaypore: Strict corporate onboarding & QC audits | GlowRoad: GSTIN, PAN & Bank Penny Drop check | Silaai Recommendation: Tiered KYC (Aadhaar for New → GST for Elite)"],
  ["Fee split & refund", "Craftsvilla: Commission reversed; shipping fee charged | Jaypore: B2B wholesale margin discount | GlowRoad: Reseller margin + platform fee reversed | Silaai Recommendation: Payment gateway fee refunded on buyer fault"],
  ["Hold extension", "Craftsvilla: Not possible (hard 15-day timeline) | Jaypore: Not applicable (B2B terms) | GlowRoad: Not possible (hard 7-day timeline) | Silaai Recommendation: Allowed up to 48 hrs for fit check"],
  ["Alteration vs Refund", "Craftsvilla: Returns/refunds only; no alterations | Jaypore: Final sale (no alterations/refunds) | GlowRoad: Returns/refunds only; no alterations | Silaai Recommendation: Mandatory alterations first; refund secondary"],
  ["Material loss shield", "Craftsvilla: No coverage for raw materials | Jaypore: Artisan charged for fabric wastage >5% | GlowRoad: No raw material coverage | Silaai Recommendation: Escrow protection for custom fabric up to ₹5,000"]
];

// ─── BUILD DOCUMENT ──────────────────────────────────────────────────────────
const competitors = ["Craftsvilla", "Jaypore", "Glowroad"];
const inputDir = "c:/Users/yasha/Desktop/scout/outputs/competitor_research";

const documentChildren = [];

// Title
documentChildren.push(
  new Paragraph({
    spacing: { before: 400, after: 200 },
    children: [
      new TextRun({ text: "SILAAI — ESCROW MODEL RESEARCH", bold: true, size: 28, font: "Arial" }),
      new TextRun({ text: "\nCore Competitors Escrow & Payout Comparison (Craftsvilla, Jaypore, Glowroad)", size: 20, font: "Arial" })
    ]
  }),
  new Paragraph({ spacing: { after: 300 } })
);

// ── SUMMARY COMPARATIVE REFERENCE (TEXT VERSION) ─────────────────────────────
documentChildren.push(
  h1("COMPARATIVE ESCROW SUMMARY"),
  p("", { after: 100 })
);

comparativeSummary.forEach(([dimension, text]) => {
  documentChildren.push(new Paragraph({
    spacing: { after: 80 },
    children: [
      new TextRun({ text: `• ${dimension}: `, bold: true, size: 20, font: "Arial" }),
      new TextRun({ text: text, size: 20, font: "Arial" })
    ]
  }));
});

documentChildren.push(
  p("", { after: 200 }),
  new Paragraph({ children: [new PageBreak()] })
);

// ── ADD SECTIONS FOR EACH COMPETITOR ─────────────────────────────────────────
competitors.forEach((company, index) => {
  const filePath = path.join(inputDir, `${company}.txt`);
  const parsed = parseTextFile(filePath);
  if (!parsed) return;

  // Company Name Heading
  documentChildren.push(
    h1(company.toUpperCase()),
    p("", { after: 120 })
  );

  // Escrow Model Overview
  if (parsed["ESCROW MODEL"] && parsed["ESCROW MODEL"].length > 0) {
    documentChildren.push(h2("Escrow Model Overview"));
    parsed["ESCROW MODEL"].forEach(([k, v]) => {
      documentChildren.push(labelParagraph(k, v));
    });
    documentChildren.push(p("", { after: 100 }));
  }

  // Release Triggers
  if (parsed["RELEASE TRIGGERS"] && parsed["RELEASE TRIGGERS"].length > 0) {
    documentChildren.push(h2("Release Triggers"));
    parsed["RELEASE TRIGGERS"].forEach(([k, v]) => {
      documentChildren.push(labelParagraph(k, v));
    });
    documentChildren.push(p("", { after: 100 }));
  }

  // Auto-Release
  if (parsed["AUTO-RELEASE"] && parsed["AUTO-RELEASE"].length > 0) {
    documentChildren.push(h2("Auto-Release"));
    parsed["AUTO-RELEASE"].forEach(([k, v]) => {
      documentChildren.push(labelParagraph(k, v));
    });
    documentChildren.push(p("", { after: 100 }));
  }

  // Dispute Handling
  if (parsed["DISPUTE HANDLING"] && parsed["DISPUTE HANDLING"].length > 0) {
    documentChildren.push(h2("Dispute Handling"));
    parsed["DISPUTE HANDLING"].forEach(([k, v]) => {
      documentChildren.push(labelParagraph(k, v));
    });
    documentChildren.push(p("", { after: 100 }));
  }

  // Provider Protection
  if (parsed["PROVIDER PROTECTION"] && parsed["PROVIDER PROTECTION"].length > 0) {
    documentChildren.push(h2("Provider Protection"));
    parsed["PROVIDER PROTECTION"].forEach(([k, v]) => {
      documentChildren.push(labelParagraph(k, v));
    });
    documentChildren.push(p("", { after: 100 }));
  }

  // Dispute Nuances
  if (parsed["DISPUTE NUANCES & ACCOUNT CONTROLS"] && parsed["DISPUTE NUANCES & ACCOUNT CONTROLS"].length > 0) {
    documentChildren.push(h2("Dispute Nuances & Account Controls"));
    parsed["DISPUTE NUANCES & ACCOUNT CONTROLS"].forEach(([k, v]) => {
      documentChildren.push(labelParagraph(k, v));
    });
    documentChildren.push(p("", { after: 100 }));
  }

  // Key Insight
  if (parsed["KEY INSIGHT FOR SILAAI"] && parsed["KEY INSIGHT FOR SILAAI"].length > 0) {
    documentChildren.push(h2("Key Insight for Silaai"));
    parsed["KEY INSIGHT FOR SILAAI"].forEach(([k, v]) => {
      documentChildren.push(labelParagraph(k, v));
    });
    documentChildren.push(p("", { after: 100 }));
  }

  // Sources Used
  if (parsed["SOURCES USED"]) {
    documentChildren.push(h2("Sources Used"));
    for (const source of parsed["SOURCES USED"]) {
      const text = source[0] === "Details" ? source[1] : `${source[0]}: ${source[1]}`;
      const urls = text.split('\n');
      for (const u of urls) {
        if (u.trim()) {
          documentChildren.push(new Paragraph({
            numbering: { reference: "bullets", level: 0 },
            spacing: { after: 60 },
            children: [new TextRun({ text: u.trim(), size: 17, color: "64748B", font: "Arial" })]
          }));
        }
      }
    }
    documentChildren.push(p("", { after: 200 }));
  }

  // Add PageBreak between companies except the last one
  if (index < competitors.length - 1) {
    documentChildren.push(new Paragraph({ children: [new PageBreak()] }));
  }
});

// ── SILAAI TAKEAWAYS SECTION ─────────────────────────────────────────────────
documentChildren.push(
  new Paragraph({ children: [new PageBreak()] }),
  h1("SILAAI SYNTHESIS — STRATEGIC RECOMMENDATIONS"),
  p("", { after: 120 }),
  h2("Top 5 Mechanisms to Adopt for Silaai")
);

SilaaiTakeaways.mechanismsToAdopt.forEach(([title, desc]) => {
  documentChildren.push(new Paragraph({
    spacing: { before: 120, after: 60 },
    children: [new TextRun({ text: title, bold: true, size: 22, font: "Arial" })]
  }));
  documentChildren.push(p(desc, { after: 100 }));
});

documentChildren.push(
  p("", { after: 120 }),
  h2("Top 3 Things to Avoid or Reject")
);

SilaaiTakeaways.thingsToAvoid.forEach(([title, desc]) => {
  documentChildren.push(new Paragraph({
    spacing: { before: 120, after: 60 },
    children: [new TextRun({ text: title, bold: true, size: 22, color: C.red, font: "Arial" })]
  }));
  documentChildren.push(p(desc, { after: 100 }));
});

// Create Document
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 1 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 600, hanging: 300 } } } }] },
    ]
  },
  sections: [{
    properties: {
      page: { size: { width: 12240, height: 15840 }, margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 } }
    },
    children: documentChildren
  }]
});

// Pack & Save to outputs/Answer.docx
Packer.toBuffer(doc).then(buffer => {
  const targetDir = 'c:/Users/yasha/Desktop/scout/outputs';
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }
  const outputPath = path.join(targetDir, 'Answer.docx');
  try {
    fs.writeFileSync(outputPath, buffer);
    console.log('Saved primary competitors report to:', outputPath);
  } catch (err) {
    if (err.code === 'EBUSY') {
      const fallbackPath = path.join(targetDir, 'Answer_New.docx');
      fs.writeFileSync(fallbackPath, buffer);
      console.log('Warning: Answer.docx is locked. Saved as fallback to:', fallbackPath);
    } else {
      throw err;
    }
  }
}).catch(err => {
  console.error('Error generating document:', err);
  process.exit(1);
});
