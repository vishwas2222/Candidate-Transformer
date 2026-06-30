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
        - "Title – Research, Company MM/YYYY – Present" (inline dates without parens)
        - Grouped entries separated by ' | ' where the first segment is the header
        
        Args:
            text (str): The raw text line (or grouped entry).
            
        Returns:
            Experience: An Experience object containing parsed fields.
        """
        if not text:
            return cls("")
            
        # If this is a grouped entry (header | bullet1 | bullet2), use the header for parsing
        header = text.split(' | ')[0] if ' | ' in text else text
            
        title = ""
        company = ""
        start_date = ""
        end_date = ""
        
        # Pattern 1: Inline dates without parentheses
        # e.g. "PRISM Intern – Compiler Optimization Research, Samsung PRISM Program 01/2026 – Present"
        match_inline = re.search(
            r'^(.*?),\s*(.*?)\s+(\d{1,2}/\d{4}|\w+\s+\d{4}|\d{4})\s*(?:[-–]|to)\s*(Present|Current|Now|\d{1,2}/\d{4}|\w+\s+\d{4}|\d{4})\s*$',
            header, re.IGNORECASE
        )
        if match_inline:
            title = match_inline.group(1).strip()
            company = match_inline.group(2).strip()
            start_date = match_inline.group(3).strip()
            end_date = match_inline.group(4).strip()
        else:
            # Pattern 2: "Title at Company (Dates)"
            match_at = re.search(r'(.*?)\s+at\s+([^(,]+)(?:\s*\((.*?)\))?', header)
            if match_at:
                title = match_at.group(1).strip()
                company = match_at.group(2).strip()
                dates = match_at.group(3) if match_at.group(3) else ""
                if dates:
                    date_parts = re.split(r'\s*(?:[-–]|to)\s*', dates, flags=re.IGNORECASE)
                    if len(date_parts) == 2:
                        start_date = date_parts[0].strip()
                        end_date = date_parts[1].strip()
                    else:
                        start_date = date_parts[0].strip()
            else:
                # Pattern 3: "Title at Company Dates" (no parens, inline)
                match_at_inline = re.search(
                    r'^(.*?)\s+at\s+(.*?)\s+(\d{1,2}/\d{4}|\w+\s+\d{4}|\d{4})\s*(?:[-–]|to)\s*(Present|Current|Now|\d{1,2}/\d{4}|\w+\s+\d{4}|\d{4})\s*$',
                    header, re.IGNORECASE
                )
                if match_at_inline:
                    title = match_at_inline.group(1).strip()
                    company = match_at_inline.group(2).strip()
                    start_date = match_at_inline.group(3).strip()
                    end_date = match_at_inline.group(4).strip()
                else:
                    # Pattern 4: "Title, Company (Dates)" with parenthesized dates
                    match_comma = re.search(r'([^,]+),\s*([^(,]+)(?:\s*\((.*?)\))?', header)
                    if match_comma:
                        title = match_comma.group(1).strip()
                        company = match_comma.group(2).strip()
                        dates = match_comma.group(3) if match_comma.group(3) else ""
                        if dates:
                            date_parts = re.split(r'\s*(?:[-–]|to)\s*', dates, flags=re.IGNORECASE)
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
