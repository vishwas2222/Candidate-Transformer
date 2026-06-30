"""
Schema validation for projected candidate output documents.

Operates on the *projected* (post field-selection/renaming) document, not the
original CanonicalCandidate, since that's what actually gets written to disk.
Never raises — any unexpected shape is reported as an ERROR/WARNING instead.
"""
import re
from typing import Any, Dict, Set

from config.config_loader import OutputConfig
from validation.validation_report import ValidationReport

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}$")
NON_DATE_TOKENS = {"present", "current", "now", ""}

KNOWN_CANDIDATE_FIELDS = {
    "full_name", "emails", "phones", "headline", "current_company", "title",
    "skills", "experience", "education", "projects",
}
LIST_FIELDS = {"emails", "phones", "skills", "experience", "education", "projects"}
LIST_OF_OBJECT_FIELDS = {
    "experience": {"required": {"title", "company"}, "optional": {
        "location", "start_date", "end_date", "description", "raw_text"}},
    "education": {"required": {"degree", "institution"}, "optional": {
        "specialization", "school", "cgpa", "percentage", "grade",
        "start_date", "end_date", "description", "raw_text"}},
    "projects": {"required": {"project_name"}, "optional": {
        "technology_stack", "description", "start_date", "end_date",
        "github", "demo", "raw_text"}},
}


class SchemaValidator:
    """Validates a projected candidate document against the output schema."""

    def validate(self, document: Dict[str, Any], config: OutputConfig) -> ValidationReport:
        """Validates a full output document ({"metadata":..., "candidate":...}).

        Args:
            document: The serialized output document.
            config: The resolved OutputConfig used to produce it (needed to
                know the field_mapping, so renamed fields are checked correctly).

        Returns:
            ValidationReport: Always returned, never raises.
        """
        report = ValidationReport()

        if not isinstance(document, dict):
            report.add("ERROR", "document", "Output document must be a JSON object.")
            return report

        candidate = document.get("candidate")
        if candidate is None:
            report.add("ERROR", "candidate", "Output document is missing the 'candidate' section.")
            return report
        if not isinstance(candidate, dict):
            report.add("ERROR", "candidate", "'candidate' section must be a JSON object.")
            return report

        reverse_mapping = {v: k for k, v in (config.field_mapping or {}).items()}

        def canonical_name(output_key: str) -> str:
            return reverse_mapping.get(output_key, output_key)

        def unwrap(value: Any):
            """Unwraps a possibly confidence/sources-wrapped value."""
            if isinstance(value, dict) and "value" in value and set(value.keys()) <= {"value", "confidence", "sources"}:
                return value["value"], value
            return value, None

        seen_canonical: Set[str] = set()
        for output_key, raw_value in candidate.items():
            canon = canonical_name(output_key)
            seen_canonical.add(canon)

            if canon not in KNOWN_CANDIDATE_FIELDS:
                report.add("WARNING", output_key, f"Unknown field '{output_key}' in output.")
                continue

            value, wrapper = unwrap(raw_value)

            if wrapper is not None:
                self._validate_wrapper(report, output_key, wrapper)

            if value is None:
                continue  # null policy — acceptable

            if canon in LIST_FIELDS and not isinstance(value, list):
                report.add("ERROR", output_key, f"Field '{output_key}' must be a list.")
                continue

            if canon == "emails":
                self._validate_emails(report, output_key, value)
            elif canon == "phones":
                self._check_duplicates(report, output_key, value, "phone")
            elif canon == "skills":
                self._check_duplicates(report, output_key, value, "skill")
            elif canon in LIST_OF_OBJECT_FIELDS:
                self._validate_object_list(report, output_key, canon, value, config)

        if "full_name" not in seen_canonical:
            report.add("INFO", "full_name", "Field 'full_name' was not included in this output profile.")

        return report

    # ------------------------------------------------------------------
    @staticmethod
    def _validate_wrapper(report: ValidationReport, field_name: str, wrapper: Dict[str, Any]) -> None:
        if "confidence" in wrapper:
            conf = wrapper["confidence"]
            if conf is not None and not (isinstance(conf, (int, float)) and 0 <= conf <= 1):
                report.add("ERROR", field_name, f"Confidence for '{field_name}' must be between 0 and 1, got {conf!r}.")
        if "sources" in wrapper:
            sources = wrapper["sources"]
            if sources is not None and not isinstance(sources, list):
                report.add("ERROR", field_name, f"'sources' for '{field_name}' must be a list.")

    @staticmethod
    def _validate_emails(report: ValidationReport, field_name: str, emails) -> None:
        seen = set()
        for email in emails:
            if not isinstance(email, str):
                report.add("ERROR", field_name, f"Email entries must be strings, got {email!r}.")
                continue
            if not EMAIL_RE.match(email):
                report.add("WARNING", field_name, f"'{email}' does not look like a valid email address.")
            key = email.lower()
            if key in seen:
                report.add("WARNING", field_name, f"Duplicate email '{email}' found.")
            seen.add(key)

    @staticmethod
    def _check_duplicates(report: ValidationReport, field_name: str, values, label: str) -> None:
        seen = set()
        for v in values:
            key = str(v).strip().lower()
            if key in seen:
                report.add("WARNING", field_name, f"Duplicate {label} '{v}' found.")
            seen.add(key)

    def _validate_object_list(self, report: ValidationReport, field_name: str, canon: str, items, config: OutputConfig) -> None:
        schema = LIST_OF_OBJECT_FIELDS[canon]
        allowed = schema["required"] | schema["optional"]
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                report.add("ERROR", field_name, f"Item {idx} in '{field_name}' must be an object.")
                continue
            for unknown_key in set(item.keys()) - allowed:
                report.add("WARNING", f"{field_name}[{idx}]", f"Unknown field '{unknown_key}' in '{field_name}' item.")
            for required_key in schema["required"]:
                if required_key in allowed and required_key not in item:
                    continue  # field wasn't selected for this profile — not an error
                if required_key in item and not item.get(required_key):
                    report.add("INFO", f"{field_name}[{idx}]", f"'{required_key}' is empty in '{field_name}' item.")
            for date_key in ("start_date", "end_date"):
                if date_key in item and isinstance(item[date_key], str):
                    self._validate_date(report, f"{field_name}[{idx}].{date_key}", item[date_key], config)
            if "description" in item and item["description"] is not None and not isinstance(item["description"], list):
                report.add("ERROR", f"{field_name}[{idx}]", f"'description' must be a list in '{field_name}' item.")

    @staticmethod
    def _validate_date(report: ValidationReport, field_name: str, value: str, config: OutputConfig) -> None:
        token = value.strip().lower()
        if token in NON_DATE_TOKENS:
            return
        if config.date_format == "ISO" and not ISO_DATE_RE.match(value.strip()):
            report.add("WARNING", field_name, f"Date '{value}' is not in ISO (YYYY-MM) format.")
