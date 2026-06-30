import pytest

from models.candidate import CanonicalCandidate, CandidateField
from models.experience import Experience
from models.education import Education
from models.project import Project


@pytest.fixture
def sample_canonical_candidate():
    return CanonicalCandidate(
        full_name=CandidateField("Jane Doe", 0.95, ["resume.pdf", "recruiter.csv"]),
        emails=CandidateField(["jane@example.com", "jane@example.com"], 0.9, ["resume.pdf"]),
        phones=CandidateField(["9876543210"], 0.9, ["recruiter.csv"]),
        headline=CandidateField("Backend Engineer", 0.8, ["resume.pdf"]),
        current_company=CandidateField("Acme Corp", 0.8, ["recruiter.csv"]),
        title=CandidateField("Senior Engineer", 0.8, ["recruiter.csv"]),
        skills=CandidateField(["Python", "react", "SQL", "python"], 0.85, ["resume.pdf"]),
        experience=CandidateField(
            [
                Experience(
                    raw_text="Senior Engineer, Acme Corp 01/2022 - Present",
                    title="Senior Engineer",
                    company="Acme Corp",
                    location="Bengaluru",
                    start_date="01/2022",
                    end_date="Present",
                    description=["Led the backend platform team."],
                )
            ],
            0.9, ["resume.pdf"]
        ),
        education=CandidateField(
            [
                Education(
                    raw_text="B.E. Computer Science, XYZ University, 2018 - 2022",
                    degree="B.E.",
                    specialization="Computer Science",
                    institution="XYZ University",
                    cgpa="8.9",
                    start_date="2018",
                    end_date="2022",
                    description=[],
                )
            ],
            0.9, ["resume.pdf"]
        ),
        projects=CandidateField(
            [
                Project(
                    raw_text="Portfolio Website",
                    project_name="Portfolio Website",
                    technology_stack=["React", "Flask"],
                    description=["Built using React and Flask."],
                    start_date="01/2023",
                    end_date="03/2023",
                )
            ],
            0.85, ["resume.pdf"]
        ),
    )
