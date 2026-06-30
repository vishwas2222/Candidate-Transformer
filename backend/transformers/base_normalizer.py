from abc import ABC, abstractmethod
from typing import Any

class BaseNormalizer(ABC):
    """Abstract base class for all data normalizers."""

    @abstractmethod
    def normalize(self, value: Any) -> Any:
        """Normalizes the input value.
        
        Args:
            value (Any): The raw input value.
            
        Returns:
            Any: The normalized value.
        """
        pass
