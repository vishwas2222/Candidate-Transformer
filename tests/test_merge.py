import pytest
from merger.candidate_merger import CandidateMerger
from models.experience import Experience
from models.education import Education

def test_candidate_merger_lists():
    merger = CandidateMerger()
    
    # Real-world: recruiter.csv has name, email, phone, company, title but NO skills, experience, or education
    cand1 = {
        "full_name": "John Doe",
        "emails": ["john@gmail.com"],
        "phones": ["9876543210"],
        "headline": "Developer",
        "current_company": "Google",
        "title": "SDE",
        "skills": [],
        "experience": [],
        "education": [],
        "source": "recruiter.csv"
    }
    
    cand2 = {
        "full_name": "John Doe",
        "emails": ["john.doe@work.com", "john@gmail.com"], # duplicate email john@gmail.com
        "phones": ["1234567890"],
        "headline": "Lead Developer",
        "current_company": "Alphabet",
        "title": "Lead SDE",
        "skills": ["Python", "AWS"],
        "experience": [Experience(raw_text="Lead Developer at Alphabet", company="Alphabet", title="Lead Developer")],
        "education": [Education(raw_text="MS CS, MIT", school="MIT", degree="MS CS")],
        "source": "sample_resume.pdf"
    }
    
    cc = merger.merge(cand1, cand2)
    
    # Check List fields (Union mapping)
    assert cc.emails.value == ["john@gmail.com", "john.doe@work.com"]
    assert cc.phones.value == ["9876543210", "1234567890"]
    assert cc.skills.value == ["Python", "AWS"]
    
    # Check Append fields (concatenation)
    assert len(cc.experience.value) == 1
    assert cc.experience.value[0].company == "Alphabet"
    
    assert len(cc.education.value) == 1
    assert cc.education.value[0].school == "MIT"
    
    # Check list confidence (highest confidence source wins, CSV = 1.00, Resume = 0.90)
    assert cc.emails.confidence == 1.00
    assert cc.skills.confidence == 0.90 # Skills only in resume
    
    # Check list sources
    assert "recruiter.csv" in cc.emails.sources
    assert "sample_resume.pdf" in cc.emails.sources
    assert cc.skills.sources == ["sample_resume.pdf"]


def test_merge_duplicate_phone_numbers():
    """Identical phone numbers from both sources should collapse into a single entry."""
    merger = CandidateMerger()

    cand1 = {
        "full_name": "Jane Roe",
        "emails": [],
        "phones": ["9876543210"],
        "skills": [],
        "experience": [],
        "education": [],
        "source": "recruiter.csv",
    }
    cand2 = {
        "full_name": "Jane Roe",
        "emails": [],
        "phones": ["9876543210", "1112223333"],  # duplicate + a new number
        "skills": [],
        "experience": [],
        "education": [],
        "source": "sample_resume.pdf",
    }

    cc = merger.merge(cand1, cand2)

    assert cc.phones.value == ["9876543210", "1112223333"]
    assert cc.phones.value.count("9876543210") == 1
    assert "recruiter.csv" in cc.phones.sources
    assert "sample_resume.pdf" in cc.phones.sources


def test_merge_duplicate_emails():
    """Identical email addresses from both sources should collapse into a single entry."""
    merger = CandidateMerger()

    cand1 = {
        "full_name": "Jane Roe",
        "emails": ["jane@gmail.com"],
        "phones": [],
        "skills": [],
        "experience": [],
        "education": [],
        "source": "recruiter.csv",
    }
    cand2 = {
        "full_name": "Jane Roe",
        "emails": ["jane@gmail.com", "jane.roe@work.com"],  # duplicate + a new email
        "phones": [],
        "skills": [],
        "experience": [],
        "education": [],
        "source": "sample_resume.pdf",
    }

    cc = merger.merge(cand1, cand2)

    assert cc.emails.value == ["jane@gmail.com", "jane.roe@work.com"]
    assert cc.emails.value.count("jane@gmail.com") == 1


def test_merge_duplicate_skills():
    """Overlapping skills between sources should be unioned without duplicates."""
    merger = CandidateMerger()

    cand1 = {
        "full_name": "Jane Roe",
        "emails": [],
        "phones": [],
        "skills": ["Python", "SQL"],
        "experience": [],
        "education": [],
        "source": "recruiter.csv",
    }
    cand2 = {
        "full_name": "Jane Roe",
        "emails": [],
        "phones": [],
        "skills": ["SQL", "AWS"],  # "SQL" overlaps with cand1
        "experience": [],
        "education": [],
        "source": "sample_resume.pdf",
    }

    cc = merger.merge(cand1, cand2)

    assert cc.skills.value == ["Python", "SQL", "AWS"]
    assert cc.skills.value.count("SQL") == 1
    assert "recruiter.csv" in cc.skills.sources
    assert "sample_resume.pdf" in cc.skills.sources


def test_merge_conflicting_company_names():
    """When sources disagree on current_company, the higher-priority source should win
    (recruiter.csv outranks sample_resume.pdf), with conflict provenance preserved."""
    merger = CandidateMerger()

    cand1 = {
        "full_name": "Jane Roe",
        "emails": [],
        "phones": [],
        "current_company": "Google",
        "skills": [],
        "experience": [],
        "education": [],
        "source": "recruiter.csv",
    }
    cand2 = {
        "full_name": "Jane Roe",
        "emails": [],
        "phones": [],
        "current_company": "Alphabet Inc.",  # Conflicting value
        "skills": [],
        "experience": [],
        "education": [],
        "source": "sample_resume.pdf",
    }

    cc = merger.merge(cand1, cand2)

    # recruiter.csv has higher priority than sample_resume.pdf, so it should win
    assert cc.current_company.value == "Google"
    assert cc.current_company.sources == ["recruiter.csv"]
    assert cc.current_company.confidence == 1.00


def test_merge_projects_are_appended():
    """Projects from both sources should be concatenated (append rule), matching
    the treatment of experience/education entries."""
    from models.project import Project

    merger = CandidateMerger()

    cand1 = {
        "full_name": "Jane Roe",
        "emails": [],
        "phones": [],
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [Project(raw_text="Gym Website", project_name="Gym Website")],
        "source": "recruiter.csv",
    }
    cand2 = {
        "full_name": "Jane Roe",
        "emails": [],
        "phones": [],
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [Project(raw_text="PRISM", project_name="PRISM")],
        "source": "sample_resume.pdf",
    }

    cc = merger.merge(cand1, cand2)

    assert len(cc.projects.value) == 2
    assert {p.project_name for p in cc.projects.value} == {"Gym Website", "PRISM"}


def test_merge_with_missing_resume():
    """When the resume source fails to parse (file not found), the parser layer
    raises ParserFileNotFoundError and the caller skips it -- merge should still
    succeed using only the recruiter CSV data, as main.py does."""
    from parsers.resume_parser import ResumeParser
    from parsers.base_parser import ParserError

    merger = CandidateMerger()

    csv_data = {
        "full_name": "Jane Roe",
        "emails": ["jane@gmail.com"],
        "phones": ["9876543210"],
        "current_company": "Google",
        "title": "SDE",
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [],
        "source": "recruiter.csv",
    }

    resume_data = {}
    try:
        ResumeParser("does_not_exist.pdf").parse()
    except ParserError:
        resume_data = {}  # Gracefully skipped, matching main.py's behavior

    cc = merger.merge(csv_data, resume_data)

    assert cc.full_name.value == "Jane Roe"
    assert cc.emails.value == ["jane@gmail.com"]
    assert cc.emails.sources == ["recruiter.csv"]


def test_merge_with_missing_recruiter_csv():
    """When the recruiter CSV is missing, merge should still succeed using only
    resume data."""
    from models.experience import Experience

    merger = CandidateMerger()

    csv_data = {}
    resume_data = {
        "full_name": "Jane Roe",
        "emails": ["jane@resume.com"],
        "phones": [],
        "current_company": "",
        "title": "",
        "skills": ["Python"],
        "experience": [Experience(raw_text="SDE at Acme", company="Acme", title="SDE")],
        "education": [],
        "projects": [],
        "source": "sample_resume.pdf",
    }

    cc = merger.merge(csv_data, resume_data)

    assert cc.full_name.value == "Jane Roe"
    assert cc.skills.value == ["Python"]
    assert cc.skills.sources == ["sample_resume.pdf"]
    assert len(cc.experience.value) == 1


def test_merge_with_malformed_recruiter_csv(tmp_path):
    """A recruiter CSV missing required columns should raise ParserInvalidFormatError
    at the parser layer; merge should still succeed using only resume data, since
    the malformed source is skipped before reaching the merger."""
    from parsers.csv_parser import CSVParser
    from parsers.base_parser import ParserError

    merger = CandidateMerger()

    bad_csv = tmp_path / "bad_recruiter.csv"
    bad_csv.write_text("Name,Email,Phone\nJane Roe,jane@gmail.com,9876543210\n")  # missing Company/Title

    csv_data = {}
    try:
        CSVParser(str(bad_csv)).parse()
    except ParserError:
        csv_data = {}  # Gracefully skipped, matching main.py's behavior

    resume_data = {
        "full_name": "Jane Roe",
        "emails": ["jane@resume.com"],
        "phones": [],
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [],
        "source": "sample_resume.pdf",
    }

    cc = merger.merge(csv_data, resume_data)

    assert cc.full_name.value == "Jane Roe"
    assert cc.emails.value == ["jane@resume.com"]
    assert cc.emails.sources == ["sample_resume.pdf"]


def test_merge_with_empty_resume(tmp_path):
    """A 0-byte resume PDF should raise ParserEmptyFileError at the parser layer;
    merge should still succeed using only recruiter CSV data."""
    from parsers.resume_parser import ResumeParser
    from parsers.base_parser import ParserError

    merger = CandidateMerger()

    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_text("")

    resume_data = {}
    try:
        ResumeParser(str(empty_pdf)).parse()
    except ParserError:
        resume_data = {}  # Gracefully skipped, matching main.py's behavior

    csv_data = {
        "full_name": "Jane Roe",
        "emails": ["jane@gmail.com"],
        "phones": ["9876543210"],
        "current_company": "Google",
        "title": "SDE",
        "skills": [],
        "experience": [],
        "education": [],
        "projects": [],
        "source": "recruiter.csv",
    }

    cc = merger.merge(csv_data, resume_data)

    assert cc.full_name.value == "Jane Roe"
    assert cc.current_company.value == "Google"
    assert cc.current_company.sources == ["recruiter.csv"]
