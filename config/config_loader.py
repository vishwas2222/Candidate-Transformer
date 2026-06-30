"""
Runtime configuration loader for Part 3 (Output Layer).

Loads JSON output-profile configs (default/minimal/recruiter/analytics/developer
or any custom profile) and validates them *before* anything downstream consumes
them. Never raises on a malformed/missing config — callers always get an
``OutputConfig`` (falling back to safe defaults) plus a list of ``ConfigIssue``
objects describing anything that was wrong, so the pipeline can surface a
validation report instead of crashing.
"""
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

# All keys recognized in a config file. Anything else is reported as "unknown".
KNOWN_CONFIG_KEYS = {
    "profile", "include_fields", "exclude_fields", "include_confidence",
    "include_sources", "include_raw_text", "pretty_print", "sort_skills",
    "sort_projects", "date_format", "output_directory", "output_filename",
    "empty_field_policy", "field_mapping", "metadata", "validation",
}

# Top-level Candidate fields that include_fields/exclude_fields/field_mapping
# are allowed to reference (including dotted nested paths like "experience.title").
KNOWN_TOP_LEVEL_FIELDS = {
    "full_name", "emails", "phones", "headline", "current_company", "title",
    "skills", "experience", "education", "projects",
}
KNOWN_NESTED_SUFFIXES = {
    "experience": {"title", "company", "location", "start_date", "end_date", "description", "raw_text"},
    "education": {"degree", "specialization", "institution", "school", "cgpa",
                  "percentage", "grade", "start_date", "end_date", "description", "raw_text"},
    "projects": {"project_name", "technology_stack", "description", "start_date",
                 "end_date", "github", "demo", "raw_text"},
}

VALID_EMPTY_FIELD_POLICIES = {"keep", "remove", "null"}
VALID_DATE_FORMATS = {"ISO", "RAW"}


@dataclass
class ConfigIssue:
    """A single problem (or note) found while loading/validating a config."""
    severity: str  # "ERROR" | "WARNING" | "INFO"
    message: str
    key: Optional[str] = None


@dataclass
class OutputConfig:
    """Fully-resolved, defaulted runtime configuration for the output layer."""
    profile: str = "default"
    include_fields: List[str] = field(default_factory=lambda: list(KNOWN_TOP_LEVEL_FIELDS))
    exclude_fields: List[str] = field(default_factory=list)
    include_confidence: bool = False
    include_sources: bool = False
    include_raw_text: bool = False
    pretty_print: bool = True
    sort_skills: bool = False
    sort_projects: bool = False
    date_format: str = "ISO"
    output_directory: str = "output"
    output_filename: str = "candidate.json"
    empty_field_policy: str = "keep"
    field_mapping: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=lambda: {"include": True, "schema_version": "1.0"})
    validation: Dict[str, Any] = field(default_factory=lambda: {"enabled": True, "strict": False})

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConfigLoader:
    """Loads and validates output-profile JSON configs.

    Usage:
        loader = ConfigLoader()
        config, issues = loader.load("recruiter")
    """

    def __init__(self, config_dir: str = CONFIG_DIR):
        self.config_dir = config_dir

    def _resolve_path(self, profile: str) -> str:
        # Accept both "recruiter" and "recruiter.json" / a full path.
        if os.path.isfile(profile):
            return profile
        filename = profile if profile.endswith(".json") else f"{profile}.json"
        return os.path.join(self.config_dir, filename)

    def load(self, profile: Optional[str] = None) -> "tuple[OutputConfig, List[ConfigIssue]]":
        """Loads a config profile by name, validating it along the way.

        Args:
            profile: Profile name (e.g. "recruiter"), filename, or full path.
                Defaults to "default" if omitted.

        Returns:
            Tuple of (OutputConfig, list of ConfigIssue). Always returns a usable
            OutputConfig, even if the file is missing or malformed — in that case
            issues will contain ERROR entries and a safe default config is used.
        """
        profile = profile or "default"
        issues: List[ConfigIssue] = []
        path = self._resolve_path(profile)

        raw: Dict[str, Any] = {}
        if not os.path.isfile(path):
            issues.append(ConfigIssue(
                "ERROR", f"Config file not found for profile '{profile}' (looked at {path}); "
                         f"falling back to built-in defaults."
            ))
            return OutputConfig(profile=profile), issues

        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError as e:
            issues.append(ConfigIssue(
                "ERROR", f"Malformed JSON in config '{path}': {e}. Falling back to built-in defaults."
            ))
            return OutputConfig(profile=profile), issues
        except OSError as e:
            issues.append(ConfigIssue(
                "ERROR", f"Could not read config '{path}': {e}. Falling back to built-in defaults."
            ))
            return OutputConfig(profile=profile), issues

        if not isinstance(raw, dict):
            issues.append(ConfigIssue("ERROR", f"Config '{path}' must contain a JSON object."))
            return OutputConfig(profile=profile), issues

        issues.extend(self._validate(raw))

        config = self._build_config(raw, profile)
        return config, issues

    # ------------------------------------------------------------------
    def _validate(self, raw: Dict[str, Any]) -> List[ConfigIssue]:
        issues: List[ConfigIssue] = []

        # Unknown top-level keys
        for key in raw.keys():
            if key not in KNOWN_CONFIG_KEYS:
                issues.append(ConfigIssue("WARNING", f"Unknown configuration key '{key}' (ignored).", key))

        # include/exclude field validation
        for list_key in ("include_fields", "exclude_fields"):
            values = raw.get(list_key)
            if values is None:
                continue
            if not isinstance(values, list):
                issues.append(ConfigIssue("ERROR", f"'{list_key}' must be a list of field names.", list_key))
                continue
            seen = set()
            for item in values:
                if not isinstance(item, str):
                    issues.append(ConfigIssue("ERROR", f"'{list_key}' entries must be strings, got {item!r}.", list_key))
                    continue
                if item in seen:
                    issues.append(ConfigIssue("WARNING", f"Duplicate entry '{item}' in '{list_key}'.", list_key))
                seen.add(item)
                if not self._is_known_field(item):
                    issues.append(ConfigIssue("WARNING", f"Unknown field name '{item}' in '{list_key}'.", list_key))

        # field_mapping validation
        mapping = raw.get("field_mapping")
        if mapping is not None:
            if not isinstance(mapping, dict):
                issues.append(ConfigIssue("ERROR", "'field_mapping' must be an object.", "field_mapping"))
            else:
                seen_targets: Dict[str, str] = {}
                for src, dst in mapping.items():
                    if not self._is_known_field(src):
                        issues.append(ConfigIssue("WARNING", f"Unknown source field '{src}' in 'field_mapping'.", "field_mapping"))
                    if not isinstance(dst, str) or not dst:
                        issues.append(ConfigIssue("ERROR", f"'field_mapping' target for '{src}' must be a non-empty string.", "field_mapping"))
                        continue
                    if dst in seen_targets:
                        issues.append(ConfigIssue(
                            "ERROR",
                            f"'field_mapping' targets must be unique: '{src}' and '{seen_targets[dst]}' both map to '{dst}'.",
                            "field_mapping"
                        ))
                    seen_targets[dst] = src

        # empty_field_policy
        policy = raw.get("empty_field_policy")
        if policy is not None and policy not in VALID_EMPTY_FIELD_POLICIES:
            issues.append(ConfigIssue(
                "ERROR",
                f"Invalid 'empty_field_policy' value '{policy}'. Must be one of {sorted(VALID_EMPTY_FIELD_POLICIES)}.",
                "empty_field_policy"
            ))

        # date_format
        date_format = raw.get("date_format")
        if date_format is not None and date_format not in VALID_DATE_FORMATS:
            issues.append(ConfigIssue(
                "WARNING",
                f"Unrecognized 'date_format' value '{date_format}'. Expected one of {sorted(VALID_DATE_FORMATS)}; "
                f"dates will be passed through unmodified.",
                "date_format"
            ))

        # boolean fields
        for bool_key in ("include_confidence", "include_sources", "include_raw_text",
                          "pretty_print", "sort_skills", "sort_projects"):
            val = raw.get(bool_key)
            if val is not None and not isinstance(val, bool):
                issues.append(ConfigIssue("ERROR", f"'{bool_key}' must be a boolean.", bool_key))

        # output_directory / output_filename
        for str_key in ("output_directory", "output_filename", "profile"):
            val = raw.get(str_key)
            if val is not None and not isinstance(val, str):
                issues.append(ConfigIssue("ERROR", f"'{str_key}' must be a string.", str_key))

        # metadata / validation must be objects if present
        for obj_key in ("metadata", "validation"):
            val = raw.get(obj_key)
            if val is not None and not isinstance(val, dict):
                issues.append(ConfigIssue("ERROR", f"'{obj_key}' must be an object.", obj_key))

        return issues

    @staticmethod
    def _is_known_field(item: str) -> bool:
        """Checks whether a (possibly dotted) field reference is recognized."""
        if "." in item:
            top, _, rest = item.partition(".")
            if top not in KNOWN_NESTED_SUFFIXES:
                return False
            return rest in KNOWN_NESTED_SUFFIXES[top]
        return item in KNOWN_TOP_LEVEL_FIELDS

    @staticmethod
    def _build_config(raw: Dict[str, Any], profile: str) -> OutputConfig:
        """Builds an OutputConfig from raw JSON, defaulting/repairing bad values."""
        defaults = OutputConfig(profile=raw.get("profile", profile) if isinstance(raw.get("profile", profile), str) else profile)

        def _get(key, default, expected_type=None):
            val = raw.get(key, default)
            if expected_type is not None and not isinstance(val, expected_type):
                return default
            return val

        include_fields = _get("include_fields", defaults.include_fields, list)
        exclude_fields = _get("exclude_fields", defaults.exclude_fields, list)
        include_fields = [f for f in include_fields if isinstance(f, str)]
        exclude_fields = [f for f in exclude_fields if isinstance(f, str)]

        field_mapping = _get("field_mapping", {}, dict)
        field_mapping = {k: v for k, v in field_mapping.items() if isinstance(k, str) and isinstance(v, str) and v}

        empty_policy = raw.get("empty_field_policy", defaults.empty_field_policy)
        if empty_policy not in VALID_EMPTY_FIELD_POLICIES:
            empty_policy = defaults.empty_field_policy

        date_format = raw.get("date_format", defaults.date_format)
        if date_format not in VALID_DATE_FORMATS:
            date_format = "RAW"

        metadata = _get("metadata", defaults.metadata, dict)
        validation = _get("validation", defaults.validation, dict)

        return OutputConfig(
            profile=defaults.profile,
            include_fields=include_fields or list(KNOWN_TOP_LEVEL_FIELDS),
            exclude_fields=exclude_fields,
            include_confidence=bool(_get("include_confidence", False, bool)),
            include_sources=bool(_get("include_sources", False, bool)),
            include_raw_text=bool(_get("include_raw_text", False, bool)),
            pretty_print=bool(_get("pretty_print", True, bool)),
            sort_skills=bool(_get("sort_skills", False, bool)),
            sort_projects=bool(_get("sort_projects", False, bool)),
            date_format=date_format,
            output_directory=_get("output_directory", defaults.output_directory, str),
            output_filename=_get("output_filename", defaults.output_filename, str),
            empty_field_policy=empty_policy,
            field_mapping=field_mapping,
            metadata=metadata,
            validation=validation,
        )
