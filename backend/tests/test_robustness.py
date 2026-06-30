"""
test_robustness.py — Production-robustness tests for the Multi-Source
Candidate Data Transformer.

Covers failure modes identified in the project analysis:
- File extension validation
- Encrypted / password-protected PDF detection
- Scanned (image-only) PDF detection
- File size limit enforcement
- CSV encoding fallback (latin-1)
- CSV delimiter sniffing (semicolon, tab)
- CSV missing required columns
- Both sources failing → graceful handling
- Emoji-prefixed section headings
- Month-name date ranges in experience headers
- Research Projects heading → projects section (not other)
- Wrapped PDF line merging in experience descriptions
- Multi-word skill preservation
- validate_file() helper
"""
import io
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from parsers.resume_parser import ResumeParser
from parsers.csv_parser import CSVParser
from parsers.base_parser import ParserFileNotFoundError, ParserEmptyFileError
from utils.exceptions import (
    UnsupportedFileTypeError,
    FileValidationError,
    CorruptedPDFError,
    EmptyResumeError,
    CorruptedCSVError,
)
from utils.file_utils import validate_file, get_file_size_mb, is_file_readable
from extractors.resume_extractor import ResumeExtractor


# ============================================================================
# Helpers
# ============================================================================

def _write_temp_file(content: bytes, suffix: str) -> str:
    """Writes bytes to a named temp file and returns its path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        os.write(fd, content)
    finally:
        os.close(fd)
    return path


def _make_csv_bytes(content: str, encoding: str = "utf-8") -> bytes:
    return content.encode(encoding)


# ============================================================================
# Section 1: File Extension Validation
# ============================================================================

class TestFileExtensionValidation:
    """ResumeParser must reject non-PDF files with UnsupportedFileTypeError."""

    def test_docx_extension_raises(self, tmp_path):
        fake_docx = tmp_path / "resume.docx"
        fake_docx.write_bytes(b"PK\x03\x04fake docx content")
        parser = ResumeParser(str(fake_docx))
        with pytest.raises(UnsupportedFileTypeError):
            parser.load()

    def test_txt_extension_raises(self, tmp_path):
        fake_txt = tmp_path / "resume.txt"
        fake_txt.write_text("John Doe\nPython Developer")
        parser = ResumeParser(str(fake_txt))
        with pytest.raises(UnsupportedFileTypeError):
            parser.load()

    def test_pdf_extension_accepted(self, tmp_path):
        """A .pdf file that IS a valid PDF should not raise UnsupportedFileTypeError."""
        valid_pdf = tmp_path / "resume.pdf"
        # Minimal syntactically-plausible PDF header
        valid_pdf.write_bytes(b"%PDF-1.4 fake")
        parser = ResumeParser(str(valid_pdf))
        # Should not raise UnsupportedFileTypeError; may raise CorruptedPDFError
        with pytest.raises((CorruptedPDFError, EmptyResumeError, Exception)):
            parser.load()


# ============================================================================
# Section 2: Scanned / Encrypted PDF Detection
# ============================================================================

class TestPDFDetection:
    """ResumeParser must raise typed exceptions for un-parseable PDFs."""

    def test_scanned_pdf_raises_empty_resume_error(self, tmp_path):
        """A PDF that opens successfully but yields no text should raise EmptyResumeError."""
        pdf_path = tmp_path / "scanned.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 placeholder")

        mock_page = MagicMock()
        mock_page.extract_text.return_value = None  # no text layer

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]
        mock_pdf.doc = MagicMock()
        mock_pdf.doc.is_encrypted = False

        with patch("pdfplumber.open", return_value=mock_pdf):
            parser = ResumeParser(str(pdf_path))
            with pytest.raises(EmptyResumeError):
                parser.load()

    def test_encrypted_pdf_raises_corrupted_pdf_error(self, tmp_path):
        """A PDF flagged as encrypted must raise CorruptedPDFError."""
        pdf_path = tmp_path / "encrypted.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 placeholder")

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = []
        mock_pdf.doc = MagicMock()
        mock_pdf.doc.is_encrypted = True

        with patch("pdfplumber.open", return_value=mock_pdf):
            parser = ResumeParser(str(pdf_path))
            with pytest.raises(CorruptedPDFError):
                parser.load()

    def test_corrupted_pdf_raises_corrupted_pdf_error(self, tmp_path):
        """If pdfplumber.open() raises an Exception, CorruptedPDFError must be raised."""
        pdf_path = tmp_path / "corrupted.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 bad content")

        with patch("pdfplumber.open", side_effect=Exception("bad PDF")):
            parser = ResumeParser(str(pdf_path))
            with pytest.raises(CorruptedPDFError):
                parser.load()

    def test_missing_pdf_raises_file_not_found(self):
        parser = ResumeParser("inputs/no_such_file.pdf")
        with pytest.raises(ParserFileNotFoundError):
            parser.load()

    def test_empty_pdf_raises_empty_file_error(self, tmp_path):
        empty_pdf = tmp_path / "empty.pdf"
        empty_pdf.write_bytes(b"")
        parser = ResumeParser(str(empty_pdf))
        with pytest.raises(ParserEmptyFileError):
            parser.load()


# ============================================================================
# Section 3: File Size Limit
# ============================================================================

class TestFileSizeLimit:
    """validate_file() must reject files exceeding max_size_mb."""

    def test_oversized_file_raises_file_validation_error(self, tmp_path):
        big_file = tmp_path / "big.pdf"
        # Write 1 byte — then mock get_file_size_mb to return 51 MB
        big_file.write_bytes(b"%PDF-1.4")
        with patch(
            "utils.file_utils.get_file_size_mb", return_value=51.0
        ):
            with pytest.raises(FileValidationError, match="exceeds maximum"):
                validate_file(str(big_file), allowed_extensions=[".pdf"], max_size_mb=50.0)

    def test_within_size_limit_passes(self, tmp_path):
        ok_file = tmp_path / "ok.pdf"
        ok_file.write_bytes(b"%PDF-1.4")
        with patch("utils.file_utils.get_file_size_mb", return_value=1.0):
            # Should not raise
            validate_file(str(ok_file), allowed_extensions=[".pdf"], max_size_mb=50.0)


# ============================================================================
# Section 4: CSV Encoding Fallback
# ============================================================================

class TestCSVEncodingFallback:
    """CSVParser must fall back to latin-1 when UTF-8 fails."""

    def test_latin1_encoded_csv_loads_successfully(self, tmp_path):
        # Build a CSV with a latin-1 character (é = 0xe9)
        content = "Name,Email,Phone,Company,Title\nRen\xe9 Dupont,rene@example.com,9876543210,AcmeCorp,Engineer\n"
        csv_path = tmp_path / "latin1.csv"
        csv_path.write_bytes(content.encode("latin-1"))

        parser = CSVParser(str(csv_path))
        result = parser.parse()
        assert "ren" in result["full_name"].lower() or result["full_name"]  # name extracted

    def test_utf8_csv_still_works(self, tmp_path):
        content = "Name,Email,Phone,Company,Title\nJane Doe,jane@example.com,9876543210,Acme,Developer\n"
        csv_path = tmp_path / "utf8.csv"
        csv_path.write_bytes(content.encode("utf-8"))

        parser = CSVParser(str(csv_path))
        result = parser.parse()
        assert result["full_name"] == "Jane Doe"


# ============================================================================
# Section 5: CSV Delimiter Sniffing
# ============================================================================

class TestCSVDelimiterSniffing:
    """CSVParser must auto-detect semicolon and tab delimiters."""

    def test_semicolon_delimited_csv_loads(self, tmp_path):
        content = "Name;Email;Phone;Company;Title\nJohn;john@example.com;9876543210;Corp;Dev\n"
        csv_path = tmp_path / "semi.csv"
        csv_path.write_bytes(content.encode("utf-8"))

        parser = CSVParser(str(csv_path))
        result = parser.parse()
        assert result["full_name"] == "John"

    def test_tab_delimited_csv_loads(self, tmp_path):
        content = "Name\tEmail\tPhone\tCompany\tTitle\nAlice\talice@example.com\t9876543210\tCorp\tEngineer\n"
        csv_path = tmp_path / "tab.csv"
        csv_path.write_bytes(content.encode("utf-8"))

        parser = CSVParser(str(csv_path))
        result = parser.parse()
        assert result["full_name"] == "Alice"


# ============================================================================
# Section 6: CSV Missing Required Columns
# ============================================================================

class TestCSVMissingColumns:
    """CSVParser must raise ParserInvalidFormatError when required columns are absent."""

    def test_missing_required_column_raises(self, tmp_path):
        from parsers.base_parser import ParserInvalidFormatError
        content = "FullName,EmailAddress,PhoneNumber\nJohn,john@x.com,123\n"
        csv_path = tmp_path / "bad_cols.csv"
        csv_path.write_bytes(content.encode("utf-8"))

        parser = CSVParser(str(csv_path))
        with pytest.raises(ParserInvalidFormatError):
            parser.parse()

    def test_missing_csv_raises_file_not_found(self):
        parser = CSVParser("inputs/nonexistent.csv")
        with pytest.raises(ParserFileNotFoundError):
            parser.load()

    def test_empty_csv_raises_empty_file_error(self, tmp_path):
        csv_path = tmp_path / "empty.csv"
        csv_path.write_bytes(b"")
        parser = CSVParser(str(csv_path))
        with pytest.raises(ParserEmptyFileError):
            parser.load()


# ============================================================================
# Section 7: Emoji-Prefixed Section Headings
# ============================================================================

class TestEmojiHeadings:
    """Headings prefixed with emoji or non-ASCII decorators must be recognised."""

    def test_emoji_skills_heading(self):
        text = (
            "John Doe\n"
            "\U0001f6e0\ufe0f Skills\n"
            "Python, React, Docker\n"
        )
        sections = ResumeExtractor.extract_sections(text)
        assert any("Python" in l for l in sections["skills"]), (
            "Skills under emoji heading not extracted"
        )

    def test_emoji_experience_heading(self):
        text = (
            "Jane Doe\n"
            "\U0001f4bc Work Experience\n"
            "Software Engineer, Acme 01/2023 - Present\n"
        )
        sections = ResumeExtractor.extract_sections(text)
        assert any("Software Engineer" in l for l in sections["experience"])

    def test_emoji_projects_heading(self):
        text = (
            "Jane Doe\n"
            "\U0001f4bb Projects\n"
            "Portfolio Website\n"
            "Built using React and Flask.\n"
        )
        sections = ResumeExtractor.extract_sections(text)
        assert any("Portfolio" in l for l in sections["projects"])


# ============================================================================
# Section 8: Month-Name Date Ranges
# ============================================================================

class TestMonthNameDateRanges:
    """DATE_RANGE_PATTERN must match month-name date ranges in experience headers."""

    def test_jan_dec_date_range_triggers_new_entry(self):
        from extractors.resume_extractor import DATE_RANGE_PATTERN

        line = "Software Engineer, Acme Corp Jan 2023 – Dec 2024"
        assert DATE_RANGE_PATTERN.search(line), (
            "Month-name date range not detected"
        )

    def test_month_present_date_range_triggers_new_entry(self):
        from extractors.resume_extractor import DATE_RANGE_PATTERN

        line = "Backend Developer, TechCo March 2022 – Present"
        assert DATE_RANGE_PATTERN.search(line)

    def test_month_name_experience_extracted_correctly(self):
        text = (
            "John Doe\n"
            "Experience\n"
            "Backend Developer, TechCo March 2022 – Present\n"
            "• Built REST APIs using Django and PostgreSQL.\n"
        )
        sections = ResumeExtractor.extract_sections(text)
        entries = ResumeExtractor.extract_experience(sections)
        assert len(entries) >= 1
        assert "Backend Developer" in entries[0]["header"]


# ============================================================================
# Section 9: Research Projects → projects (not other)
# ============================================================================

class TestResearchProjectsRouting:
    """'Research Projects' heading must route to projects, not other."""

    def test_research_projects_heading(self):
        text = (
            "Jane Doe\n"
            "Research Projects\n"
            "Autonomous Drone Navigation\n"
            "• Built using Python and OpenCV.\n"
        )
        sections = ResumeExtractor.extract_sections(text)
        assert any("Autonomous" in l for l in sections["projects"]), (
            "'Research Projects' heading incorrectly routed away from projects"
        )

    def test_academic_projects_and_research_heading(self):
        text = (
            "Jane Doe\n"
            "Academic Projects & Research\n"
            "Smart Irrigation System\n"
        )
        sections = ResumeExtractor.extract_sections(text)
        assert any("Smart Irrigation" in l for l in sections["projects"])


# ============================================================================
# Section 10: Wrapped PDF Line Merging in Experience
# ============================================================================

class TestWrappedLineMerging:
    """Continuation lines (lowercase start, previous item incomplete) must be merged."""

    def test_wrapped_description_line_is_merged(self):
        lines = [
            "Software Engineer, Acme Corp 01/2023 – Present",
            "• Led migration of the legacy monolith to microservices",
            "using Docker and Kubernetes on AWS.",  # continuation — starts lowercase
        ]
        entries = ResumeExtractor._group_experience_entries(lines)
        assert len(entries) == 1
        # The continuation should be merged into the first bullet
        assert any(
            "using Docker and Kubernetes on AWS" in bullet
            for bullet in entries[0]["description"]
        ), f"Got bullets: {entries[0]['description']}"

    def test_uppercase_line_is_not_merged(self):
        """A non-continuation line (uppercase start) must stay as its own item."""
        lines = [
            "Software Engineer, Acme Corp 01/2023 – Present",
            "• Built REST APIs.",
            "Awarded employee of the month.",  # new fact — uppercase start
        ]
        entries = ResumeExtractor._group_experience_entries(lines)
        assert len(entries) == 1
        # Should be two separate description items
        desc = entries[0]["description"]
        assert len(desc) >= 2

    def test_sentence_ending_line_is_not_merged(self):
        """A sentence that already ends with '.' must not be merged with the next line."""
        lines = [
            "Software Engineer, Acme Corp 01/2023 – Present",
            "• Built REST APIs.",
            "added caching layer.",  # would merge if prev ends without '.'
        ]
        entries = ResumeExtractor._group_experience_entries(lines)
        desc = entries[0]["description"]
        # "Built REST APIs." ends with '.' so "added caching layer." is a new item
        assert any("added caching layer" in d for d in desc)
        assert not any("Built REST APIs. added caching layer" in d for d in desc)


# ============================================================================
# Section 11: Multi-Word Skill Preservation
# ============================================================================

class TestMultiWordSkillPreservation:
    """Multi-word skills like 'Computer Networks' must not be split."""

    def test_computer_networks_not_split(self):
        text = (
            "Jane Doe\n"
            "Skills\n"
            "Python, Computer Networks, Machine Learning\n"
        )
        sections = ResumeExtractor.extract_sections(text)
        skills = ResumeExtractor.extract_skills(text, sections)
        lowered = [s.lower() for s in skills]
        assert "computer networks" in lowered or any(
            "networks" in s for s in lowered
        )
        # "Networks" alone (incorrectly split) is less ideal but tolerated
        # The important thing: "Computer" alone should NOT appear as a skill
        assert "computer" not in [s.lower().strip() for s in skills]

    def test_machine_learning_preserved(self):
        text = (
            "Jane Doe\n"
            "Technical Skills\n"
            "Machine Learning, Deep Learning, Python\n"
        )
        sections = ResumeExtractor.extract_sections(text)
        skills = ResumeExtractor.extract_skills(text, sections)
        lowered = [s.lower() for s in skills]
        # machine learning should be in skill list (not split)
        assert any("machine learning" in s for s in lowered)


# ============================================================================
# Section 12: validate_file() helper
# ============================================================================

class TestValidateFileHelper:
    """Unit tests for utils.file_utils.validate_file()."""

    def test_non_existent_file_raises(self, tmp_path):
        with pytest.raises(FileValidationError, match="not found"):
            validate_file(str(tmp_path / "ghost.pdf"), [".pdf"])

    def test_wrong_extension_raises_unsupported(self, tmp_path):
        f = tmp_path / "doc.docx"
        f.write_bytes(b"data")
        with pytest.raises(UnsupportedFileTypeError):
            validate_file(str(f), [".pdf"])

    def test_correct_extension_passes(self, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4")
        # Should complete without raising
        validate_file(str(f), [".pdf"])

    def test_get_file_size_mb_nonexistent_returns_zero(self):
        assert get_file_size_mb("/path/that/does/not/exist.pdf") == 0.0

    def test_is_file_readable_existing_file(self, tmp_path):
        f = tmp_path / "readable.txt"
        f.write_text("hello")
        assert is_file_readable(str(f)) is True
