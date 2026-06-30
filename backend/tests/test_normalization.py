import pytest
from transformers.phone_normalizer import PhoneNormalizer
from transformers.email_normalizer import EmailNormalizer
from transformers.skill_normalizer import SkillNormalizer
from transformers.company_normalizer import CompanyNormalizer
from transformers.date_normalizer import DateNormalizer
from transformers.text_normalizer import TextNormalizer
from transformers.normalization_pipeline import NormalizationPipeline

def test_phone_normalization():
    normalizer = PhoneNormalizer()
    assert normalizer.normalize("9876543210") == "9876543210"
    assert normalizer.normalize("+91 9876543210") == "+919876543210"
    assert normalizer.normalize("(987)6543210") == "9876543210"
    assert normalizer.normalize("987-654-3210") == "9876543210"
    assert normalizer.normalize("  ") == ""
    assert normalizer.normalize(None) == ""

def test_email_normalization():
    normalizer = EmailNormalizer()
    assert normalizer.normalize("John@gmail.com") == "john@gmail.com"
    assert normalizer.normalize(" JOHN@gmail.com  ") == "john@gmail.com"
    assert normalizer.normalize("") == ""

def test_skill_normalization():
    normalizer = SkillNormalizer()
    assert normalizer.normalize("cpp") == "C++"
    assert normalizer.normalize("c++") == "C++"
    assert normalizer.normalize("C Plus Plus") == "C++"
    assert normalizer.normalize("py") == "Python"
    assert normalizer.normalize("python") == "Python"
    assert normalizer.normalize("js") == "JavaScript"
    assert normalizer.normalize("reactjs") == "React"
    # Unmapped skills are trimmed but preserved
    assert normalizer.normalize("  Docker  ") == "Docker"

def test_company_normalization():
    normalizer = CompanyNormalizer()
    assert normalizer.normalize("Google LLC") == "Google"
    assert normalizer.normalize("Google Inc.") == "Google"
    assert normalizer.normalize("Google, Inc.") == "Google"
    assert normalizer.normalize("AWS") == "Amazon Web Services"
    assert normalizer.normalize("Amazon Web Services") == "Amazon Web Services"
    assert normalizer.normalize("Microsoft Corporation") == "Microsoft"

def test_date_normalization():
    normalizer = DateNormalizer()
    assert normalizer.normalize("Jan 2024") == "2024-01"
    assert normalizer.normalize("01/2024") == "2024-01"
    assert normalizer.normalize("2024 January") == "2024-01"
    assert normalizer.normalize("2024-01") == "2024-01"
    assert normalizer.normalize("2024-1") == "2024-01"
    assert normalizer.normalize("2024") == "2024-01"

def test_text_normalization():
    normalizer = TextNormalizer()
    assert normalizer.normalize("  John    Doe  ") == "John Doe"
    assert normalizer.normalize_name("john doe") == "John Doe"

def test_normalization_pipeline():
    pipeline = NormalizationPipeline()
    raw_cand = {
        "full_name": "jane smith",
        "emails": ["JANE@gmail.com", "JANE@gmail.com"],  # Duplicate
        "phones": ["123-456-7890", "(123) 456-7890"],   # Duplicate
        "headline": "  Engineer  ",
        "current_company": "Google LLC",
        "title": "SDE",
        "skills": ["py", "python", "aws"],              # Duplicate skills
        "experience": ["Senior Software Engineer at Amazon (2022 - Present)"],
        "education": ["B.S. in CS - UC Berkeley (2014 - 2018)"],
        "source": "resume.pdf"
    }
    
    norm = pipeline.normalize_candidate(raw_cand)
    
    assert norm["full_name"] == "Jane Smith"
    assert norm["emails"] == ["jane@gmail.com"] # Deduplicated
    assert norm["phones"] == ["1234567890"]    # Deduplicated
    assert norm["current_company"] == "Google"
    assert norm["skills"] == ["Python", "Amazon Web Services"] # Deduplicated & Normalized
    assert len(norm["experience"]) == 1
    assert norm["experience"][0].company == "Amazon"
    assert norm["experience"][0].end_date == "Present"
    assert norm["education"][0].school == "UC Berkeley"
