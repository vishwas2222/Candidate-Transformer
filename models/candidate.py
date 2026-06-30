from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
from .experience import Experience
from .education import Education

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

@dataclass
class FieldMetadata:
    """Class containing value and metadata (confidence, sources) for a profile field."""
    value: Any = None
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)

@dataclass
class CanonicalCandidate:
    """Dataclass representing the merged canonical candidate profile."""
    full_name: FieldMetadata = field(default_factory=lambda: FieldMetadata("", 0.0))
    emails: FieldMetadata = field(default_factory=lambda: FieldMetadata([], 0.0))
    phones: FieldMetadata = field(default_factory=lambda: FieldMetadata([], 0.0))
    headline: FieldMetadata = field(default_factory=lambda: FieldMetadata("", 0.0))
    current_company: FieldMetadata = field(default_factory=lambda: FieldMetadata("", 0.0))
    title: FieldMetadata = field(default_factory=lambda: FieldMetadata("", 0.0))
    skills: FieldMetadata = field(default_factory=lambda: FieldMetadata([], 0.0))
    experience: FieldMetadata = field(default_factory=lambda: FieldMetadata([], 0.0))
    education: FieldMetadata = field(default_factory=lambda: FieldMetadata([], 0.0))

