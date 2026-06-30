from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
from .experience import Experience
from .education import Education
from .project import Project

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
    projects: List[str] = field(default_factory=list)
    source: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert the candidate object to the standard output dictionary format.
        
        Returns:
            Dict[str, Any]: The exact standard output dictionary representation.
        """
        return asdict(self)

@dataclass
class CandidateField:
    """Dataclass wrapping a field's value with confidence score and source provenance.
    
    Every field in the CanonicalCandidate stores its value, confidence,
    contributing sources, and normalization status internally using this class.
    """
    value: Any = None
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)
    normalized: bool = True

# Backward-compatible alias so existing imports still work
FieldMetadata = CandidateField

@dataclass
class CanonicalCandidate:
    """Dataclass representing the merged canonical candidate profile.
    
    Every field is a CandidateField containing the value, confidence, and sources.
    """
    full_name: CandidateField = field(default_factory=lambda: CandidateField("", 0.0))
    emails: CandidateField = field(default_factory=lambda: CandidateField([], 0.0))
    phones: CandidateField = field(default_factory=lambda: CandidateField([], 0.0))
    headline: CandidateField = field(default_factory=lambda: CandidateField("", 0.0))
    current_company: CandidateField = field(default_factory=lambda: CandidateField("", 0.0))
    title: CandidateField = field(default_factory=lambda: CandidateField("", 0.0))
    skills: CandidateField = field(default_factory=lambda: CandidateField([], 0.0))
    experience: CandidateField = field(default_factory=lambda: CandidateField([], 0.0))
    education: CandidateField = field(default_factory=lambda: CandidateField([], 0.0))
    projects: CandidateField = field(default_factory=lambda: CandidateField([], 0.0))
