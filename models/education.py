from dataclasses import dataclass
import re

@dataclass
class Education:
    """Dataclass representing structured education details."""
    raw_text: str
    school: str = ""
    degree: str = ""
    start_date: str = ""
    end_date: str = ""

    @classmethod
    def from_raw_text(cls, text: str) -> 'Education':
        """Heuristic to parse a raw text line into structured Education fields.
        
        Supports patterns like:
        - "Degree - School (Start Date - End Date)"
        - "Degree, Field, School, Location YYYY – YYYY" (comma-separated, inline dates)
        - "Degree at School (Start Date - End Date)"
        - Grouped entries separated by ' | ' where the first segment is the header
        
        Args:
            text (str): The raw text line (or grouped entry).
            
        Returns:
            Education: An Education object containing parsed fields.
        """
        if not text:
            return cls("")
            
        # If this is a grouped entry (header | CGPA: 9.0), use the header for parsing
        header = text.split(' | ')[0] if ' | ' in text else text
            
        school = ""
        degree = ""
        start_date = ""
        end_date = ""
        
        # Pattern 1: Comma-separated with inline dates (no parentheses)
        # e.g. "B.E., Information Science, B.M.S. College of Engineering, Bengaluru 2023 – Present"
        # e.g. "Class XII, Vidyanikentan PU College, Gangavathi, Karnataka 2021 – 2023"
        match_inline = re.search(
            r'^(.+?),\s*(.+?)\s+(\d{4})\s*(?:[-–]|to)\s*(Present|Current|Now|\d{4})\s*$',
            header, re.IGNORECASE
        )
        if match_inline:
            # Split the pre-date portion by commas to identify degree vs school
            pre_date = match_inline.group(1).strip() + ', ' + match_inline.group(2).strip()
            start_date = match_inline.group(3).strip()
            end_date = match_inline.group(4).strip()
            
            parts = [p.strip() for p in pre_date.split(',') if p.strip()]
            
            if len(parts) >= 3:
                # First 1-2 parts are degree/field, rest is school/location
                # Heuristic: if first part looks like a degree abbreviation, take it as degree
                degree = ', '.join(parts[:2])  # e.g. "B.E., Information Science"
                school = ', '.join(parts[2:])  # e.g. "B.M.S. College of Engineering, Bengaluru"
            elif len(parts) == 2:
                degree = parts[0]
                school = parts[1]
            else:
                degree = parts[0] if parts else ""
                
        else:
            # Pattern 2: "Degree - School (Dates)"
            match_dash = re.search(r'(.*?)\s*-\s*([^(]+)(?:\s*\((.*?)\))?', header)
            if match_dash:
                degree = match_dash.group(1).strip()
                school = match_dash.group(2).strip()
                dates = match_dash.group(3) if match_dash.group(3) else ""
                if dates:
                    date_parts = re.split(r'\s*(?:[-–]|to)\s*', dates, flags=re.IGNORECASE)
                    if len(date_parts) == 2:
                        start_date = date_parts[0].strip()
                        end_date = date_parts[1].strip()
                    else:
                        start_date = date_parts[0].strip()
            else:
                # Pattern 3: "Degree at School (Dates)"
                match_at = re.search(r'(.*?)\s+at\s+([^(,]+)(?:\s*\((.*?)\))?', header)
                if match_at:
                    degree = match_at.group(1).strip()
                    school = match_at.group(2).strip()
                    dates = match_at.group(3) if match_at.group(3) else ""
                    if dates:
                        date_parts = re.split(r'\s*(?:[-–]|to)\s*', dates, flags=re.IGNORECASE)
                        if len(date_parts) == 2:
                            start_date = date_parts[0].strip()
                            end_date = date_parts[1].strip()
                        else:
                            start_date = date_parts[0].strip()
                        
        return cls(
            raw_text=text,
            school=school,
            degree=degree,
            start_date=start_date,
            end_date=end_date
        )
