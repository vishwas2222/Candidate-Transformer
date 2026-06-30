import os
from typing import Any, Tuple, Dict, Optional
from utils.logger import logger

class ConflictResolver:
    """Handles resolution of scalar field value conflicts between different candidate sources."""

    def __init__(self, source_priorities: Optional[Dict[str, int]] = None):
        """Initializes the ConflictResolver with source priorities.
        
        A lower integer priority value represents higher priority.
        
        Args:
            source_priorities (Optional[Dict[str, int]]): Custom source priority mapping.
        """
        if source_priorities is None:
            # Default priority configuration: CSV takes precedence over PDF Resumes
            self.source_priorities = {
                "recruiter.csv": 1,
                "sample_resume.pdf": 2
            }
        else:
            self.source_priorities = {k.lower(): v for k, v in source_priorities.items()}
        
        # Records of every conflict encountered, available for merge-summary reporting
        self.conflicts: list = []

    def resolve(self, field_name: str, val1: Any, source1: str, val2: Any, source2: str) -> Tuple[Any, str]:
        """Resolves a conflict between two field values based on source priority rules.
        
        Args:
            field_name (str): Name of the field undergoing conflict resolution.
            val1 (Any): Value from source 1.
            source1 (str): Name of source 1.
            val2 (Any): Value from source 2.
            source2 (str): Name of source 2.
            
        Returns:
            Tuple[Any, str]: The winning value and the source it originated from.
        """
        # Clean inputs
        s1_key = os.path.basename(source1).lower() if source1 else ""
        s2_key = os.path.basename(source2).lower() if source2 else ""
        
        # If one value is empty/null, return the other without a conflict
        if not val1 and val2:
            return val2, source2
        if val1 and not val2:
            return val1, source1
        if not val1 and not val2:
            return "", ""

        # If values are identical, no conflict
        if val1 == val2:
            return val1, source1

        # Conflict detected! Log the event
        logger.info("Conflict detected")
        
        # Determine priority scores (default to 99 if unknown source)
        p1 = 99
        for key, p_val in self.source_priorities.items():
            if key in s1_key:
                p1 = p_val
                break
                
        p2 = 99
        for key, p_val in self.source_priorities.items():
            if key in s2_key:
                p2 = p_val
                break

        if p1 <= p2:
            winner_val, winner_src = val1, source1
            reason = f"{os.path.basename(source1) or 'Source 1'} has higher priority."
        else:
            winner_val, winner_src = val2, source2
            reason = f"{os.path.basename(source2) or 'Source 2'} has higher priority."

        self.conflicts.append({
            "field": field_name,
            "old_value": val1,
            "new_value": val2,
            "winner": winner_val,
            "reason": reason,
        })

        logger.info(
            f"Conflict | Field: {field_name} | Old Value: {val1} | "
            f"New Value: {val2} | Winner: {winner_val} | Reason: {reason}"
        )
        logger.info("Conflict resolved")
        return winner_val, winner_src
