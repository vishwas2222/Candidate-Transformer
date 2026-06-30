import re
from typing import List, Dict, Any
from extractors.regex_patterns import EMAIL_PATTERN, PHONE_PATTERN

# Keywords used to identify section boundaries in the resume text
EXPERIENCE_KEYWORDS = [
    "experience", "work history", "employment history",
    "professional experience", "work experience", "employment",
    "professional background", "internships", "internship"
]
EDUCATION_KEYWORDS = [
    "education", "academic profile", "academic background",
    "academic qualifications", "qualifications", "academic credentials",
    "academic history"
]
SKILLS_KEYWORDS = [
    "skills", "technical skills", "core competencies",
    "skills & expertise", "skills and technologies", "technologies",
    "technical expertise"
]
PROJECTS_KEYWORDS = [
    "projects", "personal projects", "academic projects",
    "side projects", "key projects", "project work"
]

# Section sub-headings that should NOT be treated as skills
SKILL_SECTION_HEADINGS = {
    "languages", "core subjects", "backend", "frontend", "backend / development",
    "development", "tools", "frameworks", "databases", "devops", "cloud",
    "web technologies", "programming languages", "soft skills", "other",
    "machine learning", "data science", "mobile", "testing", "infrastructure",
    "computer organization & architecture (coa)", "computer organization",
    "achievements", "profiles", "projects", "education", "experience",
    "technology stack", "tech stack",
}

# Sorted longest-first so multi-word headings are matched before shorter substrings
_SORTED_HEADINGS = sorted(SKILL_SECTION_HEADINGS, key=len, reverse=True)

# Date pattern to detect a date range anywhere in a line
# Matches inline (e.g. "01/2026 – Present") and parenthesized (e.g. "(2022 - Present)")
DATE_RANGE_PATTERN = re.compile(
    r'(?:\()?(?:\d{1,2}/)?(?:\d{4})\s*(?:[-–]|to)\s*(?:Present|Current|Now|(?:\d{1,2}/)?\d{4})\s*\)?\s*$',
    re.IGNORECASE
)

# Bullet character pattern
BULLET_PATTERN = re.compile(r'^[•\-*–►▸→]\s*')


class ResumeExtractor:
    """Extractor class for parsing candidate information from raw resume text."""

    @staticmethod
    def _preprocess_text(text: str) -> str:
        """Cleans up common PDF text extraction artifacts.

        Fixes:
        - Spaces inserted before '@' in email addresses (e.g. "user @gmail.com")
        - Removes zero-width spaces and other unicode artifacts

        Args:
            text (str): The raw extracted text.

        Returns:
            str: The cleaned text.
        """
        # Fix spaces before '@' in emails (common pdfplumber artifact)
        text = re.sub(r'(\S)\s+@\s*(\S)', r'\1@\2', text)
        # Remove zero-width spaces
        text = text.replace('\u200b', '').replace('\ufeff', '')
        return text

    @staticmethod
    def extract_sections(text: str) -> Dict[str, List[str]]:
        """Splits the raw text into logical sections based on keyword headers.

        Args:
            text (str): The full raw text of the resume.

        Returns:
            Dict[str, List[str]]: A dictionary mapping section names to their lines of text.
        """
        sections = {
            "header": [],
            "experience": [],
            "education": [],
            "skills": [],
            "projects": []
        }

        current_section = "header"
        lines = text.split('\n')

        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue

            # Clean punctuation for checking matching headers
            check_line = cleaned.lower().lstrip('#').strip().rstrip(':').strip()

            if check_line in EXPERIENCE_KEYWORDS:
                current_section = "experience"
                continue
            elif check_line in EDUCATION_KEYWORDS:
                current_section = "education"
                continue
            elif check_line in SKILLS_KEYWORDS:
                current_section = "skills"
                continue
            elif check_line in PROJECTS_KEYWORDS:
                current_section = "projects"
                continue
            elif current_section == "skills" and check_line in SKILL_SECTION_HEADINGS:
                # Sub-headings inside the Skills section (e.g. "Languages", "Core Subjects",
                # "Backend / Development") are labels, not new top-level resume sections.
                # Stay in "skills" so the technologies listed beneath them are still captured.
                continue
            elif len(check_line) < 30 and check_line in [
                "certifications", "summary", "objective",
                "interests", "languages", "publications", "awards",
                "achievements", "hobbies", "extracurricular", "volunteer"
            ]:
                # We skip non-core sections, routing their lines to "other"
                current_section = "other"
                continue

            if current_section in sections:
                sections[current_section].append(cleaned)

        return sections

    @staticmethod
    def _is_bullet_line(line: str) -> bool:
        """Returns True if the line starts with a bullet character."""
        return bool(BULLET_PATTERN.match(line.strip()))

    @staticmethod
    def _strip_bullet(line: str) -> str:
        """Strips leading bullet characters from a line."""
        return BULLET_PATTERN.sub('', line.strip()).strip()

    @staticmethod
    def _split_inline_bullets(line: str) -> List[str]:
        """Splits a line that has embedded mid-sentence bullet '•' characters.

        pdfplumber sometimes concatenates adjacent lines into one string, with
        bullet characters embedded mid-line, e.g.:
            "Built system. •Implemented feature. •Integrated component."

        Only splits on '•' (the true list bullet), NOT on arrows like '→' which
        are used as flow arrows in descriptions (e.g. "Request → Accept → Start").

        Args:
            line: Raw line from the PDF.

        Returns:
            List of clean sub-strings (one per bullet fragment).
        """
        # Only split on inline '•' characters
        parts = re.split(r'(?<!\A)\s*•\s*', line)
        result = []
        for part in parts:
            cleaned = part.strip().lstrip('•').strip()
            if cleaned:
                result.append(cleaned)
        return result if result else [line.strip()]


    @staticmethod
    def _is_continuation_line(line: str) -> bool:
        """Heuristic: returns True if line is a continuation of the previous sentence.

        A continuation line:
        - Does NOT end with a date range
        - Does NOT look like a new entry header (short standalone title-case line)
        - Starts with lowercase OR starts with a bullet
        """
        stripped = line.strip()
        if not stripped:
            return False
        # Lines starting with bullets are always content, not headers
        if BULLET_PATTERN.match(stripped):
            return True
        # Lines that start with lowercase are continuations
        if stripped[0].islower():
            return True
        return False

    @classmethod
    def _group_experience_entries(cls, lines: List[str]) -> List[Dict]:
        """Groups raw experience section lines into structured entry dicts.

        A new entry starts when a line:
        - Contains a date range (e.g. "Title, Company 01/2026 – Present")
        - OR looks like a standalone role header (short line, no bullet, ends with date or comma)

        All subsequent bullet/continuation lines belong to that entry's description.

        Args:
            lines: Raw lines from the experience section.

        Returns:
            List of dicts with keys: header, description, raw_lines
        """
        if not lines:
            return []

        entries = []
        current_header = None
        current_desc = []
        current_raw = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped in ['•', '-', '*', '–', '►', '▸']:
                continue

            is_date_header = bool(DATE_RANGE_PATTERN.search(stripped))
            is_bullet = cls._is_bullet_line(stripped)

            if is_date_header and not is_bullet:
                # Save previous entry
                if current_header is not None:
                    entries.append({
                        "header": current_header,
                        "description": current_desc,
                        "raw_lines": current_raw
                    })
                current_header = stripped
                current_desc = []
                current_raw = [stripped]
            elif is_bullet:
                # It's a description bullet
                clean_bullet = cls._strip_bullet(stripped)
                if clean_bullet:
                    if current_header is None:
                        # Orphan bullet — start an implicit entry
                        current_header = ""
                        current_raw = []
                    current_desc.append(clean_bullet)
                    current_raw.append(stripped)
            else:
                # Non-bullet, non-date-header line
                if current_header is not None:
                    # Continuation of description or sub-header
                    current_desc.append(stripped)
                    current_raw.append(stripped)
                else:
                    # Start a new entry with this as the header
                    current_header = stripped
                    current_desc = []
                    current_raw = [stripped]

        if current_header is not None:
            entries.append({
                "header": current_header,
                "description": current_desc,
                "raw_lines": current_raw
            })

        return entries

    @classmethod
    def _group_project_entries(cls, lines: List[str]) -> List[Dict]:
        """Groups raw project section lines into structured entry dicts.

        Projects often have NO date range on the header line. A new project starts when:
        - A short non-bullet line appears that is NOT a pure continuation
        - OR a line has a date range

        Bullet lines and continuation lines belong to the current project's description.
        The second line after a project header (if short and comma-separated) is treated
        as the technology stack.

        Args:
            lines: Raw lines from the projects section.

        Returns:
            List of dicts with keys: header, tech_line, description, raw_lines
        """
        if not lines:
            return []

        entries = []
        current_header = None
        current_tech_line = None
        current_desc = []
        current_raw = []
        awaiting_tech = False  # True right after a header is set

        def _looks_like_project_header(line: str) -> bool:
            """A project header is a short standalone line without a leading bullet.

            Heuristics:
            - No bullet prefix
            - Relatively short (< 120 chars)
            - Does not start with a lowercase letter (which would indicate continuation)
            - Not purely a percentage/CGPA/grade line
            """
            s = line.strip()
            if not s:
                return False
            if BULLET_PATTERN.match(s):
                return False
            if s[0].islower():
                return False
            if re.match(r'^(CGPA|Percentage|Grade|GPA)\s*:', s, re.IGNORECASE):
                return False
            return len(s) < 120

        def _looks_like_tech_line(line: str) -> bool:
            """A technology line is comma-separated with mostly short tokens."""
            s = line.strip()
            if BULLET_PATTERN.match(s):
                return False
            tokens = [t.strip() for t in s.split(',')]
            if len(tokens) < 2:
                return False
            avg_len = sum(len(t) for t in tokens) / len(tokens)
            return avg_len < 20

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped in ['•', '-', '*', '–', '►', '▸']:
                continue

            is_bullet = cls._is_bullet_line(stripped)
            is_date_header = bool(DATE_RANGE_PATTERN.search(stripped)) and not is_bullet

            # Case 1: Line with explicit date range → always a new entry header
            if is_date_header:
                if current_header is not None:
                    entries.append({
                        "header": current_header,
                        "tech_line": current_tech_line,
                        "description": current_desc,
                        "raw_lines": current_raw
                    })
                current_header = stripped
                current_tech_line = None
                current_desc = []
                current_raw = [stripped]
                awaiting_tech = True

            # Case 2: Bullet line → description content
            elif is_bullet:
                clean_bullet = cls._strip_bullet(stripped)
                if clean_bullet:
                    if current_header is None:
                        current_header = ""
                        current_raw = []
                    # Split inline bullets (pdfplumber may merge multiple bullets into one line)
                    sub_bullets = cls._split_inline_bullets(clean_bullet)
                    current_desc.extend(sub_bullets)
                    current_raw.append(stripped)
                    awaiting_tech = False

            # Case 3: Non-bullet, non-date line
            else:
                # Could be: project header, tech line, or description continuation
                if current_header is None:
                    # Start fresh entry
                    current_header = stripped
                    current_tech_line = None
                    current_desc = []
                    current_raw = [stripped]
                    awaiting_tech = True
                elif awaiting_tech and _looks_like_tech_line(stripped):
                    # Second line after header — treat as technology stack
                    current_tech_line = stripped
                    current_raw.append(stripped)
                    awaiting_tech = False
                elif _looks_like_project_header(stripped) and not current_desc:
                    # Looks like a new project name (no bullets seen yet for current)
                    # Check if we should start a new entry or treat as sub-info
                    # Heuristic: if current_header is already set and has content, new entry
                    if current_header:
                        entries.append({
                            "header": current_header,
                            "tech_line": current_tech_line,
                            "description": current_desc,
                            "raw_lines": current_raw
                        })
                        current_header = stripped
                        current_tech_line = None
                        current_desc = []
                        current_raw = [stripped]
                        awaiting_tech = True
                    else:
                        current_header = stripped
                        current_raw.append(stripped)
                elif _looks_like_project_header(stripped) and current_desc:
                    # New project after bullets
                    entries.append({
                        "header": current_header,
                        "tech_line": current_tech_line,
                        "description": current_desc,
                        "raw_lines": current_raw
                    })
                    current_header = stripped
                    current_tech_line = None
                    current_desc = []
                    current_raw = [stripped]
                    awaiting_tech = True
                else:
                    # Continuation description text (no bullet, not a new header)
                    # Still may have embedded bullets from PDF layout
                    sub_bullets = cls._split_inline_bullets(stripped)
                    current_desc.extend(sub_bullets)
                    current_raw.append(stripped)
                    awaiting_tech = False

        if current_header is not None:
            entries.append({
                "header": current_header,
                "tech_line": current_tech_line,
                "description": current_desc,
                "raw_lines": current_raw
            })

        return entries

    @classmethod
    def _group_education_entries(cls, lines: List[str]) -> List[Dict]:
        """Groups raw education section lines into structured entry dicts.

        Education entries can span multiple lines:
        - "B.E., Information Science & Engineering, 2023 – 2027"  (may have date inline)
        - "B.M.S. College of Engineering (BMSCE)"                (school on next line)
        - "CGPA: 7.04/ 10"
        - "12th, Sir mv pu college 2023"                         (single-year entry)
        - "Percentage:96"
        - "2021"                                                  (year continuation)

        A new entry starts when a line unambiguously looks like a degree/class header.

        Args:
            lines: Raw lines from the education section.

        Returns:
            List of dicts with keys: header, school_line, meta_lines, description, raw_lines
        """
        if not lines:
            return []

        entries = []
        current_header = None
        current_school = None
        current_meta = []   # CGPA, Percentage, Grade lines
        current_desc = []   # other description lines
        current_raw = []

        # Patterns for metadata lines
        CGPA_PAT = re.compile(r'(cgpa|gpa)\s*:', re.IGNORECASE)
        PCT_PAT = re.compile(r'percentage\s*:', re.IGNORECASE)
        GRADE_PAT = re.compile(r'grade\s*:', re.IGNORECASE)
        YEAR_PAT = re.compile(r'\b(19|20)\d{2}\b')
        STANDALONE_YEAR_PAT = re.compile(r'^\s*(19|20)\d{2}\s*$')

        def _is_meta_line(s: str) -> bool:
            return bool(CGPA_PAT.search(s) or PCT_PAT.search(s) or GRADE_PAT.search(s))

        # Tighter degree pattern — must match at start-of-string or after comma/space
        # so that "B.M.S." does NOT match (it requires the full abbreviated form).
        DEGREE_PAT = re.compile(
            r'(?:^|,\s*|\s)'
            r'(B\.E\b|B\.Tech\b|M\.Tech\b|M\.E\b|M\.S\b|B\.S\b|MBA\b|Ph\.D\b|'
            r'BCA\b|MCA\b|B\.Sc\b|M\.Sc\b|BE\b|BTech\b|MTech\b|BBA\b|'
            r'Class\s+X(?:II)?\b|10th\b|12th\b|Diploma\b|'
            r'Bachelor(?:\'s)?\b|Master(?:\'s)?\b)',
            re.IGNORECASE
        )

        def _looks_like_school_name(s: str) -> bool:
            """Heuristic: line has a school/college/university keyword."""
            if BULLET_PATTERN.match(s):
                return False
            if _is_meta_line(s):
                return False
            if s[0].islower():
                return False
            return bool(re.search(
                r'\b(college|university|school|institute|pu\s+college|institution|academy)\b',
                s, re.IGNORECASE
            ))

        def _looks_like_edu_header(s: str) -> bool:
            """A degree/class header has a recognizable degree keyword or a year.
            Degree keyword takes priority over school-name classification.
            Only pure school-name lines (no degree keyword) are excluded.
            """
            if BULLET_PATTERN.match(s):
                return False
            if _is_meta_line(s):
                return False
            if s[0].islower():
                return False
            if STANDALONE_YEAR_PAT.match(s):
                return False
            has_degree = bool(DEGREE_PAT.search(s))
            # Degree keyword always wins — even if line also has a school keyword
            if has_degree:
                return True
            has_year = bool(YEAR_PAT.search(s))
            # Year-only line: only a header if it doesn't look like a pure school name
            if has_year and not _looks_like_school_name(s):
                return True
            return False


        def _save_current():
            if current_header is not None:
                entries.append({
                    "header": current_header,
                    "school_line": current_school,
                    "meta_lines": list(current_meta),
                    "description": list(current_desc),
                    "raw_lines": list(current_raw)
                })

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped in ['•', '-', '*', '–']:
                continue

            is_bullet = cls._is_bullet_line(stripped)

            # Bullets -> description content
            if is_bullet:
                if current_header is not None:
                    current_desc.append(cls._strip_bullet(stripped))
                    current_raw.append(stripped)
                continue

            # Meta lines (CGPA, Percentage, Grade)
            if _is_meta_line(stripped):
                if current_header is not None:
                    current_meta.append(stripped)
                    current_raw.append(stripped)
                continue

            # Standalone year -> append to previous header as end_date continuation
            if STANDALONE_YEAR_PAT.match(stripped):
                if current_header is not None:
                    current_header = current_header.rstrip() + ' ' + stripped.strip()
                    current_raw.append(stripped)
                continue

            # Degree header line -> starts a new education entry
            # (checked BEFORE school_name so '12th, Sir mv pu college 2023' becomes a new entry)
            if _looks_like_edu_header(stripped):
                _save_current()
                current_header = stripped
                current_school = None
                current_meta = []
                current_desc = []
                current_raw = [stripped]
                continue

            # School name line -> group under current entry as school_line
            if (current_header is not None
                    and current_school is None
                    and _looks_like_school_name(stripped)):
                current_school = stripped
                current_raw.append(stripped)
                continue

            # Anything else: description or orphan
            if current_header is not None:
                current_desc.append(stripped)
                current_raw.append(stripped)
            else:
                current_header = stripped
                current_school = None
                current_meta = []
                current_desc = []
                current_raw = [stripped]

        _save_current()
        return entries

    @classmethod
    def extract_name(cls, text: str, sections: Dict[str, List[str]]) -> str:
        """Heuristic to extract candidate name (usually at the very top).

        Args:
            text (str): Full text of the resume.
            sections (Dict[str, List[str]]): The split sections of the resume.

        Returns:
            str: The extracted name, or empty string.
        """
        header_lines = sections.get("header", [])
        for line in header_lines:
            cleaned = line.strip()
            if len(cleaned) < 3:
                continue
            # Ignore lines containing typical contact info
            if "@" in cleaned or "http" in cleaned or "www." in cleaned:
                continue
            # Ignore lines with excessive numbers (dates, zip codes, phone numbers)
            if sum(c.isdigit() for c in cleaned) > 2:
                continue
            return cleaned

        # Fallback to the first non-empty line of the file
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines[:5]:
            if "@" not in line and "http" not in line and sum(c.isdigit() for c in line) <= 2 and len(line) >= 3:
                return line

        return ""

    @classmethod
    def extract_emails(cls, text: str) -> List[str]:
        """Extracts all email addresses found in the text.

        Pre-processes text to fix PDF artifacts before running regex.

        Args:
            text (str): Full text.

        Returns:
            List[str]: Found email addresses with spaces removed.
        """
        cleaned_text = cls._preprocess_text(text)
        emails = EMAIL_PATTERN.findall(cleaned_text)
        return [e.replace(' ', '') for e in emails]

    @classmethod
    def extract_phones(cls, text: str) -> List[str]:
        """Extracts all phone numbers found in the text.

        Args:
            text (str): Full text.

        Returns:
            List[str]: Found phone numbers.
        """
        return PHONE_PATTERN.findall(text)

    @classmethod
    def _is_section_heading(cls, text: str) -> bool:
        """Checks if a text fragment is a section sub-heading rather than an actual skill."""
        return text.lower().strip() in SKILL_SECTION_HEADINGS

    @classmethod
    def _strip_embedded_headings(cls, text: str) -> str:
        """Removes known section heading phrases embedded inside a line of text."""
        cleaned = text
        for heading in _SORTED_HEADINGS:
            pattern = re.compile(rf'(?<!\w){re.escape(heading)}(?!\w)', re.IGNORECASE)
            cleaned = pattern.sub(' ', cleaned)
        return re.sub(r'\s+', ' ', cleaned).strip()

    @classmethod
    def _split_glued_tokens(cls, token: str) -> List[str]:
        """Splits glued tokens like 'JavaScript DSA' into ['JavaScript', 'DSA'].

        Some PDFs merge adjacent items that should be separate skills.
        This splits on whitespace, but preserves known multi-word skill phrases.

        Args:
            token: A single skill candidate string.

        Returns:
            List of split skill strings.
        """
        # Multi-word skill phrases that must be kept together
        protected_phrases = {
            "javascript", "typescript", "postgresql", "mongodb",
            "tensorflow", "pytorch", "scikit", "opencv", "mediapipe",
            "yolov8", "yolo", "llvm", "clang", "github", "gitlab",
            # multi-word phrases
            "web technologies", "shell scripting", "machine learning",
            "deep learning", "natural language processing",
            "computer vision", "data science", "rest api", "rest apis",
            "operating systems", "computer networks", "data structures",
            "object oriented", "object-oriented", "shell script",
            "visual studio", "node.js", "express.js", "react.js",
        }
        lower = token.lower().strip()
        if lower in protected_phrases:
            return [token]

        # If token is a single word, return as-is
        words = token.split()
        if len(words) == 1:
            return [token]

        # Two-word phrases: split only if it looks like two concatenated skills
        # (i.e. both words are meaningful non-heading standalone skills)
        if len(words) >= 2:
            result = []
            for word in words:
                w = word.strip().rstrip('.')
                if w and not cls._is_section_heading(w):
                    result.append(w)
            return result if result else [token]

        return [token]


    @classmethod
    def extract_skills(cls, text: str, sections: Dict[str, List[str]]) -> List[str]:
        """Extracts skills from the skills section and scans the full text for keywords.

        Filters out section sub-headings (e.g. "Languages", "Tools", "Backend / Development")
        that should not appear as skills.

        Args:
            text (str): Full text of the resume.
            sections (Dict[str, List[str]]): Resume sections.

        Returns:
            List[str]: List of extracted skills.
        """
        extracted_skills = []

        # 1. Parse lines from the identified skills section
        skills_lines = sections.get("skills", [])
        for line in skills_lines:
            line_clean = line.strip().lstrip('•-*').strip()

            # Handles "Languages: Python, C++" or "Technologies: AWS, SQL"
            if ":" in line_clean:
                parts = line_clean.split(":", 1)
                skills_part = parts[1]
            else:
                skills_part = line_clean

            # Strip any known heading phrases glued onto this line
            skills_part = cls._strip_embedded_headings(skills_part)

            # Split by commas and semicolons
            for raw_skill in re.split(r'[,;]', skills_part):
                raw_clean = raw_skill.strip().rstrip('.').strip()
                # Split glued tokens (e.g. "JavaScript DSA" → ["JavaScript", "DSA"])
                sub_tokens = cls._split_glued_tokens(raw_clean)
                for skill_clean in sub_tokens:
                    skill_clean = skill_clean.strip()
                    if skill_clean and len(skill_clean) < 40 and not cls._is_section_heading(skill_clean):
                        extracted_skills.append(skill_clean)

        # 2. Scan the full text for common skills to ensure coverage
        common_keywords = [
            "python", "java", "c\\+\\+", "cpp", "c#", "go", "golang", "rust", "ruby",
            "php", "javascript", "typescript", "html", "css", "sql", "nosql", "mongodb",
            "postgresql", "mysql", "react", "angular", "vue", "node\\.js", "django",
            "flask", "fastapi", "spring", "aws", "azure", "gcp", "docker", "kubernetes",
            "git", "linux", "machine learning", "deep learning", "nlp", "tensorflow",
            "pytorch", "pandas", "numpy", "scikit-learn", "mediapipe", "yolov8", "yolo",
            "llvm", "clang", "opencv", "express\\.js", "express", "slam", "android",
            "openCV", "llvm", "rest api", "rest apis"
        ]

        for kw in common_keywords:
            pattern = re.compile(rf'\b{kw}\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                matched_text = match.group(0)
                if not any(s.lower() == matched_text.lower() for s in extracted_skills):
                    extracted_skills.append(matched_text)

        return extracted_skills

    @classmethod
    def extract_experience(cls, sections: Dict[str, List[str]]) -> List[Dict]:
        """Extracts and groups experience entries into structured dicts.

        Args:
            sections (Dict[str, List[str]]): The parsed sections.

        Returns:
            List[Dict]: Structured experience entry dicts.
        """
        raw_lines = sections.get("experience", [])
        return cls._group_experience_entries(raw_lines)

    @classmethod
    def extract_education(cls, sections: Dict[str, List[str]]) -> List[Dict]:
        """Extracts and groups education entries into structured dicts.

        Args:
            sections (Dict[str, List[str]]): The parsed sections.

        Returns:
            List[Dict]: Structured education entry dicts.
        """
        raw_lines = sections.get("education", [])
        return cls._group_education_entries(raw_lines)

    @classmethod
    def extract_projects(cls, sections: Dict[str, List[str]]) -> List[Dict]:
        """Extracts and groups project entries into structured dicts.

        Args:
            sections (Dict[str, List[str]]): The parsed sections.

        Returns:
            List[Dict]: Structured project entry dicts.
        """
        raw_lines = sections.get("projects", [])
        return cls._group_project_entries(raw_lines)
