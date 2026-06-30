from dataclasses import dataclass
import re

@dataclass
class Experience:
    """Dataclass representing structured professional experience."""
    raw_text: str
    company: str = ""
    title: str = ""
    start_date: str = ""
    end_date: str = ""

    @classmethod
    def from_raw_text(cls, text: str) -> 'Experience':
        """Heuristic to parse a raw text line into structured Experience fields.
        
        Supports patterns like:
        - "Title at Company (Start Date - End Date)"
        - "Title, Company (Start Date - End Date)"
        
        Args:
            text (str): The raw text line.
            
        Returns:
            Experience: An Experience object containing parsed fields.
        """
        if not text:
            return cls("")
            
        title = ""
        company = ""
        start_date = ""
        end_date = ""
        
        # Pattern: "Title at Company (Dates)"
        match = re.search(r'(.*?)\s+at\s+([^(,]+)(?:\s*\((.*?)\))?', text)
        if match:
            title = match.group(1).strip()
            company = match.group(2).strip()
            dates = match.group(3) if match.group(3) else ""
            if dates:
                date_parts = re.split(r'\s*(?:-|–|to)\s*', dates, flags=re.IGNORECASE)
                if len(date_parts) == 2:
                    start_date = date_parts[0].strip()
                    end_date = date_parts[1].strip()
                else:
                    start_date = date_parts[0].strip()
        else:
            # Fallback Pattern: "Title, Company (Dates)"
            match_comma = re.search(r'([^,]+),\s*([^(,]+)(?:\s*\((.*?)\))?', text)
            if match_comma:
                title = match_comma.group(1).strip()
                company = match_comma.group(2).strip()
                dates = match_comma.group(3) if match_comma.group(3) else ""
                if dates:
                    date_parts = re.split(r'\s*(?:-|–|to)\s*', dates, flags=re.IGNORECASE)
                    if len(date_parts) == 2:
                        start_date = date_parts[0].strip()
                        end_date = date_parts[1].strip()
                    else:
                        start_date = date_parts[0].strip()
                        
        return cls(
            raw_text=text,
            company=company,
            title=title,
            start_date=start_date,
            end_date=end_date
        )
