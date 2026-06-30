import re
from typing import List, Dict, Any
from extractors.regex_patterns import EMAIL_PATTERN, PHONE_PATTERN

# Keywords used to identify section boundaries in the resume text
EXPERIENCE_KEYWORDS = [
    "experience", "work history", "employment history", 
    "professional experience", "work experience", "employment",
    "professional background"
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
    "side projects", "key projects"
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

# Sorted longest-first so multi-word headings are matched before their shorter substrings
# (e.g. "core subjects" before "core") when stripping embedded headings from glued tokens.
_SORTED_HEADINGS = sorted(SKILL_SECTION_HEADINGS, key=len, reverse=True)

# Date pattern to detect lines ending with date ranges
# Matches both inline dates (e.g. "01/2026 – Present") and parenthesized dates (e.g. "(2022 - Present)")
DATE_RANGE_PATTERN = re.compile(
    r'(?:\()?(?:\d{1,2}/)?(?:\d{4})\s*(?:[-–]|to)\s*(?:Present|Current|Now|(?:\d{1,2}/)?\d{4})\s*\)?\s*$',
    re.IGNORECASE
)


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
                "interests", "languages", "publications", "awards"
            ]:
                # We skip non-core sections, routing their lines to "other" to avoid misclassification
                current_section = "other"
                continue
                
            if current_section in sections:
                sections[current_section].append(cleaned)
                
        return sections

    @staticmethod
    def _group_section_entries(lines: List[str]) -> List[str]:
        """Groups raw section lines into logical entries.
        
        PDFs often split bullet points and descriptions across multiple lines.
        This method merges them: a "header" line (containing a date range) becomes
        the start of an entry, and subsequent lines (bullets, descriptions) are
        joined under it.
        
        Args:
            lines (List[str]): Raw lines from a section.
            
        Returns:
            List[str]: Grouped entries, each as a single string.
        """
        if not lines:
            return []
            
        entries = []
        current_entry_lines = []
        
        for line in lines:
            cleaned = line.strip()
            
            # Skip standalone bullet characters
            if cleaned in ['•', '-', '*', '–']:
                continue
            
            # Strip leading bullet characters from lines
            stripped = re.sub(r'^[•\-*–]\s*', '', cleaned).strip()
            if not stripped:
                continue
            
            # Check if this line looks like a "header" (has a date range at the end)
            is_header = bool(DATE_RANGE_PATTERN.search(stripped))
            
            if is_header:
                # Save the previous entry if it exists
                if current_entry_lines:
                    entries.append(' | '.join(current_entry_lines))
                # Start new entry
                current_entry_lines = [stripped]
            else:
                # Append description to the current entry
                if current_entry_lines:
                    current_entry_lines.append(stripped)
                else:
                    # Orphan line before first header (e.g. CGPA lines in education)
                    current_entry_lines = [stripped]
                    
        # Don't forget the last entry
        if current_entry_lines:
            entries.append(' | '.join(current_entry_lines))
            
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
            
        # Fallback to the first non-empty line of the file if no header section lines matched
        lines = [line.strip() for line in text.split('\n') if line.strip()]
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
        # Remove any residual whitespace inside the matched emails
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
        """Checks if a text fragment is a section sub-heading rather than an actual skill.
        
        Args:
            text (str): The skill candidate string.
            
        Returns:
            bool: True if the text is a known section heading.
        """
        return text.lower().strip() in SKILL_SECTION_HEADINGS

    @classmethod
    def _strip_embedded_headings(cls, text: str) -> str:
        """Removes known section heading phrases embedded inside a line of text.
        
        Some PDF layouts (e.g. multi-column resumes) cause two adjacent section
        headings to be extracted onto a single line with no separator, e.g.
        "Languages Core Subjects". This strips any such known heading phrases
        out of the line (as whole-word matches) before the line is split into
        individual skill tokens, so the heading text never becomes a skill.
        
        Args:
            text (str): A raw line from the skills section.
            
        Returns:
            str: The line with embedded heading phrases removed.
        """
        cleaned = text
        for heading in _SORTED_HEADINGS:
            pattern = re.compile(rf'(?<!\w){re.escape(heading)}(?!\w)', re.IGNORECASE)
            cleaned = pattern.sub(' ', cleaned)
        return re.sub(r'\s+', ' ', cleaned).strip()

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
            
            # Strip any known heading phrases glued onto this line (e.g. from
            # multi-column PDF layouts merging two headings onto one line)
            skills_part = cls._strip_embedded_headings(skills_part)
                
            # Split by commas and semicolons
            for skill in re.split(r'[,;]', skills_part):
                skill_clean = skill.strip().rstrip('.').strip()
                # Filter: skip empty, too long, and section heading terms
                if skill_clean and len(skill_clean) < 30 and not cls._is_section_heading(skill_clean):
                    extracted_skills.append(skill_clean)
                    
        # 2. Scan the full text for common skills to ensure coverage (keeping matched case)
        common_keywords = [
            "python", "java", "c\\+\\+", "cpp", "c#", "go", "golang", "rust", "ruby", 
            "php", "javascript", "typescript", "html", "css", "sql", "nosql", "mongodb", 
            "postgresql", "mysql", "react", "angular", "vue", "node\\.js", "django", 
            "flask", "fastapi", "spring", "aws", "azure", "gcp", "docker", "kubernetes", 
            "git", "linux", "machine learning", "deep learning", "nlp", "tensorflow", 
            "pytorch", "pandas", "numpy", "scikit-learn", "mediapipe", "yolov8", "yolo",
            "llvm", "clang", "opencv", "express\\.js", "express"
        ]
        
        for kw in common_keywords:
            pattern = re.compile(rf'\b{kw}\b', re.IGNORECASE)
            for match in pattern.finditer(text):
                matched_text = match.group(0)
                # Avoid duplicates but maintain case of first occurrence
                if not any(s.lower() == matched_text.lower() for s in extracted_skills):
                    extracted_skills.append(matched_text)
                    
        return extracted_skills

    @classmethod
    def extract_experience(cls, sections: Dict[str, List[str]]) -> List[str]:
        """Extracts and groups experience entries.
        
        Args:
            sections (Dict[str, List[str]]): The parsed sections.
            
        Returns:
            List[str]: Grouped experience entries.
        """
        raw_lines = sections.get("experience", [])
        return cls._group_section_entries(raw_lines)

    @classmethod
    def extract_education(cls, sections: Dict[str, List[str]]) -> List[str]:
        """Extracts and groups education entries.
        
        Args:
            sections (Dict[str, List[str]]): The parsed sections.
            
        Returns:
            List[str]: Grouped education entries.
        """
        raw_lines = sections.get("education", [])
        return cls._group_section_entries(raw_lines)

    @classmethod
    def extract_projects(cls, sections: Dict[str, List[str]]) -> List[str]:
        """Extracts and groups project entries.
        
        Args:
            sections (Dict[str, List[str]]): The parsed sections.
            
        Returns:
            List[str]: Grouped project entries.
        """
        raw_lines = sections.get("projects", [])
        return cls._group_section_entries(raw_lines)
