import pytest
from extractors.resume_extractor import ResumeExtractor
from models.project import Project
from transformers.skill_normalizer import SkillNormalizer


def test_project_extraction_from_grouped_entry():
    """Project.from_raw_text should split a grouped project entry into structured fields."""
    raw = "ProctorAI, React, Flask, MediaPipe, YOLOv8 10/2025 – 11/2025 | Built an AI-powered exam proctoring system."
    project = Project.from_raw_text(raw)

    assert project.project_name == "ProctorAI"
    assert project.start_date == "10/2025"
    assert project.end_date == "11/2025"
    assert "Built an AI-powered exam proctoring system." in project.description
    assert project.raw_text == raw


def test_project_section_is_extracted_into_sections_dict():
    """The 'Projects' heading should route subsequent lines into the projects section."""
    text = (
        "Projects\n"
        "Gym Website, React, Node.js, MongoDB 2025 – 2025\n"
        "Built a full-stack gym management platform.\n"
    )
    sections = ResumeExtractor.extract_sections(text)

    assert any("Gym Website" in line for line in sections["projects"])
    projects = ResumeExtractor.extract_projects(sections)
    assert len(projects) == 1
    assert "Gym Website" in projects[0]


def test_skill_section_headings_are_never_extracted_as_skills():
    """Known section sub-headings (Languages, Tools, Backend / Development, etc.)
    must never appear in the extracted skills list, only the actual technologies."""
    text = (
        "Skills\n"
        "Languages\n"
        "C, C++, Java, Python, JavaScript\n"
        "Backend / Development\n"
        "Node.js, Express.js, React.js, REST APIs, SQL, MongoDB\n"
        "Core Subjects\n"
        "DSA, OOP, DBMS, Operating Systems, Computer Networks\n"
    )
    sections = ResumeExtractor.extract_sections(text)
    skills = ResumeExtractor.extract_skills(text, sections)

    forbidden_headings = {"languages", "backend / development", "core subjects", "tools"}
    assert not any(s.lower().strip() in forbidden_headings for s in skills)

    for expected in ["C++", "Java", "Python", "Node.js", "DSA", "OOP", "DBMS"]:
        assert any(expected.lower() in s.lower() for s in skills), f"Missing skill: {expected}"


def test_glued_section_headings_are_stripped_from_skill_lines():
    """Some PDF layouts merge two adjacent headings onto a single line with no
    separator (e.g. 'Languages Core Subjects'). These must not leak into skills."""
    text = (
        "Skills\n"
        "Languages Core Subjects\n"
        "Python, C++\n"
    )
    sections = ResumeExtractor.extract_sections(text)
    skills = ResumeExtractor.extract_skills(text, sections)

    assert "Languages Core Subjects" not in skills
    assert not any("core subjects" in s.lower() for s in skills)


def test_advanced_skill_discovery_from_project_and_experience_text():
    """Skills should also be discovered when they appear inside project or
    experience descriptions, not just under an explicit Skills heading."""
    text = (
        "Projects\n"
        "ProctorAI, 10/2025 – 11/2025\n"
        "Built using React, Flask, MediaPipe, YOLOv8, and OpenCV for real-time monitoring.\n"
        "Experience\n"
        "PRISM Intern at Samsung 01/2026 – Present\n"
        "Built compiler instrumentation passes using LLVM and Docker-based test environments.\n"
    )
    sections = ResumeExtractor.extract_sections(text)
    skills = ResumeExtractor.extract_skills(text, sections)

    for expected in ["React", "Flask", "MediaPipe", "YOLOv8", "OpenCV", "LLVM", "Docker"]:
        assert any(expected.lower() == s.lower() for s in skills), f"Missing discovered skill: {expected}"


def test_skill_normalizer_loads_configurable_mapping():
    """SkillNormalizer should load its canonical mapping from config/skill_mapping.json
    and correctly canonicalize known variants."""
    normalizer = SkillNormalizer()

    assert normalizer.normalize("React.js") == "React"
    assert normalizer.normalize("ReactJS") == "React"
    assert normalizer.normalize("NodeJS") == "Node.js"
    assert normalizer.normalize("JS") == "JavaScript"
    assert normalizer.normalize("MongoDB Tools") == "MongoDB"
    assert normalizer.normalize("Computer Networks (CN)") == "Computer Networks"
    assert normalizer.normalize("Computer Organization & Architecture (COA)") == "Computer Organization & Architecture"
    assert normalizer.normalize("Operating Systems") == "OS"
    assert normalizer.normalize("C Plus Plus") == "C++"


def test_skill_normalizer_falls_back_when_config_missing():
    """If the config file path doesn't exist, the normalizer should fall back to a
    built-in default mapping rather than raising an error."""
    normalizer = SkillNormalizer(mapping_path="/nonexistent/path/skill_mapping.json")
    assert normalizer.normalize("python") == "Python"
