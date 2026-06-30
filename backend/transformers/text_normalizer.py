import re
from transformers.base_normalizer import BaseNormalizer

class TextNormalizer(BaseNormalizer):
    """Normalizer for general text, removing extra spaces and standardizing format."""

    def normalize(self, value: str) -> str:
        """Removes extra white space, standardizes capitalization if needed.
        
        Args:
            value (str): The raw text.
            
        Returns:
            str: Normalized text.
        """
        if not isinstance(value, str) or not value:
            return ""
            
        # Replace multiple spaces/tabs/newlines with a single space and strip
        return re.sub(r'\s+', ' ', value).strip()

    def normalize_name(self, value: str) -> str:
        """Specific capitalization normalization for candidate names (Title Case).
        
        Args:
            value (str): Raw name.
            
        Returns:
            str: Title case cleaned name.
        """
        cleaned = self.normalize(value)
        return cleaned.title()
