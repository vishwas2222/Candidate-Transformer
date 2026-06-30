from typing import List

class ProvenanceTracker:
    """Tracks source file provenance for merged candidate fields."""

    @staticmethod
    def get_provenance(source: str) -> List[str]:
        """Helper to convert a single source string into a list format.
        
        Args:
            source (str): Original source file path or name.
            
        Returns:
            List[str]: Provenance tracking list.
        """
        return [source] if source else []

    @staticmethod
    def merge_provenance(sources1: List[str], sources2: List[str]) -> List[str]:
        """Merges two lists of sources, keeping unique sources and preserving order.
        
        Args:
            sources1 (List[str]): Source list from profile 1.
            sources2 (List[str]): Source list from profile 2.
            
        Returns:
            List[str]: The combined source list.
        """
        merged = []
        for src in sources1 + sources2:
            if src and src not in merged:
                merged.append(src)
        return merged
