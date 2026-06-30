from typing import List, Dict, Optional
from utils.logger import logger

class ConfidenceEngine:
    """Engine responsible for assigning and merging field confidence scores."""

    def __init__(self, source_confidences: Optional[Dict[str, float]] = None):
        """Initializes the ConfidenceEngine with source confidence scores.
        
        Args:
            source_confidences (Optional[Dict[str, float]]): Mapping of source patterns to floats.
        """
        if source_confidences is None:
            # Default confidence configuration
            self.source_confidences = {
                "recruiter.csv": 1.00,
                "sample_resume.pdf": 0.90
            }
        else:
            self.source_confidences = {k.lower(): v for k, v in source_confidences.items()}

    def get_confidence_for_source(self, source: str) -> float:
        """Calculates the confidence score of a value originating from a specific source.
        
        Args:
            source (str): Source filename.
            
        Returns:
            float: Confidence score.
        """
        if not source:
            return 0.0
        s_key = source.lower()
        for key, val in self.source_confidences.items():
            if key in s_key:
                return val
        return 0.5  # Default confidence for unknown sources

    def get_merged_confidence(self, sources: List[str]) -> float:
        """Calculates merged field confidence using 'highest confidence wins' rule.
        
        Args:
            sources (List[str]): List of contributing sources.
            
        Returns:
            float: Highest confidence score.
        """
        if not sources:
            return 0.0
            
        max_conf = max((self.get_confidence_for_source(src) for src in sources), default=0.0)
        return max_conf
