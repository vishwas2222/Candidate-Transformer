# Multi-Source Candidate Data Transformer (Part 1)

An interview-ready, production-grade Python library for reading multiple structured and unstructured candidate sources and extracting key details into a unified dictionary structure.

## Project Overview

This module represents **Part 1 (Input & Data Extraction Layer)** of a multi-module Candidate Data Pipeline. It is solely responsible for loading candidate files, extracting relevant textual details using rules, heuristics, and regex patterns (without calling external AI/LLM models), and compiling this data into a standardized schema representation.

Key constraints respected:
* **No cleaning or normalization** is performed (e.g. phone formats are left unmodified, skills are not canonicalized).
* **No merging, deduplication, schema validation, confidence scoring, or provenance tracking** is implemented (reserved for future modules).
* **Robust error handling**: custom parser exceptions are raised for missing files, empty inputs, corrupted PDFs, and malformed CSV rows. It never crashes.

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
│      base_parser.py          # Abstract base parser class & custom exceptions
│      csv_parser.py           # Parser implementation for recruiter CSVs
│      resume_parser.py        # Parser implementation for Resume PDFs
│
├── extractors/
│      __init__.py
│      regex_patterns.py       # Reusable regex patterns (emails, phones, URLs)
│      resume_extractor.py     # Heuristics and text segmenters for resumes
│
├── models/
│      __init__.py
│      candidate.py            # Candidate dataclass modeling the target schema
│
├── tests/
│      test_csv_parser.py      # Unit tests for CSV parser
│      test_resume_parser.py   # Unit tests for Resume PDF parser
│
├── utils/
│      file_utils.py           # File helper utilities (existence, size, etc.)
│      logger.py               # Custom console logger configuration
│
├── main.py                    # CLI application entrypoint
├── requirements.txt           # Main dependency list
└── README.md                  # Project documentation
```

---

## Requirements

The project targets Python 3.11+ and uses the following external dependencies:
* `pdfplumber` (for high-fidelity PDF text extraction)
* `pandas` (for robust CSV loading and verification)
* `pytest` (for unit testing)
* `python-docx` (included for future Word document parsing support)
* `PyPDF2` (included for additional PDF operation support)

---

## Installation

Create a virtual environment and install the dependencies listed in `requirements.txt`:

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

### Execute the Parser Pipeline (CLI)

Run the CLI using the Python environment. It reads the sample CSV and Resume files in the `inputs/` directory and prints their unified schemas:

```bash
python main.py
```

### Run Unit Tests

Execute the test suite with `pytest` (making sure python has the project root in its path):

```bash
python -m pytest
```

---

## How Parsers Work

### 1. BaseParser & Custom Exceptions
All parsers inherit from `BaseParser` (defined in `parsers/base_parser.py`) and implement `load()` and `parse()`. Errors encountered are mapped to standard custom exceptions:
* `ParserFileNotFoundError`: The target file is missing.
* `ParserEmptyFileError`: The file exists but contains 0 bytes or contains no parseable records/text.
* `ParserInvalidFormatError`: The file is corrupted (PDF structure breaks) or has wrong columns (CSV schema mismatch).

### 2. CSV Parser
* Loads target CSVs using `pandas` (passing `dtype=str` to preserve exact representation and avoid float conversion issues).
* Checks for the presence of required headers: `Name`, `Email`, `Phone`, `Company`, `Title`.
* Extracts the first record and maps it to the standard dictionary schema.

### 3. Resume Parser
* Opens PDF documents using `pdfplumber` and extracts text from pages.
* Segments raw resume text into logical sections (`Experience`, `Education`, `Skills`, `Header`) by scanning for standard section headers (e.g. `"professional experience"`, `"academic background"`).
* Uses compiled regexes (e.g. `EMAIL_PATTERN`, `PHONE_PATTERN`) to extract contact details.
* Implements case-insensitive keywords and substring matching to extract candidate skills, ensuring exact text cases in the PDF are returned without modification.
* Returns lines belonging to the `Experience` and `Education` blocks as raw lists of strings.

---

## Unified Candidate Output Schema

Every parser returns exactly the following structure (no additional fields):

```json
{
    "full_name": "Jane Smith",
    "emails": ["jane.smith@gmail.com"],
    "phones": ["123-456-7890"],
    "headline": "",
    "current_company": "",
    "title": "",
    "skills": ["Python", "C++", "SQL", "Docker", "AWS", "Git"],
    "experience": [
        "Senior Software Engineer at Amazon (2022 - Present)",
        "- Led a team of 4 engineers to rebuild the order processing system using Python and AWS.",
        "- Reduced latency by 30% and increased throughput by 50%.",
        "Software Engineer at Microsoft (2020 - 2022)",
        "- Developed and maintained core API services using C++ and SQL.",
        "- Wrote unit tests and improved test coverage from 60% to 85%."
    ],
    "education": [
        "M.S. in Computer Science - Stanford University (2018 - 2020)",
        "B.S. in Computer Science - University of California, Berkeley (2014 - 2018)"
    ],
    "source": "sample_resume.pdf"
}
```

---

## Future Modules (Out of Scope for Part 1)
* **Normalizer**: Standardizing phone numbers to E.164 formats, normalizing skills to canonical synonyms (e.g., `cpp` -> `C++`), and correcting casing of names.
* **Merger**: Collating candidates across multiple files, deduplicating candidate entities, and handling attribute conflict resolution.
* **Confidence Scorer**: Calculating extraction and parser confidence scores based on text alignment indicators.
* **Provenance Tracker**: Keeping records of exact source lines and parser identifiers responsible for each field entry.
# Candidate-Transformer
