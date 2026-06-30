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

        # If percentage still empty, try to pull it from the raw header itself.
        # Handles: "10th Grade - St. Marys - 2019 - 89.4%"
        #          "Class X (CBSE) | 2019 | 85%"
        #          "High School Diploma, City School 2021, 88%"
        if not percentage and not cgpa:
            # Pipe-separated: look at pipe segments
            if '|' in header:
                for seg in header.split('|'):
                    pct_m = re.match(r'^\s*([\d.]+)\s*%\s*$', seg.strip())
                    if pct_m:
                        percentage = pct_m.group(1)
                        break
            # Trailing dash-% or comma-% pattern
            if not percentage:
                m = re.search(r'(?:,|-)\s*([\d.]+)\s*%\s*$', header)
                if m:
                    percentage = m.group(1)

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
        1. "B.E., Information Science & Engineering, 2023 \u2013 2027" (inline date, comma-sep)
        2. "Class XII, Sir mv pu college 2023"  (single year)
        3. "10th, school name 2021"
        4. "B.E. Information Science - School (Dates)"  (dash separated)
        5. "Class X (CBSE) | 2019 | 85%"  (pipe-separated with inline percentage)
        6. "High School Diploma, City School 2021, 88%"  (trailing inline percentage)

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

        # ── Pre-process: pipe-separated format ──────────────────────────────
        # e.g. "Class X (CBSE) | 2019 | 85%"  or  "Class XII | 2021 | 90.5%"
        if '|' in header:
            pipe_parts = [p.strip() for p in header.split('|')]
            # First part is degree/school label
            degree = pipe_parts[0].strip()
            # Remaining parts: extract year and percentage
            _year_found = ""
            for part in pipe_parts[1:]:
                year_m = re.match(r'^\s*(\d{4})\s*$', part)
                pct_m  = re.match(r'^\s*([\d.]+)\s*%\s*$', part)
                if year_m:
                    _year_found = year_m.group(1)
                elif pct_m:
                    # Return percentage as a special marker in institution to be
                    # picked up by from_dict. We encode it as a meta line instead.
                    pass  # handled below via inline_pct extraction
            if _year_found:
                start_date = _year_found
            # Strip any trailing percentage from degree string if accidentally included
            degree = re.sub(r'\s*[\d.]+\s*%\s*$', '', degree).strip()
            return degree, specialization, institution or school_line, start_date, end_date

        # ── Capture and strip an inline trailing percentage before other parsing
        # e.g. "High School Diploma, City School 2021, 88%"
        # We strip it so the remaining patterns work cleanly.
        _inline_pct = ""
        header_no_pct = header
        trailing_pct_m = re.search(r',?\s*([\d.]+)\s*%\s*$', header)
        if trailing_pct_m:
            _inline_pct = trailing_pct_m.group(1)
            header_no_pct = header[:trailing_pct_m.start()].strip()

        # ── Also capture inline trailing percentage in dash-separated score
        # e.g. "10th Grade - St. Marys School - 2019 - 89.4%"
        if not _inline_pct:
            dash_pct_m = re.search(r'-\s*([\d.]+)\s*%\s*$', header)
            if dash_pct_m:
                _inline_pct = dash_pct_m.group(1)
                header_no_pct = header[:dash_pct_m.start()].strip()

        # Work on cleaned header from here
        h = header_no_pct

        # Pattern 1: Comma-sep with inline date range
        # e.g. "B.E., Information Science & Engineering, 2023 \u2013 2027"
        m = re.search(
            r'^(.+?),\s*(.+?)\s+(\d{4})\s*(?:[-\u2013]|to)\s*(Present|Current|Now|\d{4})\s*$',
            h, re.IGNORECASE
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
                if school_line:
                    specialization = parts[1]
                    institution = school_line
                else:
                    specialization = ""
                    institution = parts[1]
            else:
                degree = parts[0] if parts else ""
                institution = school_line
            return degree, specialization, institution, start_date, end_date

        # Pattern 2: Single-year at end \u2014 "Class XII, college name 2023"
        m = re.search(r'^(.+?),\s*(.+?)\s+(\d{4})\s*$', h)
        if m:
            degree = m.group(1).strip()
            institution = m.group(2).strip() or school_line
            start_date = m.group(3).strip()
            return degree, specialization, institution, start_date, end_date

        # Pattern 3: "Degree - School (Dates)" or "Degree - School - Year - Score%"
        m = re.search(r'^(.*?)\s*-\s*([^(]+)(?:\s*\((.+?)\))?\s*$', h)
        if m:
            degree_part = m.group(1).strip()
            school_part = m.group(2).strip()
            dates_str   = m.group(3) or ""
            # degree_part may be "B.E., Information Science"
            deg_parts = [p.strip() for p in degree_part.split(',', 1)]
            degree = deg_parts[0]
            if len(deg_parts) > 1:
                specialization = deg_parts[1]
            # Strip trailing year from school_part if present (e.g. "2019" at end)
            school_clean = re.sub(r'\s*-?\s*(19|20)\d{2}\s*$', '', school_part).strip()
            # Extract year from school_part if dates_str is empty
            if not dates_str and not start_date:
                yr_m = re.search(r'\b(19|20)\d{2}\b', school_part)
                if yr_m:
                    start_date = yr_m.group(0)
            institution = school_clean or school_line
            if dates_str:
                start_date, end_date = _parse_edu_date_range(dates_str)
            return degree, specialization, institution, start_date, end_date

        # Fallback: treat whole header as degree, school_line as institution
        degree = h
        institution = school_line
        return degree, specialization, institution, start_date, end_date


    @staticmethod
    def _parse_meta(meta_lines: List[str]):
        """Extract cgpa, percentage, grade from metadata lines.

        Handles:
          - "CGPA: 7.04/10"       -> cgpa
          - "GPA: 3.8/4"          -> cgpa
          - "Score: 8.2/10"       -> cgpa (treated as GPA-style)
          - "Percentage: 96"      -> percentage
          - "Marks: 456/500"      -> percentage (computed as 456/500*100)
          - "Marks: 456/500 (91%)"-> percentage (extracts bracket value)
          - "88.5%"               -> percentage (standalone)
          - "Grade: A+"           -> grade

        Args:
            meta_lines: Lines recognised as grade/score metadata.

        Returns:
            Tuple (cgpa, percentage, grade)
        """
        cgpa       = ""
        percentage = ""
        grade      = ""

        for line in meta_lines:
            lower = line.lower()

            # ── CGPA / GPA ──────────────────────────────────────────────────
            if 'cgpa' in lower or 'gpa' in lower:
                # Handles: "CGPA: 7.04/10" and "CGPA 9.16/ 10 extra text"
                m = re.search(r'(?:cgpa|gpa)\s*[:]?\s*(\d+(?:\.\d+)?)', line, re.IGNORECASE)
                if m:
                    cgpa = m.group(1).strip()
                continue

            # ── Score: 8.2/10  ─ treat like CGPA ────────────────────────────
            if re.search(r'\bscore\s*:', line, re.IGNORECASE):
                m = re.search(r'(\d+(?:\.\d+)?)\s*(?:/\s*\d+(?:\.\d+)?)?', line)
                if m:
                    cgpa = m.group(1).strip()
                continue

            # ── Marks: 456/500 (91%) or Marks: 456/500 ──────────────────────
            if re.search(r'\bmarks\s*:', line, re.IGNORECASE):
                # Prefer bracketed percentage if present
                bracket = re.search(r'\(\s*([\d.]+)\s*%\s*\)', line)
                if bracket:
                    percentage = bracket.group(1).strip()
                else:
                    # Compute from numerator/denominator
                    frac = re.search(r'([\d.]+)\s*/\s*([\d.]+)', line)
                    if frac:
                        try:
                            pct = float(frac.group(1)) / float(frac.group(2)) * 100
                            percentage = f"{pct:.1f}"
                        except ZeroDivisionError:
                            pass
                    else:
                        m = re.search(r'([\d.]+)', line)
                        if m:
                            percentage = m.group(1).strip()
                continue

            # ── Percentage: 96 or standalone 88.5% or compound line ───────────
            if 'percentage' in lower or '%' in line:
                # Prefer explicit percentage number before/after '%'
                # e.g. "Percentage: 96%" or "State Board. Percentage: 93.8% City"
                pct_m = re.search(r'percentage\s*:\s*(\d+(?:\.\d+)?)\s*%?', line, re.IGNORECASE)
                if pct_m:
                    percentage = pct_m.group(1).strip()
                    continue
                # Standalone bare percentage line like "88.5%" or "96%"
                bare = re.match(r'^\s*(\d+(?:\.\d+)?)\s*%\s*$', line)
                if bare:
                    percentage = bare.group(1).strip()
                    continue
                # Any number followed immediately by % anywhere in the line
                m = re.search(r'(\d+(?:\.\d+)?)\s*%', line)
                if m:
                    percentage = m.group(1).strip()
                    continue
                # Last resort: first proper number after 'Percentage:'
                m = re.search(r'(\d+(?:\.\d+)?)', line)
                if m:
                    percentage = m.group(1).strip()
                continue

            # ── Grade: A+ ────────────────────────────────────────────────────
            if 'grade' in lower:
                m = re.search(r':\s*(.+)', line)
                if m:
                    grade = m.group(1).strip()
                continue

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
