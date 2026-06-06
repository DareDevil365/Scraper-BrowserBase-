const {
  Document, Packer, Paragraph, TextRun, PageBreak, LevelFormat, AlignmentType
} = require('docx');
const fs = require('fs');
const path = require('path');

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
      new TextRun({ text: "\nCore Competitors Analysis (Craftsvilla, Jaypore, Glowroad)", size: 20, font: "Arial" })
    ]
  }),
  new Paragraph({ spacing: { after: 300 } })
);

// ── SUMMARY MATRIX (TEXT VERSION) ────────────────────────────────────────────
documentChildren.push(
  h1("SUMMARY REFERENCE MATRIX"),
  p("", { after: 100 })
);

const matrixData = [
  ["Craftsvilla", "Escrow-like", "Seller ships & uploads tracking", "No (schedule-based post-ship)", "15 working days post-shipment"],
  ["Jaypore", "No (Curated D2C Brand)", "Artisan B2B invoicing", "N/A (procurement terms)", "None (Net 30/45 B2B terms)"],
  ["Glowroad", "Escrow-like", "Carrier API delivery confirmation", "No (automatic post-delivery)", "7-10 days post-delivery"]
];

matrixData.forEach(([platform, type, trigger, confirm, window]) => {
  documentChildren.push(new Paragraph({
    spacing: { after: 80 },
    children: [
      new TextRun({ text: `• ${platform}: `, bold: true, size: 20, font: "Arial" }),
      new TextRun({ text: `Escrow Type: ${type} | Payout Trigger: ${trigger} | Buyer Confirm?: ${confirm} | Auto-Release: ${window}`, size: 20, font: "Arial" })
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

// Pack & Save to outputs/Core_Competitors.docx
Packer.toBuffer(doc).then(buffer => {
  const targetDir = 'c:/Users/yasha/Desktop/scout/outputs';
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }
  const outputPath = path.join(targetDir, 'Core_Competitors.docx');
  try {
    fs.writeFileSync(outputPath, buffer);
    console.log('Saved core competitors report to:', outputPath);
  } catch (err) {
    if (err.code === 'EBUSY') {
      const fallbackPath = path.join(targetDir, 'Core_Competitors_New.docx');
      fs.writeFileSync(fallbackPath, buffer);
      console.log('Warning: Core_Competitors.docx is locked. Saved as fallback to:', fallbackPath);
    } else {
      throw err;
    }
  }
}).catch(err => {
  console.error('Error generating document:', err);
  process.exit(1);
});
