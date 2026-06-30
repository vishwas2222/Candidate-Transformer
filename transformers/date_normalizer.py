import re
from transformers.base_normalizer import BaseNormalizer

class DateNormalizer(BaseNormalizer):
    """Normalizer for date fields, standardizing standard/text dates to YYYY-MM format."""

    MONTHS_MAP = {
        "jan": "01", "january": "01",
        "feb": "02", "february": "02",
        "mar": "03", "march": "03",
        "apr": "04", "april": "04",
        "may": "05",
        "jun": "06", "june": "06",
        "jul": "07", "july": "07",
        "aug": "08", "august": "08",
        "sep": "09", "september": "09", "sept": "09",
        "oct": "10", "october": "10",
        "nov": "11", "november": "11",
        "dec": "12", "december": "12"
    }

    def normalize(self, value: str) -> str:
        """Converts raw date strings to YYYY-MM format.
        
        Examples:
            - "Jan 2024" -> "2024-01"
            - "01/2024" -> "2024-01"
            - "2024 January" -> "2024-01"
            - "2024" -> "2024-01"
            
        Args:
            value (str): The raw date string.
            
        Returns:
            str: The normalized YYYY-MM date string, or the trimmed original if unparseable.
        """
        if not isinstance(value, str) or not value:
            return ""
            
        cleaned = value.strip().lower()
        
        # Already YYYY-MM
        if re.match(r'^\d{4}-\d{2}$', cleaned):
            return cleaned
            
        # YYYY-M format -> format to YYYY-MM (e.g. 2024-1 -> 2024-01)
        match_yyyy_m = re.match(r'^(\d{4})-(\d{1})$', cleaned)
        if match_yyyy_m:
            return f"{match_yyyy_m.group(1)}-0{match_yyyy_m.group(2)}"
            
        # 1. MM/YYYY or M/YYYY (e.g. 01/2024, 1/2024)
        match_slash = re.match(r'^(\d{1,2})/(\d{4})$', cleaned)
        if match_slash:
            month = match_slash.group(1).zfill(2)
            year = match_slash.group(2)
            return f"{year}-{month}"
            
        # 2. Month Name + Year (e.g. Jan 2024, January 2024)
        match_month_year = re.match(r'^([a-zA-Z]+)\s+(\d{4})$', cleaned)
        if match_month_year:
            m_name = match_month_year.group(1)
            year = match_month_year.group(2)
            if m_name in self.MONTHS_MAP:
                return f"{year}-{self.MONTHS_MAP[m_name]}"
                
        # 3. Year + Month Name (e.g. 2024 January, 2024 Jan)
        match_year_month = re.match(r'^(\d{4})\s+([a-zA-Z]+)$', cleaned)
        if match_year_month:
            year = match_year_month.group(1)
            m_name = match_year_month.group(2)
            if m_name in self.MONTHS_MAP:
                return f"{year}-{self.MONTHS_MAP[m_name]}"
                
        # 4. Only 4-digit Year YYYY (e.g. 2024) -> default to YYYY-01
        match_year_only = re.match(r'^(\d{4})$', cleaned)
        if match_year_only:
            return f"{match_year_only.group(1)}-01"
            
        return value.strip()
