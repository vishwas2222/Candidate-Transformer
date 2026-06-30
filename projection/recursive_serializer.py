"""
Generic recursive serializer.

A single reusable function that turns *any* of the project's domain objects
(dataclasses, lists of dataclasses, Enums, CandidateField wrappers, plain
scalars) into plain JSON-serializable Python primitives (dict/list/str/
int/float/bool/None). New dataclasses added in the future do not require any
changes here — they're discovered via ``dataclasses.is_dataclass``.
"""
from dataclasses import is_dataclass, fields
from enum import Enum
from typing import Any


class RecursiveSerializer:
    """Stateless, generic serializer for nested domain objects."""

    @classmethod
    def serialize(cls, value: Any) -> Any:
        """Recursively converts a value into plain JSON-serializable primitives.

        Args:
            value: Any value — dataclass instance, list/tuple/set, dict, Enum,
                CandidateField, or plain scalar (str/int/float/bool/None).

        Returns:
            A structure made only of dict/list/str/int/float/bool/None.
        """
        # Local import to avoid a hard dependency / circular import — the
        # serializer must remain generic and not require models to exist.
        try:
            from models.candidate import CandidateField
        except ImportError:  # pragma: no cover - defensive, models always present
            CandidateField = None

        if value is None:
            return None

        if CandidateField is not None and isinstance(value, CandidateField):
            return {
                "value": cls.serialize(value.value),
                "confidence": value.confidence,
                "sources": list(value.sources),
                "normalized": value.normalized,
            }

        if isinstance(value, Enum):
            return value.value

        if is_dataclass(value) and not isinstance(value, type):
            return {f.name: cls.serialize(getattr(value, f.name)) for f in fields(value)}

        if isinstance(value, dict):
            return {str(k): cls.serialize(v) for k, v in value.items()}

        if isinstance(value, (list, tuple, set)):
            return [cls.serialize(item) for item in value]

        if isinstance(value, (str, int, float, bool)):
            return value

        # Fallback for any other object: best-effort string representation
        # rather than crashing the whole serialization pass.
        return str(value)
