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
