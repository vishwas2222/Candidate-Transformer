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
        - "Degree, School (Start Date - End Date)"
        - "Degree at School (Start Date - End Date)"
        
        Args:
            text (str): The raw text line.
            
        Returns:
            Education: An Education object containing parsed fields.
        """
        if not text:
            return cls("")
            
        school = ""
        degree = ""
        start_date = ""
        end_date = ""
        
        # Pattern: "Degree - School (Dates)"
        match = re.search(r'(.*?)\s*-\s*([^(]+)(?:\s*\((.*?)\))?', text)
        if match:
            degree = match.group(1).strip()
            school = match.group(2).strip()
            dates = match.group(3) if match.group(3) else ""
            if dates:
                date_parts = re.split(r'\s*(?:-|–|to)\s*', dates, flags=re.IGNORECASE)
                if len(date_parts) == 2:
                    start_date = date_parts[0].strip()
                    end_date = date_parts[1].strip()
                else:
                    start_date = date_parts[0].strip()
        else:
            # Fallback Pattern: "Degree, School (Dates)" or "Degree at School (Dates)"
            match_alt = re.search(r'(.*?)\s+(?:at|,)\s+([^(,]+)(?:\s*\((.*?)\))?', text)
            if match_alt:
                degree = match_alt.group(1).strip()
                school = match_alt.group(2).strip()
                dates = match_alt.group(3) if match_alt.group(3) else ""
                if dates:
                    date_parts = re.split(r'\s*(?:-|–|to)\s*', dates, flags=re.IGNORECASE)
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
