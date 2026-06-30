from dataclasses import dataclass, field
import re
from typing import List, Optional

@dataclass
class Education:
    """Dataclass representing structured education details.

    Fields
    ------
    raw_text       : Original joined text for traceability.
    degree         : Degree or class name (e.g. "B.E.", "Class XII").
    specialization : Field of study (e.g. "Information Science & Engineering").
    institution    : School or college name.
    cgpa           : CGPA as a float string (e.g. "7.04").
    percentage     : Percentage as a float string (e.g. "96.2").
    grade          : Grade string if available.
    start_date     : Start year/date.
    end_date       : End year/date.
    description    : Any additional info lines not captured above.
    """
    raw_text: str
    school: str = ""            # alias kept for backward compatibility
    degree: str = ""
    specialization: str = ""
    institution: str = ""
    cgpa: str = ""
    percentage: str = ""
    grade: str = ""
    start_date: str = ""
    end_date: str = ""
    description: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, entry: dict) -> 'Education':
        """Build an Education from a structured dict produced by ResumeExtractor.

        The dict has keys: header, school_line, meta_lines, description, raw_lines.

        Args:
            entry: Dict with keys 'header', 'school_line', 'meta_lines',
                   'description', 'raw_lines'.

        Returns:
            Education: Fully populated Education object.
        """
        header = entry.get("header", "")
        school_line = entry.get("school_line") or ""
        meta_lines = entry.get("meta_lines", [])
        description = entry.get("description", [])
        raw_text = "\n".join(entry.get("raw_lines", [header]))

        degree, specialization, institution, start_date, end_date = cls._parse_header(
            header, school_line
        )
        cgpa, percentage, grade = cls._parse_meta(meta_lines)

        # school for backward compat
        school = institution or school_line

        return cls(
            raw_text=raw_text,
            school=school,
            degree=degree,
            specialization=specialization,
            institution=institution,
            cgpa=cgpa,
            percentage=percentage,
            grade=grade,
            start_date=start_date,
            end_date=end_date,
            description=description,
        )

    @classmethod
    def from_raw_text(cls, text: str) -> 'Education':
        """Backward-compatible factory: parse from a raw text string.

        Accepts both plain strings and ' | '-separated grouped entries.

        Args:
            text: Raw education text.

        Returns:
            Education: Populated Education object.
        """
        if not text:
            return cls("")

        if isinstance(text, dict):
            return cls.from_dict(text)

        # Legacy ' | ' grouped format
        parts = [p.strip() for p in text.split(' | ')]
        header = parts[0]
        extra_parts = parts[1:] if len(parts) > 1 else []

        meta_lines = []
        description = []
        for part in extra_parts:
            lower = part.lower()
            if any(kw in lower for kw in ['cgpa', 'gpa', 'percentage', '%', 'grade']):
                meta_lines.append(part)
            else:
                description.append(part)

        entry = {
            "header": header,
            "school_line": None,
            "meta_lines": meta_lines,
            "description": description,
            "raw_lines": [text],
        }
        return cls.from_dict(entry)

    @staticmethod
    def _parse_header(header: str, school_line: str = ""):
        """Parse degree, specialization, institution, dates from header line.

        Supported formats:
        1. "B.E., Information Science & Engineering, 2023 – 2027" (inline date, comma-sep)
        2. "Class XII, Sir mv pu college 2023"  (single year)
        3. "10th, school name 2021"
        4. "B.E. Information Science - School (Dates)"  (dash separated)

        Returns:
            Tuple (degree, specialization, institution, start_date, end_date)
        """
        degree = ""
        specialization = ""
        institution = ""
        start_date = ""
        end_date = ""

        if not header:
            return degree, specialization, institution, start_date, end_date

        # Pattern 1: Comma-sep with inline date range
        # e.g. "B.E., Information Science & Engineering, 2023 – 2027"
        m = re.search(
            r'^(.+?),\s*(.+?)\s+(\d{4})\s*(?:[-–]|to)\s*(Present|Current|Now|\d{4})\s*$',
            header, re.IGNORECASE
        )
        if m:
            pre_date = m.group(1).strip() + ', ' + m.group(2).strip()
            start_date = m.group(3).strip()
            end_date = m.group(4).strip()
            parts = [p.strip() for p in pre_date.split(',') if p.strip()]
            if len(parts) >= 3:
                degree = parts[0]
                specialization = parts[1]
                institution = ', '.join(parts[2:]) or school_line
            elif len(parts) == 2:
                degree = parts[0]
                # If school_line is provided separately, the second comma part is
                # the specialization/field, not the institution
                if school_line:
                    specialization = parts[1]
                    institution = school_line
                else:
                    # No school_line: second part is institution
                    specialization = ""
                    institution = parts[1]
            else:
                degree = parts[0] if parts else ""
                institution = school_line
            return degree, specialization, institution, start_date, end_date

        # Pattern 2: Single-year at end — "Class XII, college name 2023"
        m = re.search(r'^(.+?),\s*(.+?)\s+(\d{4})\s*$', header)
        if m:
            degree = m.group(1).strip()
            institution = m.group(2).strip() or school_line
            start_date = m.group(3).strip()
            return degree, specialization, institution, start_date, end_date

        # Pattern 3: "Degree - School (Dates)"
        m = re.search(r'^(.*?)\s*-\s*([^(]+)(?:\s*\((.+?)\))?\s*$', header)
        if m:
            degree_part = m.group(1).strip()
            school_part = m.group(2).strip()
            dates_str = m.group(3) or ""
            # degree_part may be "B.E., Information Science"
            deg_parts = [p.strip() for p in degree_part.split(',', 1)]
            degree = deg_parts[0]
            if len(deg_parts) > 1:
                specialization = deg_parts[1]
            institution = school_part or school_line
            start_date, end_date = _parse_edu_date_range(dates_str)
            return degree, specialization, institution, start_date, end_date

        # Fallback: treat whole header as degree, school_line as institution
        degree = header
        institution = school_line
        return degree, specialization, institution, start_date, end_date

    @staticmethod
    def _parse_meta(meta_lines: List[str]):
        """Extract cgpa, percentage, grade from metadata lines.

        Args:
            meta_lines: Lines like ["CGPA: 7.04/ 10", "Percentage:96"]

        Returns:
            Tuple (cgpa, percentage, grade)
        """
        cgpa = ""
        percentage = ""
        grade = ""

        for line in meta_lines:
            lower = line.lower()
            if 'cgpa' in lower or 'gpa' in lower:
                m = re.search(r'([\d.]+)\s*(?:/\s*[\d.]+)?', line)
                if m:
                    cgpa = m.group(1).strip()
            elif 'percentage' in lower or '%' in line:
                m = re.search(r'([\d.]+)\s*%?', line)
                if m:
                    percentage = m.group(1).strip()
            elif 'grade' in lower:
                m = re.search(r':\s*(.+)', line)
                if m:
                    grade = m.group(1).strip()

        return cgpa, percentage, grade


def _split_degree_parts(parts: List[str], school_line: str = ""):
    """Split comma-separated pre-date parts into degree, specialization, institution.

    Heuristic:
    - parts[0] = degree (e.g. "B.E.")
    - parts[1] = specialization (e.g. "Information Science & Engineering")
    - parts[2:] = institution parts (e.g. "B.M.S. College of Engineering, Bengaluru")
    """
    if not parts:
        return "", "", school_line
    if len(parts) == 1:
        return parts[0], "", school_line
    if len(parts) == 2:
        return parts[0], "", parts[1] or school_line
    # 3+ parts
    degree = parts[0]
    specialization = parts[1]
    institution = ', '.join(parts[2:]) or school_line
    return degree, specialization, institution


def _parse_edu_date_range(dates_str: str):
    """Parse 'start – end' into (start, end)."""
    if not dates_str:
        return "", ""
    parts = re.split(r'\s*(?:[-–]|to)\s*', dates_str, flags=re.IGNORECASE)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return parts[0].strip(), ""
