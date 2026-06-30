from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any

@dataclass
class Candidate:
    """Dataclass representing the unified candidate model schema."""
    full_name: str = ""
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    headline: str = ""
    current_company: str = ""
    title: str = ""
    skills: List[str] = field(default_factory=list)
    experience: List[str] = field(default_factory=list)
    education: List[str] = field(default_factory=list)
    source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert the candidate object to the standard output dictionary format.
        
        Returns:
            Dict[str, Any]: The exact standard output dictionary representation.
        """
        return asdict(self)
