"""
Generate the one-page design document PDF for the Eightfold AI assignment.
Output: VishwasReddy_vishwasr762@gmail.com_Eightfold.pdf
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

OUTPUT = "/home/vishwas/FULL/Candidate-Transformer/VishwasReddy_vishwasr762@gmail.com_Eightfold.pdf"

PAGE_W, PAGE_H = A4
MARGIN = 1.6 * cm

DARK   = colors.HexColor("#1e293b")
MID    = colors.HexColor("#475569")
LIGHT  = colors.HexColor("#94a3b8")
ACCENT = colors.HexColor("#2563eb")
GREEN  = colors.HexColor("#059669")
LINE   = colors.HexColor("#e2e8f0")
BGHEAD = colors.HexColor("#f8fafc")

def S(name, **kw):
    base = dict(fontName="Helvetica", fontSize=8.5, leading=12,
                textColor=DARK, alignment=TA_JUSTIFY)
    base.update(kw)
    return ParagraphStyle(name, **base)

TITLE  = S("title",  fontName="Helvetica-Bold", fontSize=15, leading=18,
           textColor=DARK, alignment=TA_LEFT)
BYLINE = S("byline",  fontName="Helvetica", fontSize=8, leading=11,
           textColor=MID,  alignment=TA_LEFT)
SEC    = S("sec",    fontName="Helvetica-Bold", fontSize=9.5, leading=13,
           textColor=ACCENT, spaceBefore=7, spaceAfter=1)
BODY   = S("body",   fontName="Helvetica", fontSize=8.2, leading=12,
           textColor=DARK, alignment=TA_JUSTIFY, spaceAfter=3)
SMALL  = S("small",  fontName="Helvetica", fontSize=7.8, leading=11,
           textColor=DARK)
SMIB   = S("smib",   fontName="Helvetica-Bold", fontSize=7.8, leading=11,
           textColor=DARK)
FOOT   = S("foot",   fontName="Helvetica", fontSize=7.2, leading=10,
           textColor=LIGHT, alignment=TA_CENTER)

def HR():
    return HRFlowable(width="100%", thickness=0.4, color=LINE,
                      spaceAfter=3, spaceBefore=1)

def sec(title, *paras):
    items = [Paragraph(title, SEC), HR()]
    for p in paras:
        items.append(Paragraph(p, BODY))
    return items

W = PAGE_W - 2 * MARGIN   # usable width

story = []

# ── Title block ────────────────────────────────────────────────────────────────
story.append(Paragraph("Candidate Data Transformer — System Design", TITLE))
story.append(Spacer(1, 3))
story.append(Paragraph(
    "Vishwas Reddy &nbsp;·&nbsp; vishwasr762@gmail.com &nbsp;·&nbsp; Eightfold AI Engineering Intern Assignment",
    BYLINE))
story.append(Spacer(1, 5))
story.append(HR())
story.append(Spacer(1, 4))

# ── Two-column layout helper ───────────────────────────────────────────────────
def two_col(left_items, right_items, split=0.50):
    lw = W * split - 0.2*cm
    rw = W * (1-split) - 0.2*cm
    left_frame  = Table([[i] for i in left_items],  colWidths=[lw])
    right_frame = Table([[i] for i in right_items], colWidths=[rw])
    left_frame.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    right_frame.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    outer = Table([[left_frame, right_frame]], colWidths=[lw + 0.2*cm, rw + 0.2*cm])
    outer.setStyle(TableStyle([
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    return outer

# ── Section 1: The Problem + Pipeline ─────────────────────────────────────────
prob_items = [
    Paragraph("The Problem", SEC), HR(),
    Paragraph(
        "Eightfold ingests candidate information from many places at once. "
        "The same person may appear in a recruiter's CSV <i>and</i> as a resume PDF "
        "with conflicting or missing data. The job is to merge these into one clean, "
        "trustworthy profile — tracking where every field came from and how confident "
        "we are in it. Wrong-but-confident is worse than honestly empty.",
        BODY),
    Paragraph("Sources handled", SEC), HR(),
    Paragraph(
        "<b>Structured (CSV):</b> Recruiter CSV export with rows for name, email, phone, "
        "company, and title. This is the primary source — it scores the highest confidence (1.0).<br/>"
        "<b>Unstructured (PDF resume):</b> Free-text PDF parsed with pdfplumber, split "
        "into sections (education, experience, skills, projects) using keyword headers. "
        "Confidence: 0.9.",
        BODY),
]

pipe_items = [
    Paragraph("The Pipeline", SEC), HR(),
    Paragraph(
        "<b>1 · Parse</b> — Each source is read by a dedicated parser. The CSV parser "
        "maps column names to canonical field names. The resume parser extracts "
        "text page by page, then splits it by section headers.<br/><br/>"
        "<b>2 · Normalize</b> — Dates → YYYY-MM. Phones → E.164 (e.g. +919014746514). "
        "Country codes → ISO 3166-1 alpha-2. Skills → lowercased and deduplicated. "
        "Emails → validated and stripped of extra spaces.<br/><br/>"
        "<b>3 · Merge</b> — Scalar fields (name, title, headline) follow a priority rule "
        "where CSV wins. List fields (skills, emails) use a union. Structured lists "
        "(education, experience) are appended from both sources.<br/><br/>"
        "<b>4 · Confidence</b> — Every field stores the source it came from and a "
        "score. The overall_confidence is the average of all field scores. A "
        "deterministic UUID is generated from name + email as the candidate_id.<br/><br/>"
        "<b>5 · Project → Validate</b> — A config selects which fields appear, renames "
        "them, applies normalization, and controls the missing-field policy. "
        "The result is validated before returning.",
        BODY),
]

story.append(two_col(prob_items, pipe_items, split=0.44))
story.append(Spacer(1, 5))

# ── Section 2: Schema table ────────────────────────────────────────────────────
story.append(Paragraph("Default Output Schema", SEC))
story.append(HR())

schema_rows = [
    [Paragraph("<b>Field</b>", SMIB),
     Paragraph("<b>Type / Shape</b>", SMIB),
     Paragraph("<b>How it is populated</b>", SMIB)],
    [Paragraph("candidate_id", SMALL),
     Paragraph("string", SMALL),
     Paragraph("UUID-5 derived from full_name + first email — deterministic", SMALL)],
    [Paragraph("full_name", SMALL),
     Paragraph("string", SMALL),
     Paragraph("CSV wins over resume when both present", SMALL)],
    [Paragraph("emails", SMALL),
     Paragraph("string[ ]", SMALL),
     Paragraph("Union from all sources, validated", SMALL)],
    [Paragraph("phones", SMALL),
     Paragraph("string[ ] · E.164", SMALL),
     Paragraph("Normalized to +CountryCode format; Indian 5+5 format handled", SMALL)],
    [Paragraph("location", SMALL),
     Paragraph("{city, region, country}", SMALL),
     Paragraph("Extracted from resume header; country → ISO 3166-1 alpha-2", SMALL)],
    [Paragraph("links", SMALL),
     Paragraph("{linkedin, github, portfolio, other[ ]}", SMALL),
     Paragraph("Regex-extracted URLs from resume text", SMALL)],
    [Paragraph("headline", SMALL),
     Paragraph("string | null", SMALL),
     Paragraph("From CSV or resume summary section", SMALL)],
    [Paragraph("years_experience", SMALL),
     Paragraph("number | null", SMALL),
     Paragraph("Sum of all experience date ranges; 'Present' → today", SMALL)],
    [Paragraph("skills", SMALL),
     Paragraph("{name, confidence, sources[ ]}", SMALL),
     Paragraph("Canonical lowercase names; confidence from source weight", SMALL)],
    [Paragraph("experience", SMALL),
     Paragraph("{company, title, start, end, summary}", SMALL),
     Paragraph("Dates in YYYY-MM; 'Present' kept as-is", SMALL)],
    [Paragraph("education", SMALL),
     Paragraph("{institution, degree, field, end_year}", SMALL),
     Paragraph("Parsed from section headers; percentage / CGPA extracted", SMALL)],
    [Paragraph("provenance", SMALL),
     Paragraph("{field, source, method}", SMALL),
     Paragraph("Stored per field; surfaced in analytics config", SMALL)],
    [Paragraph("overall_confidence", SMALL),
     Paragraph("number  (0–1)", SMALL),
     Paragraph("Average of all non-zero field confidence scores", SMALL)],
]

cw = [W*0.18, W*0.22, W*0.60]
schema_tbl = Table(schema_rows, colWidths=cw)
schema_tbl.setStyle(TableStyle([
    ("BACKGROUND",   (0,0),(-1,0),  BGHEAD),
    ("BACKGROUND",   (0,1),(-1,-1), colors.white),
    ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f8fafc")]),
    ("GRID",         (0,0),(-1,-1), 0.35, LINE),
    ("TOPPADDING",   (0,0),(-1,-1), 3),
    ("BOTTOMPADDING",(0,0),(-1,-1), 3),
    ("LEFTPADDING",  (0,0),(-1,-1), 5),
    ("RIGHTPADDING", (0,0),(-1,-1), 5),
    ("VALIGN",       (0,0),(-1,-1), "TOP"),
]))
story.append(schema_tbl)
story.append(Spacer(1, 5))

# ── Section 3: Config + Edge cases (two columns) ───────────────────────────────
cfg_items = [
    Paragraph("Configurable Output", SEC), HR(),
    Paragraph(
        "The projection layer sits on top of the canonical record and reshapes "
        "the output without touching the engine. The config accepts:",
        BODY),
    Paragraph(
        "· <b>include_fields</b> — which fields to include<br/>"
        "· <b>field_mapping</b> — rename a field (e.g. full_name → candidate_name)<br/>"
        "· <b>normalize</b> — per-field rules (E.164 for phones, canonical for skills)<br/>"
        "· <b>include_confidence / include_sources</b> — toggle provenance on or off<br/>"
        "· <b>empty_field_policy</b> — keep, null, omit, or error<br/>"
        "· <b>date_format</b> — ISO or raw",
        BODY),
    Paragraph(
        "Four built-in profiles: <b>default</b> (all fields), <b>minimal</b> (name, "
        "email, phone, skills), <b>recruiter</b> (adds location, links, years_experience), "
        "<b>analytics</b> (adds confidence scores and provenance for every field). "
        "The same engine runs for all four — only the projection config changes.",
        BODY),
    Spacer(1, 4),
    Paragraph("Constraints", SEC), HR(),
    Paragraph(
        "<b>Deterministic</b> — same inputs always produce the same output. The "
        "candidate_id is a UUID-5 so the same person gets the same ID every time.<br/><br/>"
        "<b>Robust</b> — a missing, empty, or garbage source never crashes the run. "
        "Unknown values become null. The validation report flags warnings separately "
        "from errors.<br/><br/>"
        "<b>Scalable</b> — no global state, no LLM calls, no external APIs. "
        "Each candidate runs independently through the pipeline.",
        BODY),
]

edge_items = [
    Paragraph("Edge Cases Handled", SEC), HR(),
    Paragraph(
        "<b>Indian phone format (5+5 digits)</b><br/>"
        "+91 90147 46514 uses a space-separated 5+5 pattern that the standard 3+3+4 "
        "regex misses. The phone pattern was extended to catch both.<br/><br/>"
        "<b>Education percentages written many ways</b><br/>"
        "'Marks: 92%', '9.2 CGPA', '92% (CBSE)' all appear on real resumes. Each "
        "format has its own extraction path. A lone dot (like in 'Education.') was "
        "excluded from triggering percentage logic.<br/><br/>"
        "<b>Scanned / image-only PDFs</b><br/>"
        "If pdfplumber extracts zero text, the system raises a clear typed exception "
        "instead of returning an empty profile. OCR was deliberately left out of scope.<br/><br/>"
        "<b>Single source — no CSV uploaded</b><br/>"
        "The merger accepts an empty second source and still produces a valid output. "
        "Nothing in the pipeline assumes both sources are present.<br/><br/>"
        "<b>Duplicate skills across sources</b><br/>"
        "'ReactJS', 'React.js', and 'react' mean the same thing. Skills are lowercased "
        "and stripped of punctuation before deduplication so only one canonical "
        "name is kept.",
        BODY),
]

story.append(two_col(cfg_items, edge_items, split=0.50))
story.append(Spacer(1, 5))

# ── What I left out ────────────────────────────────────────────────────────────
story += sec(
    "What I Left Out and Why",
    "OCR for scanned PDFs was not implemented — it requires Tesseract and adds "
    "significant complexity for a case that is rare when resumes are submitted digitally. "
    "GitHub and LinkedIn API lookups were also skipped because they need "
    "authentication tokens and rate-limit handling which are outside the scope of this "
    "assignment. The system does extract GitHub and LinkedIn URLs if they appear as "
    "plain text in the resume, which covers most real-world cases. "
    "ATS JSON blob parsing was not implemented — the CSV source satisfies the "
    "structured-source requirement and is more representative of actual recruiter workflows."
)

story.append(HR())
story.append(Paragraph(
    "Built with Python 3 · pdfplumber · Flask REST API · React UI · "
    "166 automated tests · CLI + Web UI both available",
    FOOT))

# ── Build ──────────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=A4,
    leftMargin=MARGIN, rightMargin=MARGIN,
    topMargin=1.4*cm,  bottomMargin=1.2*cm,
)
doc.build(story)
print(f"PDF written → {OUTPUT}")
