"""
Tests for template-independence / generalization improvements.

Covers:
  - Section detection with non-standard / synonym heading names
  - Technology extraction from narrative project description text
  - Project grouping across different resume styles (tech-line, bullets-only,
    duration-on-own-line)
"""

from extractors.resume_extractor import ResumeExtractor, extract_technologies_from_text
from models.project import Project


class TestSectionSynonyms:

    def test_work_experience_and_internships_heading(self):
        text = (
            "John Doe\n"
            "Work Experience & Internships\n"
            "Software Engineer Intern, Acme Corp 01/2024 - Present\n"
            "Built internal tooling for the platform team.\n"
        )
        sections = ResumeExtractor.extract_sections(text)
        assert any("Software Engineer Intern" in l for l in sections["experience"])

    def test_technical_skill_set_heading(self):
        text = (
            "Jane Doe\n"
            "Technical Skill Set\n"
            "Python, Java, React\n"
        )
        sections = ResumeExtractor.extract_sections(text)
        assert any("Python" in l for l in sections["skills"])

    def test_academic_projects_research_heading(self):
        text = (
            "Jane Doe\n"
            "Academic Projects & Research\n"
            "Smart Irrigation System\n"
            "Built a sensor based irrigation controller.\n"
        )
        sections = ResumeExtractor.extract_sections(text)
        assert any("Smart Irrigation System" in l for l in sections["projects"])

    def test_educational_background_heading(self):
        text = (
            "Jane Doe\n"
            "Educational Background\n"
            "B.Tech, Computer Science, XYZ University, 2020 - 2024\n"
        )
        sections = ResumeExtractor.extract_sections(text)
        assert any("B.Tech" in l for l in sections["education"])

    def test_body_text_not_misclassified_as_heading(self):
        """A short, comma-free sentence inside a description shouldn't get
        reclassified as a new section just because it contains a signal word."""
        text = (
            "Jane Doe\n"
            "Projects\n"
            "Inventory Manager\n"
            "Worked on inventory project tracking\n"
            "Used Django and React for the project\n"
        )
        sections = ResumeExtractor.extract_sections(text)
        # Both lines should remain inside "projects", not get reclassified.
        assert len(sections["projects"]) >= 3


class TestTechFromDescription:

    def test_extracts_react_and_flask(self):
        techs = extract_technologies_from_text("Built using React and Flask")
        lowered = [t.lower() for t in techs]
        assert "react" in lowered
        assert "flask" in lowered

    def test_extracts_opencv_and_python(self):
        techs = extract_technologies_from_text("Implemented with OpenCV and Python")
        lowered = [t.lower() for t in techs]
        assert "opencv" in lowered
        assert "python" in lowered

    def test_project_technology_stack_includes_description_tech(self):
        entry = {
            "header": "Smart Attendance System",
            "tech_line": None,
            "description": [
                "Built using React and Flask for the web dashboard.",
                "Implemented face recognition with OpenCV and Python.",
            ],
            "raw_lines": ["Smart Attendance System"],
        }
        proj = Project.from_dict(entry)
        lowered = [t.lower() for t in proj.technology_stack]
        for expected in ("react", "flask", "opencv", "python"):
            assert expected in lowered

    def test_explicit_tech_line_not_duplicated(self):
        entry = {
            "header": "Smart Attendance System",
            "tech_line": "React, Python",
            "description": ["Built using React and Python end to end."],
            "raw_lines": ["Smart Attendance System"],
        }
        proj = Project.from_dict(entry)
        lowered = [t.lower() for t in proj.technology_stack]
        assert lowered.count("react") == 1
        assert lowered.count("python") == 1


class TestProjectStyles:

    def test_style_a_name_tech_description(self):
        """Style A: Project Name / Technology line / Description."""
        lines = [
            "Portfolio Website",
            "React, Tailwind CSS",
            "Designed and deployed a personal portfolio site.",
        ]
        entries = ResumeExtractor._group_project_entries(lines)
        assert len(entries) == 1
        assert entries[0]["header"] == "Portfolio Website"
        assert entries[0]["tech_line"] == "React, Tailwind CSS"

    def test_style_b_name_bullets(self):
        """Style B: Project Name followed directly by bullet points."""
        lines = [
            "Chat Application",
            "• Implemented real-time messaging using WebSockets",
            "• Added end-to-end encryption for messages",
        ]
        entries = ResumeExtractor._group_project_entries(lines)
        assert len(entries) == 1
        assert entries[0]["header"] == "Chat Application"
        assert len(entries[0]["description"]) == 2

    def test_style_c_name_duration_description(self):
        """Style C: Project Name / (Duration) / Description."""
        lines = [
            "Inventory Tracker",
            "(Jan 2024 - Mar 2024)",
            "Built a stock tracking tool for a local retailer.",
        ]
        entries = ResumeExtractor._group_project_entries(lines)
        # The duration line should not be split off as its own project entry.
        assert len(entries) == 1
        assert entries[0]["header"].startswith("Inventory Tracker")

    def test_multiple_projects_not_merged(self):
        lines = [
            "Project Alpha",
            "• Built the core data pipeline.",
            "Project Beta",
            "• Built a recommendation engine.",
        ]
        entries = ResumeExtractor._group_project_entries(lines)
        assert len(entries) == 2
        assert entries[0]["header"] == "Project Alpha"
        assert entries[1]["header"] == "Project Beta"
