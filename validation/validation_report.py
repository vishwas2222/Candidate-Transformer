"""
Validation report model.

A simple, serializable container for the results of schema validation:
errors, warnings, and informational notes, each tagged with severity.
"""
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


@dataclass
class ValidationIssue:
    """A single validation finding."""
    type: str  # "ERROR" | "WARNING" | "INFO"
    field: str
    message: str


@dataclass
class ValidationReport:
    """Aggregated result of validating a projected candidate document."""
    is_valid: bool = True
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)

    def add(self, severity: str, field_name: str, message: str) -> None:
        """Records a finding and updates `is_valid` if it's an error."""
        issue = ValidationIssue(type=severity, field=field_name, message=message)
        if severity == "ERROR":
            self.errors.append(issue)
            self.is_valid = False
        elif severity == "WARNING":
            self.warnings.append(issue)
        else:
            self.info.append(issue)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": [asdict(i) for i in self.errors],
            "warnings": [asdict(i) for i in self.warnings],
            "info": [asdict(i) for i in self.info],
        }

    def summary(self) -> Dict[str, Any]:
        """Compact summary suitable for embedding in output metadata."""
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "info_count": len(self.info),
        }
