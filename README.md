# Multi-Source Candidate Data Transformer

A production-grade pipeline that reads candidate data from multiple sources — a PDF resume and a recruiter CSV — then extracts, normalises, merges, and projects a single unified Canonical Candidate Profile. Includes a Flask REST API and a React dashboard frontend.

Built as an internship assignment for **Eightfold AI**.

---

## Table of Contents

1. [What This Project Does](#1-what-this-project-does)
2. [Architecture Overview](#2-architecture-overview)
3. [Project Structure](#3-project-structure)
4. [Tech Stack](#4-tech-stack)
5. [Setup & Installation](#5-setup--installation)
6. [How to Run](#6-how-to-run)
   - [CLI Pipeline](#61-cli-pipeline)
   - [Flask API Server](#62-flask-api-server)
   - [React Frontend](#63-react-frontend)
7. [Pipeline Deep Dive](#7-pipeline-deep-dive)
   - [Stage 1 — Parsing](#stage-1--parsing)
   - [Stage 2 — Extraction](#stage-2--extraction)
   - [Stage 3 — Normalisation](#stage-3--normalisation)
   - [Stage 4 — Merging](#stage-4--merging)
   - [Stage 5 — Output Layer](#stage-5--output-layer)
8. [Output Config Profiles](#8-output-config-profiles)
9. [REST API Reference](#9-rest-api-reference)
10. [Frontend Features](#10-frontend-features)
11. [Data Models](#11-data-models)
12. [Test Suite](#12-test-suite)
13. [Running Tests](#13-running-tests)

---

## 1. What This Project Does

Most real-world recruiting pipelines receive the same candidate's information from multiple places — a PDF resume submitted by the candidate, and a structured CSV export from a recruiter's ATS system. These two sources often overlap, contradict, or complement each other.

This project solves that problem:

- It **reads** a PDF resume and an optional recruiter CSV.
- It **extracts** structured data from unstructured resume text using heuristics (no AI or LLMs — fully deterministic).
- It **normalises** every field — emails, phones, dates, skills, company names — into a consistent canonical format.
- It **merges** the two sources using priority rules, resolving conflicts intelligently and keeping track of where every value came from.
- It **assigns a confidence score** to every field based on which source contributed it.
- It **projects** the merged profile into a clean JSON output using one of four configurable profiles.
- It **validates** the output against a schema and generates a validation report.
- It **serves** all of this through a REST API so a frontend dashboard can consume it.

---

## 2. Architecture Overview

The system is a five-stage pipeline:

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────────┐
│  CSV File   │────▶│  CSV Parser  │────▶│                      │
└─────────────┘     └──────────────┘     │  Normalisation       │
                                         │  Pipeline            │
┌─────────────┐     ┌──────────────┐     │                      │
│  PDF Resume │────▶│ Resume       │────▶│  (phone, email,      │
└─────────────┘     │ Parser +     │     │   skill, date,       │
                    │ Extractor    │     │   company, text)     │
                    └──────────────┘     └──────────┬───────────┘
                                                    │
                                                    ▼
                                         ┌──────────────────────┐
                                         │   Candidate Merger   │
                                         │                      │
                                         │  • Conflict resolver │
                                         │  • Confidence engine │
                                         │  • Provenance tracker│
                                         └──────────┬───────────┘
                                                    │
                                                    ▼
                                         ┌──────────────────────┐
                                         │    Output Layer      │
                                         │                      │
                                         │  • Config profiles   │
                                         │  • Serialiser        │
                                         │  • Schema validator  │
                                         │  • File exporter     │
                                         └──────────────────────┘
```

On top of the pipeline, a **Flask API** exposes a single `POST /api/transform` endpoint. The **React frontend** talks to this API, lets you upload files and select a profile, and renders the results in a clean dashboard.

---

## 3. Project Structure

```
Candidate-Transformer/
│
├── backend/                            ← Python backend (pipeline + API)
│   │
│   ├── api.py                          ← Flask REST API server
│   ├── main.py                         ← CLI entrypoint
│   ├── requirements.txt                ← Python dependencies
│   ├── README.md                       ← (legacy, this file replaces it)
│   │
│   ├── inputs/                         ← Sample input files
│   │   ├── sample_resume.pdf           ← Sample PDF resume
│   │   └── recruiter.csv              ← Sample recruiter CSV
│   │
│   ├── config/                         ← Output profile configurations
│   │   ├── config_loader.py            ← Loads and validates config JSON files
│   │   ├── default.json                ← All fields, no confidence/sources
│   │   ├── minimal.json                ← Name, email, phone, skills only
│   │   ├── recruiter.json              ← ATS view with field renaming
│   │   ├── analytics.json              ← Full output with confidence + sources
│   │   ├── developer.json              ← Developer-focused profile
│   │   └── skill_mapping.json          ← Skill alias → canonical name map
│   │
│   ├── parsers/                        ← File loaders (no extraction logic)
│   │   ├── base_parser.py              ← Abstract BaseParser + ParserError
│   │   ├── csv_parser.py               ← Reads recruiter CSV via pandas
│   │   └── resume_parser.py            ← Extracts raw text from PDF via pdfplumber
│   │
│   ├── extractors/                     ← Heuristic extraction from raw text
│   │   ├── regex_patterns.py           ← Shared regex for emails, phones, URLs
│   │   └── resume_extractor.py         ← Section detection, skill/exp/edu/project extraction
│   │
│   ├── models/                         ← Data model dataclasses
│   │   ├── candidate.py                ← CandidateField, CanonicalCandidate
│   │   ├── experience.py               ← Experience dataclass (title, company, dates, bullets)
│   │   ├── education.py                ← Education dataclass (degree, CGPA, percentage, grade)
│   │   └── project.py                  ← Project dataclass (name, tech stack, dates, bullets)
│   │
│   ├── transformers/                   ← Field-level normalisers
│   │   ├── base_normalizer.py          ← Abstract BaseNormalizer interface
│   │   ├── phone_normalizer.py         ← Strips formatting, preserves country code
│   │   ├── email_normalizer.py         ← Lowercases and trims
│   │   ├── skill_normalizer.py         ← Maps aliases to canonical skill names
│   │   ├── company_normalizer.py       ← Removes legal suffixes (LLC, Inc.)
│   │   ├── date_normalizer.py          ← Parses many formats → YYYY-MM
│   │   ├── text_normalizer.py          ← Whitespace cleanup and capitalisation
│   │   └── normalization_pipeline.py   ← Orchestrates all normalisers; deduplicates
│   │
│   ├── merger/                         ← Multi-source merge engine
│   │   ├── candidate_merger.py         ← Top-level merge coordinator
│   │   ├── conflict_resolver.py        ← Priority rules for scalar field conflicts
│   │   ├── confidence_engine.py        ← Calculates and assigns confidence scores
│   │   └── provenance_tracker.py       ← Records which source contributed each value
│   │
│   ├── projection/                     ← Output layer (Part 3)
│   │   ├── serializer.py               ← Converts CanonicalCandidate → raw dict
│   │   ├── projector.py                ← Applies include/exclude field rules
│   │   ├── field_selector.py           ← Field filtering and renaming logic
│   │   ├── output_formatter.py         ← Applies pretty-print and formatting rules
│   │   └── recursive_serializer.py     ← Handles nested dataclass serialisation
│   │
│   ├── validation/                     ← Schema validation
│   │   ├── schema_validator.py         ← Validates projected output against rules
│   │   └── validation_report.py        ← ValidationReport dataclass + to_dict()
│   │
│   ├── exporter/                       ← File output
│   │   └── file_exporter.py            ← Writes candidate.json + validation_report.json
│   │
│   ├── utils/                          ← Shared utilities
│   │   ├── exceptions.py               ← Custom exception hierarchy
│   │   ├── file_utils.py               ← validate_file(), is_file_readable(), get_file_size_mb()
│   │   └── logger.py                   ← Configured stream logger
│   │
│   ├── tests/                          ← Full test suite (166 tests)
│   │   ├── conftest.py
│   │   ├── test_csv_parser.py          ← CSV loading and column detection
│   │   ├── test_resume_parser.py       ← PDF loading, encoding fallback, scanned PDF
│   │   ├── test_normalization.py       ← All normaliser unit tests
│   │   ├── test_merge.py               ← Union, append, and scalar merge tests
│   │   ├── test_conflict_resolution.py ← Priority and confidence scoring tests
│   │   ├── test_config.py              ← Config loader and profile tests
│   │   ├── test_projection.py          ← Field filtering and renaming tests
│   │   ├── test_serializer.py          ← Serialiser output tests
│   │   ├── test_export.py              ← File export tests
│   │   ├── test_validation.py          ← Schema validator tests
│   │   ├── test_extraction_improvements.py ← Extraction quality tests
│   │   ├── test_generalization.py      ← Multi-template resume tests
│   │   └── test_robustness.py          ← Production robustness tests (34 tests)
│   │
│   └── output/                         ← Generated output (git-ignored)
│       ├── candidate.json
│       └── validation_report.json
│
└── frontend/                           ← React dashboard (Vite + Tailwind)
    │
    ├── src/
    │   ├── App.jsx                     ← Root component, manages all state
    │   ├── main.jsx                    ← React entry point
    │   ├── index.css                   ← Global styles + Tailwind directives
    │   │
    │   ├── components/
    │   │   ├── Header.jsx              ← Sticky top bar with API status badge
    │   │   ├── UploadCard.jsx          ← Drag-and-drop PDF + CSV upload zones
    │   │   ├── ConfigSelector.jsx      ← 4-profile selector tiles
    │   │   ├── CandidateCard.jsx       ← Name, email, phone, title with confidence bar
    │   │   ├── SkillsCard.jsx          ← Skill chips with count and source badge
    │   │   ├── ExperienceCard.jsx      ← Role cards with bullets
    │   │   ├── EducationCard.jsx       ← Degree cards with CGPA/% badges
    │   │   ├── ProjectCard.jsx         ← Project cards with tech-stack chips
    │   │   ├── DownloadButtons.jsx     ← One-click download for both JSON outputs
    │   │   ├── LoadingSpinner.jsx      ← Ring spinner shown while API processes
    │   │   └── ErrorCard.jsx           ← Friendly error alert with dismiss button
    │   │
    │   └── services/
    │       └── api.js                  ← Axios client for POST /api/transform
    │
    ├── vite.config.js                  ← Vite config with /api/* proxy to port 5000
    ├── tailwind.config.js              ← Tailwind content paths and brand colours
    ├── postcss.config.js
    └── package.json
```

---

## 4. Tech Stack

### Backend
| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| PDF parsing | pdfplumber, PyPDF2 |
| CSV parsing | pandas |
| API server | Flask + flask-cors |
| Testing | pytest (166 tests) |

### Frontend
| Layer | Technology |
|-------|-----------|
| Framework | React 18 (Vite) |
| Styling | Tailwind CSS v3 |
| HTTP client | Axios |
| Build tool | Vite 8 |

---

## 5. Setup & Installation

### Backend

```bash
# Clone the repo and enter the project root
cd Candidate-Transformer/backend

# Create a virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate          # Linux / macOS
.venv\Scripts\activate             # Windows

# Install all Python dependencies
pip install -r requirements.txt
```

### Frontend

```bash
cd Candidate-Transformer/frontend

# Install Node dependencies
npm install
```

> **Node version**: 18 or higher recommended.

---

## 6. How to Run

### 6.1 CLI Pipeline

The CLI reads the sample files in `inputs/`, runs the full pipeline, prints the Canonical Candidate Profile to the console, and writes `output/candidate.json` and `output/validation_report.json`.

```bash
cd backend

# Run with the default output profile
python main.py

# Run with a specific output profile
python main.py --config recruiter
python main.py --config analytics
python main.py --config minimal
```

Available `--config` values: `default`, `minimal`, `recruiter`, `analytics`, `developer`

---

### 6.2 Flask API Server

The API server exposes the pipeline as an HTTP endpoint so the React frontend (or any HTTP client) can call it.

```bash
cd backend

# Start the API on port 5000
python api.py
```

You should see:
```
 * Serving Flask app 'api'
 * Running on http://127.0.0.1:5000
```

Test it is alive:
```bash
curl http://localhost:5000/api/health
# {"service": "candidate-transformer", "status": "ok"}
```

---

### 6.3 React Frontend

Open a **second terminal** and start the Vite dev server. It automatically proxies all `/api/*` requests to the Flask server on port 5000.

```bash
cd frontend
npm run dev
```

Open your browser at **http://localhost:5173**

The two servers need to run at the same time:

| Server | Port | Command |
|--------|------|---------|
| Flask API | 5000 | `python api.py` (run from `backend/`) |
| React dev server | 5173 | `npm run dev` (run from `frontend/`) |

---

## 7. Pipeline Deep Dive

### Stage 1 — Parsing

Two parsers read input files and return a raw Python dictionary. Neither parser does any field extraction — they only load and decode the file content.

**`CSVParser`** (`parsers/csv_parser.py`)
- Uses `pandas` to read the recruiter CSV.
- Detects column names case-insensitively.
- Falls back through multiple encodings (UTF-8, Latin-1, CP1252) if the file has encoding issues.
- Sniffs the delimiter automatically (supports comma, semicolon, pipe, tab).
- Raises a `CorruptedCSVError` for unreadable files.

**`ResumeParser`** (`parsers/resume_parser.py`)
- Uses `pdfplumber` to extract raw text page by page.
- Detects scanned (image-only) PDFs and raises `EmptyResumeError` instead of silently returning empty text.
- Detects encrypted/password-protected PDFs.
- Falls back to `PyPDF2` if `pdfplumber` produces no usable text.
- Validates file path, extension, and readability before attempting to open.

---

### Stage 2 — Extraction

**`ResumeExtractor`** (`extractors/resume_extractor.py`)

This is the core heuristic engine. It takes the raw text string and splits it into sections, then extracts structured data from each section.

**Section detection** (`extract_sections`):
- Scans for heading-like lines (all-caps, short, followed by blank lines or bullet content).
- Maps headings to canonical section names: `skills`, `experience`, `education`, `projects`, `summary`, etc.
- Uses a set of known section heading keywords to identify boundaries.

**What is extracted from each section:**

| Section | Fields extracted |
|---------|-----------------|
| Header (top of resume) | `full_name`, `emails`, `phones`, `headline` |
| Skills | Skill list — filtered with stop words, section heading filter, multi-word phrase protection |
| Experience | Per-role: `title`, `company`, `location`, `start_date`, `end_date`, `description[]` |
| Education | Per-entry: `degree`, `specialization`, `institution`, `start_date`, `end_date`, `cgpa`, `percentage`, `grade` |
| Projects | Per-project: `project_name`, `technology_stack[]`, `start_date`, `end_date`, `description[]` |

**Skills extraction** is particularly robust:
- Section-strict: only processes lines that belong to the Skills section.
- Joins all skills-section lines into one blob before processing, healing cross-line splits from two-column PDFs.
- Multi-word phrase protection: 35+ known phrases (e.g. `Machine Learning`, `Shell Scripting`, `Computer Networks`) are matched before comma-splitting so they are never broken apart.
- Stop word filter: 80+ stop words covering articles, verbs, dates, role/org words, soft skills (Adaptability, Communication, Leadership), and PDF layout orphans.
- Tech normalisation: maps known aliases to canonical names (`react` → `React.js`, `ci/cd` → `CI/CD`, `js` → `JavaScript`).
- Case-insensitive deduplication preserving original order.

---

### Stage 3 — Normalisation

**`NormalizationPipeline`** (`transformers/normalization_pipeline.py`) runs every field through the appropriate normaliser:

| Normaliser | What it does |
|-----------|-------------|
| `PhoneNormalizer` | Strips spaces, dashes, brackets. Keeps leading `+` for country codes. |
| `EmailNormalizer` | Lowercases. Strips surrounding whitespace. Validates basic format. |
| `SkillNormalizer` | Maps raw strings to canonical names via `skill_mapping.json`. e.g. `cpp` → `C++`, `py` → `Python`. |
| `CompanyNormalizer` | Removes legal suffixes (LLC, Inc., Ltd., Pvt.) Resolves known abbreviations. |
| `DateNormalizer` | Parses `Jan 2024`, `01/2024`, `2024-01`, `2024 January`, `Present` etc. → `YYYY-MM`. |
| `TextNormalizer` | Collapses repeated whitespace. Fixes capitalisation. Strips control characters. |

After normalisation, the pipeline deduplicates list fields (emails, phones, skills) using their normalised forms so `john@gmail.com` and `JOHN@GMAIL.COM` are treated as the same entry.

---

### Stage 4 — Merging

**`CandidateMerger`** (`merger/candidate_merger.py`) takes two normalised profiles (one from CSV, one from resume) and produces a single `CanonicalCandidate`.

Three merge strategies are used depending on field type:

| Strategy | Applied to | Behaviour |
|----------|-----------|-----------|
| **UNION** | emails, phones, skills | Combines unique values from both sources |
| **APPEND** | experience, education, projects | Concatenates history from both sources |
| **CONFLICT RESOLVE** | full_name, headline, title, current_company | Picks the higher-priority source's value |

**Conflict resolution priority:**
```
Recruiter CSV  >  Resume PDF
(confidence 1.00)   (confidence 0.90)
```

If the CSV has a `full_name` and the resume also has one and they differ, the CSV value wins. The losing value is logged as a conflict.

**Confidence engine** (`merger/confidence_engine.py`):
- CSV-sourced values start at confidence `1.00`.
- Resume-sourced values start at confidence `0.90`.
- When merging lists, the highest confidence among contributing sources is taken.

**Provenance tracker** (`merger/provenance_tracker.py`):
- Every field in the final `CanonicalCandidate` is wrapped in a `CandidateField` (or `FieldMetadata`) object:
  ```
  CandidateField(
      value      = "Jane Doe",
      confidence = 1.00,
      sources    = ["recruiter.csv"]
  )
  ```
- This means every single piece of data in the output can be traced back to its origin file.

---

### Stage 5 — Output Layer

**Config loader** (`config/config_loader.py`):
- Reads one of the JSON profiles from `config/`.
- Validates the profile structure and reports issues.

**Serialiser** (`projection/serializer.py`):
- Converts the `CanonicalCandidate` dataclass tree into a plain Python dictionary.
- Handles nested `Experience`, `Education`, and `Project` objects recursively.
- Applies the config's `include_fields` / `exclude_fields` rules.
- Applies field renaming from `field_mapping` (used by the `recruiter` profile).
- Conditionally includes `confidence` and `sources` for each field (used by the `analytics` profile).

**Schema validator** (`validation/schema_validator.py`):
- Checks required fields are present.
- Validates email format.
- Warns on duplicate emails.
- Validates confidence values are in [0.0, 1.0].
- Warns on unknown fields.
- Produces a `ValidationReport` with `errors`, `warnings`, and `info` lists.

**File exporter** (`exporter/file_exporter.py`):
- Writes `output/candidate.json` — the projected candidate document.
- Writes `output/validation_report.json` — the full schema validation report.

---

## 8. Output Config Profiles

Four profiles ship with the project. Choose one via `--config` on the CLI, or via the Config Selector in the frontend.

### `default`
Balanced output for general use. All candidate fields included. Confidence and source information excluded. Empty fields kept as empty strings/arrays.

```json
{
  "candidate": {
    "full_name": "Jane Doe",
    "emails": ["jane@example.com"],
    "phones": ["9876543210"],
    "headline": "",
    "current_company": "Google",
    "title": "Software Engineer",
    "skills": ["Python", "React.js", "MongoDB"],
    "experience": [...],
    "education": [...],
    "projects": [...]
  },
  "metadata": { "profile": "default", "schema_version": "1.0" }
}
```

### `minimal`
Only the four most essential fields. Empty fields removed. Good for quick ATS pre-screening.

Fields: `full_name`, `emails`, `phones`, `skills`

### `recruiter`
ATS-optimised view. Excludes projects and headline. Renames fields to match common ATS column names (`full_name` → `candidate_name`, `phones` → `mobile_numbers`).

Fields: `full_name` (as `candidate_name`), `emails`, `phones` (as `mobile_numbers`), `skills`, `experience`, `education`

### `analytics`
Full output including confidence scores and source attribution for every field. Useful for data quality analysis and debugging merge decisions.

All fields included + `confidence` and `sources` attached to each.

---

## 9. REST API Reference

The Flask API server (`backend/api.py`) exposes two endpoints.

### Health Check

```
GET /api/health
```

**Response:**
```json
{ "service": "candidate-transformer", "status": "ok" }
```

---

### Transform

```
POST /api/transform
Content-Type: multipart/form-data
```

**Form fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resume` | File (.pdf) | Yes | The candidate's resume PDF |
| `csv` | File (.csv) | No | Recruiter CSV from an ATS |
| `config` | String | No | Output profile name (default: `default`) |

**Success response (200):**
```json
{
  "candidate": {
    "candidate": {
      "full_name": "Jane Doe",
      "emails": ["jane@example.com"],
      "skills": ["Python", "React.js"],
      "experience": [...],
      "education": [...],
      "projects": [...]
    },
    "metadata": {
      "profile": "default",
      "schema_version": "1.0",
      "generated_at": "2026-06-30T15:54:37Z",
      "candidate_sources": 2
    }
  },
  "validation_report": {
    "is_valid": true,
    "errors": [],
    "warnings": [],
    "info": []
  }
}
```

**Error responses:**

| Status | Condition |
|--------|-----------|
| 400 | No resume file uploaded |
| 400 | Resume is not a PDF, CSV is not a CSV |
| 400 | PDF is scanned/encrypted and unreadable |
| 400 | No data could be extracted from any source |
| 500 | Unexpected server error |

**Example using curl:**
```bash
curl -X POST http://localhost:5000/api/transform \
  -F "resume=@inputs/sample_resume.pdf" \
  -F "csv=@inputs/recruiter.csv" \
  -F "config=analytics"
```

---

## 10. Frontend Features

The React dashboard at `http://localhost:5173` provides a full visual interface to the pipeline.

| Feature | Component | Description |
|---------|-----------|-------------|
| PDF Upload | `UploadCard` | Drag-and-drop or click-to-browse. Shows file name and size. Remove button to clear. |
| CSV Upload | `UploadCard` | Optional second upload zone for the recruiter CSV. |
| Profile selector | `ConfigSelector` | Four clickable tiles — Default, Minimal, Recruiter, Analytics. |
| Transform button | `App` | Disabled until a resume is uploaded. Triggers the API call. |
| Loading state | `LoadingSpinner` | Ring spinner shown while the backend processes the request. |
| Error messages | `ErrorCard` | Shows backend error message with a dismiss button. |
| Candidate info | `CandidateCard` | Name with avatar initial, email (clickable mailto), phone, title, company, headline. Confidence bar for email. |
| Skills | `SkillsCard` | All skills as blue chips. Skill count badge. Source attribution badge. |
| Experience | `ExperienceCard` | Per-role card: title, company, location, date range, bullet points. |
| Education | `EducationCard` | Per-entry card: degree, institution, date range. CGPA / percentage / grade badges. |
| Projects | `ProjectCard` | Per-project card: name, date range, tech-stack chips (violet), bullet points. |
| Download | `DownloadButtons` | One-click download for `candidate.json` and `validation_report.json`. Validation pass/fail badge. |
| New transform | `App` | "New Transform" button resets all state and returns to the upload screen. |

---

## 11. Data Models

### CandidateField

Every field in the canonical profile is wrapped in this dataclass:

```python
@dataclass
class CandidateField:
    value:      Any        # The normalised value (str, list, etc.)
    confidence: float      # 0.0 – 1.0
    sources:    list[str]  # e.g. ["recruiter.csv", "sample_resume.pdf"]
```

### CanonicalCandidate

```python
@dataclass
class CanonicalCandidate:
    full_name:       CandidateField   # str
    emails:          CandidateField   # list[str]
    phones:          CandidateField   # list[str]
    headline:        CandidateField   # str
    current_company: CandidateField   # str
    title:           CandidateField   # str
    skills:          CandidateField   # list[str]
    experience:      CandidateField   # list[Experience]
    education:       CandidateField   # list[Education]
    projects:        CandidateField   # list[Project]
```

### Experience

```python
@dataclass
class Experience:
    title:       str
    company:     str
    location:    str
    start_date:  str        # YYYY-MM
    end_date:    str        # YYYY-MM or "Present"
    description: list[str]  # Bullet points
```

### Education

```python
@dataclass
class Education:
    degree:         str
    specialization: str
    institution:    str
    school:         str     # Alias for institution
    start_date:     str
    end_date:       str
    cgpa:           str     # e.g. "8.5"
    percentage:     str     # e.g. "85.4"
    grade:          str     # e.g. "A+"
    description:    list[str]
    raw_text:       str     # Original text as backup
```

### Project

```python
@dataclass
class Project:
    project_name:      str
    technology_stack:  list[str]
    start_date:        str
    end_date:          str
    description:       list[str]
```

---

## 12. Test Suite

The project has **166 tests** across 13 test files.

| File | Tests | What it covers |
|------|-------|---------------|
| `test_csv_parser.py` | 8 | CSV loading, column detection, encoding fallback, delimiter sniffing |
| `test_resume_parser.py` | 10 | PDF loading, scanned PDF detection, corrupted file handling |
| `test_normalization.py` | 18 | All field normalisers: phone, email, skill, date, company, text |
| `test_merge.py` | 12 | UNION merge, APPEND merge, empty source handling |
| `test_conflict_resolution.py` | 10 | Priority rules, confidence scoring, provenance recording |
| `test_config.py` | 8 | Config loader, profile validation, unknown fields |
| `test_projection.py` | 10 | Field filtering, renaming, empty field policy |
| `test_serializer.py` | 8 | Serialiser output structure, metadata inclusion |
| `test_export.py` | 6 | File writing, overwrite behaviour, error handling |
| `test_validation.py` | 14 | Schema validation, duplicate detection, confidence range |
| `test_extraction_improvements.py` | 22 | Section-strict extraction, multi-word phrases, heading filtering |
| `test_generalization.py` | 16 | Multi-template resume formats, edge cases |
| `test_robustness.py` | 34 | Production robustness: encoding, corrupt files, noise tokens, multi-word skills |

---

## 13. Running Tests

```bash
cd backend

# Run the full suite
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_robustness.py -v

# Run tests matching a keyword
python -m pytest tests/ -k "skill" -v

# Run with short traceback (faster to read)
python -m pytest tests/ --tb=short
```

Expected output on a clean run:
```
========================= 166 passed in 4.03s ==========================
```

---

## Quick Start (TL;DR)

```bash
# 1. Install backend dependencies
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Run the CLI pipeline once (sanity check)
python main.py

# 3. Start the Flask API server
python api.py

# 4. In a second terminal, start the frontend
cd ../frontend && npm install && npm run dev

# 5. Open http://localhost:5173 in your browser
#    Upload a PDF resume, click Transform, see the results.
```
