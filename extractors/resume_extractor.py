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

class ResumeExtractor:
    """Extractor class for parsing candidate information from raw resume text."""

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
            "skills": []
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
            elif len(check_line) < 30 and check_line in [
                "projects", "certifications", "summary", "objective", 
                "interests", "languages", "publications", "awards"
            ]:
                # We skip non-core sections, routing their lines to "other" to avoid misclassification
                current_section = "other"
                continue
                
            if current_section in sections:
                sections[current_section].append(cleaned)
                
        return sections

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
        
        Args:
            text (str): Full text.
            
        Returns:
            List[str]: Found email addresses (includes duplicates if any).
        """
        return EMAIL_PATTERN.findall(text)

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
    def extract_skills(cls, text: str, sections: Dict[str, List[str]]) -> List[str]:
        """Extracts skills from the skills section and scans the full text for keywords.
        
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
                
            # Split by commas and semicolons
            for skill in re.split(r'[,;]', skills_part):
                skill_clean = skill.strip()
                if skill_clean and len(skill_clean) < 30:
                    extracted_skills.append(skill_clean)
                    
        # 2. Scan the full text for common skills to ensure coverage (keeping matched case)
        common_keywords = [
            "python", "java", "c\\+\\+", "cpp", "c#", "go", "golang", "rust", "ruby", 
            "php", "javascript", "typescript", "html", "css", "sql", "nosql", "mongodb", 
            "postgresql", "mysql", "react", "angular", "vue", "node\\.js", "django", 
            "flask", "fastapi", "spring", "aws", "azure", "gcp", "docker", "kubernetes", 
            "git", "linux", "machine learning", "deep learning", "nlp", "tensorflow", 
            "pytorch", "pandas", "numpy", "scikit-learn"
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
        """Extracts experience lines.
        
        Args:
            sections (Dict[str, List[str]]): The parsed sections.
            
        Returns:
            List[str]: Lines of text representing experience.
        """
        return sections.get("experience", [])

    @classmethod
    def extract_education(cls, sections: Dict[str, List[str]]) -> List[str]:
        """Extracts education lines.
        
        Args:
            sections (Dict[str, List[str]]): The parsed sections.
            
        Returns:
            List[str]: Lines of text representing education.
        """
        return sections.get("education", [])
