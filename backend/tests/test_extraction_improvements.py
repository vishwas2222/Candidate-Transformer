"""
Tests for Improvement 7: comprehensive extraction quality tests.

Covers:
  - Project extraction (name, technology, description, dates)
  - Experience extraction (bullets, location, title, company)
  - Education metadata (CGPA, percentage, description)
  - Skill filtering, discovery, and normalization
"""

import pytest
from extractors.resume_extractor import ResumeExtractor
from models.project import Project
from models.experience import Experience
from models.education import Education
from transformers.skill_normalizer import SkillNormalizer


# ─── helpers ───────────────────────────────────────────────────────────────────

def make_sections(text: str) -> dict:
    return ResumeExtractor.extract_sections(text)


# ══════════════════════════════════════════════════════════════════════════════
# PROJECT EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

class TestProjectExtraction:

    def test_project_name_is_extracted(self):
        """Project.from_dict should pull project_name from the entry header."""
        entry = {
            "header": "ProctorAI",
            "tech_line": "React, Flask, Python, MediaPipe, YOLOv8",
            "description": ["Built an AI-powered proctoring system."],
            "raw_lines": ["ProctorAI", "React, Flask, Python, MediaPipe, YOLOv8",
                          "Built an AI-powered proctoring system."],
        }
        proj = Project.from_dict(entry)
        assert proj.project_name == "ProctorAI"

    def test_technology_stack_extracted_from_tech_line(self):
        """Technologies from the dedicated tech_line are stored in technology_stack."""
        entry = {
            "header": "ProctorAI",
            "tech_line": "React, Flask, Python, MediaPipe, YOLOv8",
            "description": [],
            "raw_lines": [],
        }
        proj = Project.from_dict(entry)
        assert "React" in proj.technology_stack
        assert "Flask" in proj.technology_stack
        assert "YOLOv8" in proj.technology_stack

    def test_technology_stack_extracted_from_inline_header(self):
        """Technologies appended after a comma in the header are also captured."""
        entry = {
            "header": "Library Management System, Node.js, Express.js, MySQL 02/2025 – 04/2025",
            "tech_line": "",
            "description": [],
            "raw_lines": [],
        }
        proj = Project.from_dict(entry)
        assert proj.project_name == "Library Management System"
        assert any("Node" in t for t in proj.technology_stack)
        assert proj.start_date == "02/2025"
        assert proj.end_date == "04/2025"

    def test_project_description_is_list_of_bullets(self):
        """Each bullet point should become a separate item in description[]."""
        entry = {
            "header": "Swift ride",
            "tech_line": "",
            "description": [
                "Developed an Uber-like ride booking system.",
                "Implemented trip lifecycle management.",
                "Integrated in-ride essentials ordering feature.",
            ],
            "raw_lines": [],
        }
        proj = Project.from_dict(entry)
        assert len(proj.description) == 3
        assert proj.description[0] == "Developed an Uber-like ride booking system."

    def test_project_dates_extracted_from_header(self):
        """Dates in the header line should populate start_date and end_date."""
        entry = {
            "header": "ProctorAI, React, Flask 10/2025 – 11/2025",
            "tech_line": "",
            "description": [],
            "raw_lines": [],
        }
        proj = Project.from_dict(entry)
        assert proj.start_date == "10/2025"
        assert proj.end_date == "11/2025"

    def test_project_no_date_still_parsed(self):
        """Projects without date ranges should still be extracted correctly."""
        entry = {
            "header": "DB Visualizer (Database Schema Visualizer)",
            "tech_line": "",
            "description": ["Built a Python-based Database Visualizer."],
            "raw_lines": [],
        }
        proj = Project.from_dict(entry)
        assert "DB Visualizer" in proj.project_name
        assert proj.start_date == ""

    def test_project_section_routes_lines_into_sections_dict(self):
        """The 'Projects' heading should route subsequent lines into sections['projects']."""
        text = (
            "Projects\n"
            "Swift ride\n"
            "•Developed an Uber-like ride booking system.\n"
            "DB Visualizer (Database Schema Visualizer)\n"
            "•Built a Python-based Database Visualizer.\n"
        )
        sections = make_sections(text)
        assert len(sections["projects"]) >= 2

    def test_multiple_projects_extracted(self):
        """Two distinct project headers should produce two Project objects."""
        text = (
            "Projects\n"
            "Swift ride\n"
            "•Developed an Uber-like ride booking system.\n"
            "DB Visualizer (Database Schema Visualizer)\n"
            "•Built a Python-based Database Visualizer.\n"
        )
        sections = make_sections(text)
        proj_dicts = ResumeExtractor.extract_projects(sections)
        projects = [Project.from_dict(p) for p in proj_dicts]
        assert len(projects) == 2
        names = {p.project_name for p in projects}
        assert "Swift ride" in names
        assert "DB Visualizer (Database Schema Visualizer)" in names


# ══════════════════════════════════════════════════════════════════════════════
# EXPERIENCE EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

class TestExperienceExtraction:

    def test_experience_title_and_company_parsed(self):
        """Title and company should be correctly extracted from a header line."""
        entry = {
            "header": "PRISM Intern – Compiler Optimization Research, Samsung PRISM Program 01/2026 – Present",
            "description": [],
            "raw_lines": [],
        }
        exp = Experience.from_dict(entry)
        assert "PRISM Intern" in exp.title
        assert exp.start_date == "01/2026"
        assert exp.end_date.lower() in ("present", "Present")

    def test_experience_bullets_become_description_list(self):
        """Each bullet should be a separate string in description[]."""
        entry = {
            "header": "Senior Software Engineer at Amazon (2022 – Present)",
            "description": [
                "Led a team of 4 engineers.",
                "Reduced latency by 30%.",
                "Increased throughput by 50%.",
            ],
            "raw_lines": [],
        }
        exp = Experience.from_dict(entry)
        assert len(exp.description) == 3
        assert exp.description[0] == "Led a team of 4 engineers."

    def test_experience_location_extracted(self):
        """When a location word is appended to the company name, it's separated."""
        exp = Experience._parse_header(
            "PRISM Intern – Compiler Research, Samsung PRISM Program Bengaluru 01/2026 – Present"
        )
        title, company, location, start_date, end_date = exp
        # Location 'Bengaluru' should be separated or company should be recognised
        assert "Bengaluru" in location or "Bengaluru" in company

    def test_experience_at_pattern(self):
        """'Title at Company (Dates)' format should parse correctly."""
        entry = {
            "header": "Senior Software Engineer at Amazon (2022 - Present)",
            "description": ["Led a team."],
            "raw_lines": [],
        }
        exp = Experience.from_dict(entry)
        assert exp.title == "Senior Software Engineer"
        assert exp.company == "Amazon"
        assert exp.end_date.lower() in ("present", "Present")

    def test_experience_description_not_merged(self):
        """Bullets from multiple experiences should NOT be merged into one string."""
        exp1_desc = ["Built order processing system.", "Reduced latency by 30%."]
        exp2_desc = ["Maintained API services.", "Improved test coverage to 85%."]

        entry1 = {"header": "SDE at Amazon (2022 – Present)", "description": exp1_desc, "raw_lines": []}
        entry2 = {"header": "SDE at Microsoft (2020 – 2022)", "description": exp2_desc, "raw_lines": []}

        e1 = Experience.from_dict(entry1)
        e2 = Experience.from_dict(entry2)

        assert e1.description == exp1_desc
        assert e2.description == exp2_desc
        # Descriptions must be separate
        assert e1.description != e2.description


# ══════════════════════════════════════════════════════════════════════════════
# EDUCATION EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

class TestEducationExtraction:

    def test_cgpa_extracted_from_meta_lines(self):
        """CGPA should be parsed from meta lines like 'CGPA: 7.04/ 10'."""
        entry = {
            "header": "B.E., Information Science & Engineering, 2023 – 2027",
            "school_line": "B.M.S. College of Engineering (BMSCE)",
            "meta_lines": ["CGPA: 7.04/ 10"],
            "description": [],
            "raw_lines": [],
        }
        edu = Education.from_dict(entry)
        assert edu.cgpa == "7.04"

    def test_percentage_extracted_from_meta_lines(self):
        """Percentage should be parsed from meta lines like 'Percentage:96'."""
        entry = {
            "header": "12th, Sir mv pu college 2023",
            "school_line": None,
            "meta_lines": ["Percentage:96"],
            "description": [],
            "raw_lines": [],
        }
        edu = Education.from_dict(entry)
        assert edu.percentage == "96"

    def test_school_on_next_line_becomes_institution(self):
        """When school name is on its own line, it should populate institution."""
        entry = {
            "header": "B.E., Information Science & Engineering, 2023 – 2027",
            "school_line": "B.M.S. College of Engineering (BMSCE)",
            "meta_lines": [],
            "description": [],
            "raw_lines": [],
        }
        edu = Education.from_dict(entry)
        assert "B.M.S." in (edu.institution or "") or "BMSCE" in (edu.institution or "")

    def test_degree_extracted_from_comma_format(self):
        """First comma segment should become the degree."""
        entry = {
            "header": "B.E., Information Science & Engineering, 2023 – 2027",
            "school_line": "B.M.S. College of Engineering",
            "meta_lines": [],
            "description": [],
            "raw_lines": [],
        }
        edu = Education.from_dict(entry)
        assert edu.degree == "B.E."

    def test_specialization_extracted_from_comma_format(self):
        """Second comma segment should become the specialization."""
        entry = {
            "header": "B.E., Information Science & Engineering, 2023 – 2027",
            "school_line": "B.M.S. College of Engineering",
            "meta_lines": [],
            "description": [],
            "raw_lines": [],
        }
        edu = Education.from_dict(entry)
        assert "Information Science" in edu.specialization

    def test_education_description_preserved(self):
        """Remaining non-meta lines should appear in description[]."""
        entry = {
            "header": "B.E., CS, 2022 – 2026",
            "school_line": None,
            "meta_lines": [],
            "description": ["Relevant coursework: Algorithms, OS, Networks"],
            "raw_lines": [],
        }
        edu = Education.from_dict(entry)
        assert "Relevant coursework" in edu.description[0]

    def test_multiple_education_entries_extracted(self):
        """Three education entries (degree, 12th, 10th) should produce 3 Education objects."""
        text = (
            "Education\n"
            "B.E., Information Science & Engineering, 2023 – 2027\n"
            "B.M.S. College of Engineering (BMSCE)\n"
            "CGPA: 7.04/ 10\n"
            "12th, Sir mv pu college 2023\n"
            "Percentage:96\n"
            "10th, srn mehta English medium school\n"
            "2021\n"
            "Percentage:92\n"
        )
        sections = make_sections(text)
        edu_dicts = ResumeExtractor.extract_education(sections)
        educations = [Education.from_dict(e) for e in edu_dicts]
        assert len(educations) == 3


# ══════════════════════════════════════════════════════════════════════════════
# SKILL EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

class TestSkillExtraction:

    def test_section_headings_never_appear_as_skills(self):
        """Known headings (Languages, Tools, Backend / Development) must not be skills."""
        text = (
            "Skills\n"
            "Languages\n"
            "C, C++, Java, Python, JavaScript\n"
            "Backend / Development\n"
            "Node.js, Express.js, React.js, REST APIs, SQL, MongoDB\n"
            "Core Subjects\n"
            "DSA, OOP, DBMS, Operating Systems\n"
        )
        sections = make_sections(text)
        skills = ResumeExtractor.extract_skills(text, sections)
        forbidden = {"languages", "backend / development", "core subjects", "tools"}
        assert not any(s.lower().strip() in forbidden for s in skills)

    def test_actual_skills_still_present(self):
        """Actual technologies must appear in skills even with heading filtering."""
        text = (
            "Skills\n"
            "Languages\n"
            "C, C++, Java, Python, JavaScript\n"
        )
        sections = make_sections(text)
        skills = ResumeExtractor.extract_skills(text, sections)
        for expected in ["C++", "Java", "Python", "JavaScript"]:
            assert any(expected.lower() in s.lower() for s in skills), f"Missing: {expected}"

    def test_glued_heading_tokens_split(self):
        """'JavaScript DSA' from multi-column PDF must not appear as one skill."""
        text = (
            "Skills\n"
            "Languages Core Subjects\n"
            "C, C++, Java, Python, JavaScript DSA, OOP, DBMS\n"
        )
        sections = make_sections(text)
        skills = ResumeExtractor.extract_skills(text, sections)
        assert "JavaScript DSA" not in skills
        assert not any("core subjects" in s.lower() for s in skills)

    def test_technologies_discovered_from_project_text(self):
        """Technologies in project descriptions are inferred by Project.from_dict(),
        NOT by extract_skills().

        extract_skills() is now section-strict: it only processes lines that
        appear inside the Skills section.  Technologies mentioned in project
        bullets are attached to the Project object via extract_technologies_from_text()
        (called inside Project.from_dict()), which is a separate path from skills.

        This test verifies that extract_skills() correctly returns an empty list
        when the skills section is absent.
        """
        text = (
            "Projects\n"
            "ProctorAI 10/2025 – 11/2025\n"
            "Built using React, Flask, MediaPipe, YOLOv8, and OpenCV.\n"
        )
        sections = make_sections(text)
        # No Skills section → extract_skills must return []
        skills = ResumeExtractor.extract_skills(text, sections)
        assert skills == [], (
            "extract_skills() must not scan project/experience text; "
            f"got: {skills}"
        )

    def test_technologies_discovered_from_experience_text(self):
        """Technologies in experience bullets are NOT returned by extract_skills().

        The section-strict design means only the Skills section is processed.
        Technologies that appear only in the Experience section are not added
        to the skills list (they should be attached to Experience objects instead).
        """
        text = (
            "Experience\n"
            "PRISM Intern at Samsung 01/2026 – Present\n"
            "Implemented compiler passes using LLVM and Clang.\n"
        )
        sections = make_sections(text)
        skills = ResumeExtractor.extract_skills(text, sections)
        # No Skills section → must return []
        assert skills == [], (
            "extract_skills() must not scan experience text; "
            f"got: {skills}"
        )

    def test_skill_normalizer_configurable_mapping(self):
        """SkillNormalizer should canonicalize known variants."""
        n = SkillNormalizer()
        assert n.normalize("React.js") == "React"
        assert n.normalize("NodeJS") == "Node.js"
        assert n.normalize("JS") == "JavaScript"
        assert n.normalize("MongoDB Tools") == "MongoDB"

    def test_skill_normalizer_fallback_on_missing_config(self):
        """SkillNormalizer must not raise when config file is missing."""
        n = SkillNormalizer(mapping_path="/nonexistent/skill_mapping.json")
        result = n.normalize("python")
        assert isinstance(result, str)
        assert result  # non-empty
