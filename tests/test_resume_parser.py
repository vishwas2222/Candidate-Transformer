import pytest
import os
from parsers.resume_parser import ResumeParser
from parsers.base_parser import (
    ParserFileNotFoundError,
    ParserEmptyFileError,
    ParserInvalidFormatError,
)
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def create_test_pdf(path, text_content):
    """Utility to programmatically build a standard PDF with the given text."""
    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    for line in text_content.split('\n'):
        if line.strip():
            story.append(Paragraph(line, styles['Normal']))
    doc.build(story)

def test_valid_resume(tmp_path):
    """Test parsing a valid candidate resume PDF."""
    pdf_path = tmp_path / "valid_resume.pdf"
    resume_text = (
        "Alice Cooper\n"
        "Email: alice@cooper.com\n"
        "Phone: 555-123-4567\n"
        "Skills\n"
        "Python, Java\n"
        "Experience\n"
        "Developer at Google\n"
        "Education\n"
        "BS CS, Stanford"
    )
    create_test_pdf(pdf_path, resume_text)
    
    parser = ResumeParser(str(pdf_path))
    data = parser.parse()
    
    assert data["full_name"] == "Alice Cooper"
    assert data["emails"] == ["alice@cooper.com"]
    assert data["phones"] == ["555-123-4567"]
    assert "Python" in data["skills"]
    assert "Java" in data["skills"]
    assert any("Developer at Google" in line for line in data["experience"])
    assert any("Stanford" in line for line in data["education"])
    assert data["source"] == "valid_resume.pdf"

def test_missing_resume():
    """Test that ParserFileNotFoundError is raised for a non-existent PDF."""
    parser = ResumeParser("does_not_exist.pdf")
    with pytest.raises(ParserFileNotFoundError):
        parser.parse()

def test_empty_resume(tmp_path):
    """Test that ParserEmptyFileError is raised for an empty (0 bytes) PDF."""
    pdf_path = tmp_path / "empty.pdf"
    pdf_path.write_text("")
    
    parser = ResumeParser(str(pdf_path))
    with pytest.raises(ParserEmptyFileError):
        parser.parse()

def test_corrupted_resume(tmp_path):
    """Test that ParserInvalidFormatError is raised for a corrupted PDF."""
    pdf_path = tmp_path / "corrupted.pdf"
    pdf_path.write_text("%PDF-1.4 but then garbage invalid data...")
    
    parser = ResumeParser(str(pdf_path))
    with pytest.raises(ParserInvalidFormatError):
        parser.parse()
