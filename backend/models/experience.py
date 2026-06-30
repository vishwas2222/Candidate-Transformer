from dataclasses import dataclass, field
import re
from typing import List, Optional

@dataclass
class Experience:
    """Dataclass representing structured professional experience.

    Fields
    ------
    raw_text    : Original joined text for traceability.
    title       : Job title.
    company     : Employer name.
    location    : Work location (city/country).
    start_date  : Start date string (e.g. "01/2026" or "2022").
    end_date    : End date string (e.g. "Present" or "2024").
    description : List of bullet-point strings describing responsibilities.
    """
    raw_text: str
    company: str = ""
    title: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    description: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, entry: dict) -> 'Experience':
        """Build an Experience from a structured dict produced by ResumeExtractor.

        The dict has keys: header, description, raw_lines.
        The header line is parsed to extract title, company, location, dates.

        Args:
            entry: Dict with keys 'header', 'description', 'raw_lines'.

        Returns:
            Experience: Fully populated Experience object.
        """
        header = entry.get("header", "")
        description = entry.get("description", [])
        raw_text = "\n".join(entry.get("raw_lines", [header]))

        title, company, location, start_date, end_date = cls._parse_header(header)

        return cls(
            raw_text=raw_text,
            title=title,
            company=company,
            location=location,
            start_date=start_date,
            end_date=end_date,
            description=description,
        )

    @classmethod
    def from_raw_text(cls, text: str) -> 'Experience':
        """Backward-compatible factory: parse from a raw text string.

        Accepts both plain strings and ' | '-separated grouped entries
        (legacy format from Part 2 initial implementation).

        Args:
            text: Raw experience text.

        Returns:
            Experience: Populated Experience object.
        """
        if not text:
            return cls("")

        if isinstance(text, dict):
            return cls.from_dict(text)

        # Legacy ' | ' grouped format
        parts = [p.strip() for p in text.split(' | ')]
        header = parts[0]
        description = parts[1:] if len(parts) > 1 else []
        title, company, location, start_date, end_date = cls._parse_header(header)

        return cls(
            raw_text=text,
            title=title,
            company=company,
            location=location,
            start_date=start_date,
            end_date=end_date,
            description=description,
        )

    @staticmethod
    def _parse_header(header: str):
        """Parse title, company, location, start_date, end_date from a header line.

        Supported formats:
        1. "Title, Company Location MM/YYYY – Present"  (inline date, comma-separated)
        2. "Title at Company (Dates)"
        3. "Title at Company Dates"  (no parens)
        4. "Title, Company (Dates)"
        5. "Title, Company"  (no dates)

        Returns:
            Tuple (title, company, location, start_date, end_date)
        """
        if not header:
            return "", "", "", "", ""

        title = ""
        company = ""
        location = ""
        start_date = ""
        end_date = ""

        # Pattern 1: Inline dates without parentheses, comma-separated
        # e.g. "PRISM Intern – Compiler Research, Samsung PRISM Program 01/2026 – Present"
        m = re.search(
            r'^(.*?),\s*(.*?)\s+(\d{1,2}/\d{4}|\d{4})\s*(?:[-–]|to)\s*(Present|Current|Now|\d{1,2}/\d{4}|\d{4})\s*$',
            header, re.IGNORECASE
        )
        if m:
            title = m.group(1).strip()
            company_loc = m.group(2).strip()
            start_date = m.group(3).strip()
            end_date = m.group(4).strip()
            # Separate location if last token looks like a city
            company, location = _split_company_location(company_loc)
            return title, company, location, start_date, end_date

        # Pattern 2: "Title at Company (Dates)"
        m = re.search(r'^(.*?)\s+at\s+([^(]+?)(?:\s*\((.+?)\))?\s*$', header)
        if m:
            title = m.group(1).strip()
            company_loc = m.group(2).strip()
            dates_str = m.group(3) or ""
            company, location = _split_company_location(company_loc)
            start_date, end_date = _parse_date_range(dates_str)
            return title, company, location, start_date, end_date

        # Pattern 3: "Title at Company StartDate – EndDate" (no parens)
        m = re.search(
            r'^(.*?)\s+at\s+(.*?)\s+(\d{1,2}/\d{4}|\d{4})\s*(?:[-–]|to)\s*(Present|Current|Now|\d{1,2}/\d{4}|\d{4})\s*$',
            header, re.IGNORECASE
        )
        if m:
            title = m.group(1).strip()
            company_loc = m.group(2).strip()
            start_date = m.group(3).strip()
            end_date = m.group(4).strip()
            company, location = _split_company_location(company_loc)
            return title, company, location, start_date, end_date

        # Pattern 4: "Title, Company (Dates)"
        m = re.search(r'^([^,]+),\s*([^(]+?)(?:\s*\((.+?)\))?\s*$', header)
        if m:
            title = m.group(1).strip()
            company_loc = m.group(2).strip()
            dates_str = m.group(3) or ""
            company, location = _split_company_location(company_loc)
            start_date, end_date = _parse_date_range(dates_str)
            return title, company, location, start_date, end_date

        # Fallback: entire header is the title
        title = header
        return title, company, location, start_date, end_date


def _split_company_location(company_loc: str):
    """Heuristic: split 'Company Name CityName' into (company, location).

    If the last token of the string is a short standalone word (likely a city),
    treat it as the location. Otherwise return (company_loc, "").
    """
    parts = company_loc.rsplit(None, 1)
    if len(parts) == 2:
        possible_loc = parts[1]
        # A single capitalized word that is not a common company suffix is likely a city
        company_suffixes = {"Inc", "Inc.", "Ltd", "Ltd.", "LLC", "Corp", "Program", "Research"}
        if possible_loc.istitle() and possible_loc not in company_suffixes and len(possible_loc) > 2:
            return parts[0].strip(), possible_loc
    return company_loc.strip(), ""


def _parse_date_range(dates_str: str):
    """Parse a date range string like '2022 - Present' into (start, end)."""
    if not dates_str:
        return "", ""
    parts = re.split(r'\s*(?:[-–]|to)\s*', dates_str, flags=re.IGNORECASE)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return parts[0].strip(), ""
