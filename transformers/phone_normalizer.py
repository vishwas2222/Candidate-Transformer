import re
from transformers.base_normalizer import BaseNormalizer

class PhoneNormalizer(BaseNormalizer):
    """Normalizer for candidate phone numbers."""

    def normalize(self, value: str) -> str:
        """Standardizes phone numbers to a digits-only format, preserving country code '+' if present.
        
        Examples:
            - "9876543210" -> "9876543210"
            - "+91 9876543210" -> "+919876543210"
            - "(987)6543210" -> "9876543210"
            - "987-654-3210" -> "9876543210"
            
        Args:
            value (str): The raw phone number string.
            
        Returns:
            str: The normalized phone number string.
        """
        if not isinstance(value, str) or not value:
            return ""
            
        # Strip all whitespace, dashes, parentheses, and dots
        normalized = re.sub(r'[\s\-().]', '', value)
        return normalized
