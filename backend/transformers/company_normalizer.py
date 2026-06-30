import re
from typing import Dict, Optional
from transformers.base_normalizer import BaseNormalizer

class CompanyNormalizer(BaseNormalizer):
    """Normalizer for company names, stripping legal suffixes and resolving abbreviations."""

    def __init__(self, company_map: Optional[Dict[str, str]] = None):
        """Initializes CompanyNormalizer with configurable abbreviation mappings.
        
        Args:
            company_map (Optional[Dict[str, str]]): Mapping of abbreviation keys to full company names.
        """
        if company_map is None:
            self.company_map = {
                "aws": "Amazon Web Services",
                "gcp": "Google Cloud Platform",
                "msft": "Microsoft"
            }
        else:
            self.company_map = {k.lower().strip(): v for k, v in company_map.items()}

    def normalize(self, value: str) -> str:
        """Normalizes company names by mapping abbreviations and stripping legal suffixes.
        
        Examples:
            - "Google LLC" -> "Google"
            - "Google Inc." -> "Google"
            - "AWS" -> "Amazon Web Services"
            
        Args:
            value (str): The raw company name.
            
        Returns:
            str: The normalized company name.
        """
        if not isinstance(value, str) or not value:
            return ""
            
        trimmed = value.strip()
        
        # 1. Resolve abbreviation mapping
        if trimmed.lower() in self.company_map:
            return self.company_map[trimmed.lower()]
            
        # 2. Strip legal suffixes (e.g. LLC, Inc., Ltd., Corporation)
        # Matches suffixes with or without leading commas/dots and trailing characters
        suffix_pattern = re.compile(
            r'\s*,\s*(?:llc|inc|co|corp|ltd|limited|corporation|incorporated)\b.*$|'
            r'\s+(?:llc|inc|co|corp|ltd|limited|corporation|incorporated)\b.*$',
            re.IGNORECASE
        )
        
        normalized = suffix_pattern.sub('', trimmed)
        
        # Clean up any trailing punctuation/whitespace left over
        return normalized.rstrip(',. ').strip()
