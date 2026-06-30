# Multi-Source Candidate Data Transformer (Part 1 & 2)

An interview-ready, production-grade Python library for reading multiple structured and unstructured candidate sources, extracting details, and merging them into a unified, high-confidence Canonical Candidate Profile.

---

## Project Overview

This system is divided into two distinct components:
1. **Input & Data Extraction Layer (Part 1)**: Loads candidate files (Recruiter CSVs and Resume PDFs), segments text (without calling external AI/LLMs), and extracts candidates.
2. **Transformation Engine (Part 2)**: Standardizes data values, performs deduplication, executes cross-file merges with priority rules, resolves source conflicts, calculates confidence scores, and captures provenance records at the field level.

---

## Folder Structure

```text
candidate_transformer/
├── inputs/
│      recruiter.csv           # Sample recruiter CSV file
│      sample_resume.pdf       # Sample candidate PDF resume
│
├── parsers/
│      __init__.py
│      base_parser.py          # Abstract base parser & custom exceptions
│      csv_parser.py           # Parser for recruiter CSVs
│      resume_parser.py        # Parser for Resume PDFs
│
├── extractors/
│      __init__.py
│      regex_patterns.py       # Reusable regex patterns (emails, phones, URLs)
│      resume_extractor.py     # Heuristics and text segmenters for resumes
│
├── models/
│      __init__.py
│      candidate.py            # Unified candidate model and CanonicalCandidate
│      experience.py           # Structured professional experience dataclass
│      education.py            # Structured education details dataclass
│
├── transformers/
│      __init__.py
│      base_normalizer.py      # Abstract BaseNormalizer interface
│      phone_normalizer.py     # Phone standardizer (digits-only, preserves +)
│      email_normalizer.py     # Lowercases and trims email values
│      skill_normalizer.py     # Maps raw skills to canonical names (e.g. cpp -> C++)
│      company_normalizer.py   # Cleans legal suffixes and resolves abbreviations
│      date_normalizer.py      # Standardizes date strings to YYYY-MM
│      text_normalizer.py      # Handles whitespaces and capitalization formatting
│      normalization_pipeline.py # Orchestrates normalizers and deduplicates profiles
│
├── merger/
│      __init__.py
│      candidate_merger.py     # Coordinates profile merging
│      conflict_resolver.py    # Resolves scalar conflicts via source priorities
│      confidence_engine.py    # Assigns and calculates highest confidence scores
│      provenance_tracker.py   # Records original source file origins
│
├── tests/
│      test_csv_parser.py      # Part 1: CSV parser test suite
│      test_resume_parser.py   # Part 1: PDF parser test suite
│      test_normalization.py   # Part 2: Normalizers & pipeline test suite
│      test_merge.py           # Part 2: Merging (union/append) test suite
│      test_conflict_resolution.py # Part 2: Priorities & confidence test suite
│
├── utils/
│      __init__.py
│      file_utils.py           # Filesystem helper utilities
│      logger.py               # Custom Stream Logger configuration
│
├── main.py                    # CLI application entrypoint
├── requirements.txt           # Main dependency list
└── README.md                  # Project documentation
```

---

## Requirements

The project targets Python 3.11+ and uses the following dependencies:
* `pdfplumber` (for PDF text extraction)
* `pandas` (for CSV loading and column verification)
* `pytest` (for unit testing)
* `python-docx` (Word document parsing support)
* `PyPDF2` (additional PDF operations support)

---

## Installation

Create a virtual environment and install the dependencies:

```bash
# 1. Create a virtual environment
python3 -m venv .venv

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Install required packages
pip install -r requirements.txt
```

---

## How to Run

### Execute the CLI Pipeline

Run the CLI using the Python environment. It reads the inputs, parses, normalizes, merges, and displays the Canonical Candidate Profile:

```bash
python main.py
```

### Run Unit Tests

Execute the full test suite with `pytest`:

```bash
python -m pytest
```

---

## How the Transformation Engine Works

### 1. Normalization Pipeline
* **Phone**: Strips non-digit chars, preserving leading `+` country codes.
* **Email**: Lowercases and strips surrounding spaces.
* **Skill**: Maps aliases (e.g., `cpp`/`c plus plus` -> `C++`, `py` -> `Python`).
* **Company**: Removes legal suffixes (e.g. `LLC`, `Inc.`) and resolves acronyms (e.g., `AWS` -> `Amazon Web Services`).
* **Date**: Parses strings like `Jan 2024`, `01/2024`, and `2024 January` to `2024-01`.
* **Experience & Education**: Parses raw lines into structured dataclass objects (`Experience`, `Education`) containing fields for company/school, job/degree, start/end dates, and raw text.
* **Deduplication**: Automatically removes duplicate elements from lists (emails, phones, skills) using normalized values.

### 2. Merger
* **List Fields**: Merges using `UNION` rules (unique elements collected across all sources).
* **Work/Education Fields**: Merges using `APPEND` rules (concatenates history listings from all sources).
* **Scalar Fields**: Merges using `Conflict Resolution` rules. If values differ, it selects the higher-priority source.

### 3. Conflict Resolution & Confidence
* **Priority Rule**: Set in `merger/conflict_resolver.py`. Currently configured as `Recruiter CSV` > `Resume PDF`.
* **Confidence Calculation**: Recruiter CSV values start with `1.00` confidence, and Resume PDF values start with `0.90`. When merging, the system selects the highest confidence score among contributing values.

### 4. Provenance Tracking
* Every attribute in the final profile is wrapped in a `FieldMetadata` object containing:
  * `value`: The normalized, merged scalar or list value.
  * `confidence`: The calculated confidence score.
  * `sources`: A list of original source filenames that contributed to that value.

---

## Canonical Candidate Profile Schema

The output of the merger is a single `CanonicalCandidate` dataclass object, structured as follows:

```text
CanonicalCandidate
├── full_name       : FieldMetadata(value="John Doe", confidence=1.00, sources=["recruiter.csv"])
├── emails          : FieldMetadata(value=["john@gmail.com", "jane@gmail.com"], confidence=1.00, sources=["recruiter.csv", "sample_resume.pdf"])
├── phones          : FieldMetadata(value=["9876543210"], confidence=1.00, sources=["recruiter.csv"])
├── headline        : FieldMetadata(value="", confidence=0.00, sources=[])
├── current_company : FieldMetadata(value="Google", confidence=1.00, sources=["recruiter.csv"])
├── title           : FieldMetadata(value="SDE", confidence=1.00, sources=["recruiter.csv"])
├── skills          : FieldMetadata(value=["Python", "C++", "Docker"], confidence=0.90, sources=["sample_resume.pdf"])
├── experience      : FieldMetadata(value=[Experience(...)], confidence=0.90, sources=["sample_resume.pdf"])
└── education       : FieldMetadata(value=[Education(...)], confidence=0.90, sources=["sample_resume.pdf"])
```