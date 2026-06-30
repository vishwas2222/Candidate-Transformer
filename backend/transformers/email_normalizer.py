from transformers.base_normalizer import BaseNormalizer

class EmailNormalizer(BaseNormalizer):
    """Normalizer for candidate email addresses."""

    def normalize(self, value: str) -> str:
        """Standardizes email addresses to lowercase and trims surrounding whitespace.
        
        Examples:
            - "John@gmail.com" -> "john@gmail.com"
            - " JOHN@gmail.com  " -> "john@gmail.com"
            
        Args:
            value (str): The raw email address.
            
        Returns:
            str: The normalized email address.
        """
        if not isinstance(value, str) or not value:
            return ""
            
        return value.strip().lower()
