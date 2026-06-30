"""
Field selection logic used by the Projector.

Supports plain top-level field names ("full_name") and dotted nested paths
referring to a single attribute within each item of a list-of-objects field
("experience.title", "projects.project_name", "education.institution").
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set

LIST_OF_OBJECT_FIELDS = {"experience", "education", "projects"}


@dataclass
class FieldPlan:
    """Resolved field-selection plan."""
    top_level: Set[str] = field(default_factory=set)
    # top-level field -> attrs explicitly requested via "field.attr" includes.
    # Empty/missing means "no narrowing requested" (keep all attrs, minus excludes).
    nested_include: Dict[str, Set[str]] = field(default_factory=dict)
    # top-level field -> attrs to drop via "field.attr" excludes.
    nested_exclude: Dict[str, Set[str]] = field(default_factory=dict)

    def attrs_for(self, top: str, all_attrs: Set[str]) -> Set[str]:
        """Resolves the final attribute set to keep for a nested object field."""
        included = self.nested_include.get(top)
        base = set(included) if included else set(all_attrs)
        excluded = self.nested_exclude.get(top, set())
        return base - excluded


class FieldSelector:
    """Resolves which top-level (and nested) fields should appear in output."""

    def __init__(self, include_fields: List[str], exclude_fields: List[str]):
        self.include_fields = include_fields or []
        self.exclude_fields = exclude_fields or []

    def resolve(self) -> FieldPlan:
        """Resolves the configured include/exclude lists into a FieldPlan."""
        plan = FieldPlan()
        whole_field_included: Set[str] = set()

        for item in self.include_fields:
            if "." in item:
                top, _, attr = item.partition(".")
                plan.top_level.add(top)
                plan.nested_include.setdefault(top, set()).add(attr)
            else:
                plan.top_level.add(item)
                whole_field_included.add(item)

        # A bare "experience" include means "everything", overriding any
        # narrower "experience.title" includes that also appeared.
        for top in whole_field_included:
            plan.nested_include.pop(top, None)

        excluded_top: Set[str] = set()
        for item in self.exclude_fields:
            if "." in item:
                top, _, attr = item.partition(".")
                plan.nested_exclude.setdefault(top, set()).add(attr)
            else:
                excluded_top.add(item)

        plan.top_level -= excluded_top
        return plan
