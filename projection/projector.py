"""
Projection engine.

The Projector NEVER touches the original CanonicalCandidate. It first runs the
candidate through the generic RecursiveSerializer (which produces brand new
plain dict/list structures with no references back to the original dataclass
instances), then applies field selection, renaming, sorting, date formatting,
and the empty-field policy on top of that copy.
"""
from dataclasses import fields as dataclass_fields
from typing import Any, Dict, List

from projection.field_selector import FieldSelector, LIST_OF_OBJECT_FIELDS
from projection.recursive_serializer import RecursiveSerializer
from config.config_loader import OutputConfig
from transformers.date_normalizer import DateNormalizer

_DATE_FIELDS = {"start_date", "end_date"}


class Projector:
    """Projects a CanonicalCandidate into a new, config-shaped output dict."""

    def __init__(self):
        self._date_normalizer = DateNormalizer()

    def project(self, candidate: Any, config: OutputConfig) -> Dict[str, Any]:
        """Builds a new projected dict from the canonical candidate.

        Args:
            candidate: The CanonicalCandidate (or any object whose top-level
                attributes are CandidateField-like wrappers / plain values).
            config: Resolved OutputConfig describing what to include and how.

        Returns:
            Dict[str, Any]: A brand-new dict — the original candidate object
            is never read into mutably, nor modified in any way.
        """
        serialized = self._serialize_top_level(candidate)
        plan = FieldSelector(config.include_fields, config.exclude_fields).resolve()

        result: Dict[str, Any] = {}
        for name in self._ordered(plan.top_level, serialized):
            if name not in serialized:
                continue  # unknown/unrecognized field — surfaced by the validator instead

            meta = serialized[name]
            value = meta["value"] if isinstance(meta, dict) and "value" in meta else meta

            value = self._filter_nested(name, value, plan, config)
            value = self._sort(name, value, config)
            value = self._format_dates(name, value, config)

            if config.include_confidence or config.include_sources:
                wrapped: Dict[str, Any] = {"value": value}
                if config.include_confidence:
                    wrapped["confidence"] = meta.get("confidence") if isinstance(meta, dict) else None
                if config.include_sources:
                    wrapped["sources"] = meta.get("sources") if isinstance(meta, dict) else []
                emptiness_probe = value
                output_value: Any = wrapped
            else:
                emptiness_probe = value
                output_value = value

            if self._is_empty(emptiness_probe):
                if config.empty_field_policy == "remove":
                    continue
                if config.empty_field_policy == "null":
                    if isinstance(output_value, dict) and "value" in output_value:
                        output_value["value"] = None
                    else:
                        output_value = None

            output_key = config.field_mapping.get(name, name)
            result[output_key] = output_value

        return result

    # ------------------------------------------------------------------
    @staticmethod
    def _ordered(names, serialized) -> List[str]:
        """Keeps a stable, predictable field order (declared candidate order)."""
        ordered = [n for n in serialized.keys() if n in names]
        # include any selected names that weren't part of serialized (unknown) at the end
        ordered += [n for n in names if n not in serialized]
        return ordered

    @staticmethod
    def _serialize_top_level(candidate: Any) -> Dict[str, Any]:
        """Serializes each top-level attribute of the candidate independently.

        Returns a dict of {field_name: {"value":.., "confidence":.., "sources":..}}
        (or {field_name: <plain serialized value>} if the attribute isn't a
        CandidateField wrapper), entirely decoupled from the original object.
        """
        result = {}
        if hasattr(candidate, "__dataclass_fields__"):
            names = [f.name for f in dataclass_fields(candidate)]
        else:
            names = list(getattr(candidate, "__dict__", {}).keys())
        for name in names:
            result[name] = RecursiveSerializer.serialize(getattr(candidate, name))
        return result

    @staticmethod
    def _filter_nested(name: str, value: Any, plan, config: OutputConfig) -> Any:
        if name not in LIST_OF_OBJECT_FIELDS or not isinstance(value, list):
            return value
        filtered = []
        for item in value:
            if not isinstance(item, dict):
                filtered.append(item)
                continue
            keep_attrs = plan.attrs_for(name, set(item.keys()))
            new_item = {k: v for k, v in item.items() if k in keep_attrs}
            if not config.include_raw_text:
                new_item.pop("raw_text", None)
            filtered.append(new_item)
        return filtered

    @staticmethod
    def _sort(name: str, value: Any, config: OutputConfig) -> Any:
        if name == "skills" and config.sort_skills and isinstance(value, list):
            return sorted(value, key=lambda s: str(s).lower())
        if name == "projects" and config.sort_projects and isinstance(value, list):
            return sorted(
                value,
                key=lambda p: str(p.get("project_name", "")).lower() if isinstance(p, dict) else str(p).lower()
            )
        return value

    def _format_dates(self, name: str, value: Any, config: OutputConfig) -> Any:
        if config.date_format != "ISO" or name not in LIST_OF_OBJECT_FIELDS or not isinstance(value, list):
            return value
        formatted = []
        for item in value:
            if not isinstance(item, dict):
                formatted.append(item)
                continue
            new_item = dict(item)
            for date_key in _DATE_FIELDS:
                if date_key in new_item and isinstance(new_item[date_key], str):
                    raw = new_item[date_key]
                    if raw.strip().lower() in ("present", "current", "now", ""):
                        continue
                    new_item[date_key] = self._date_normalizer.normalize(raw)
            formatted.append(new_item)
        return formatted

    @staticmethod
    def _is_empty(value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, (str, list, dict, tuple, set)) and len(value) == 0:
            return True
        return False
