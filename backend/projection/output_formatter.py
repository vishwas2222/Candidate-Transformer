"""
Output formatting.

Turns the in-memory output document (plain dict from CandidateSerializer)
into a JSON string, honoring pretty/compact printing and stable key ordering.
"""
import json
from typing import Any, Dict

from config.config_loader import OutputConfig


class OutputFormatter:
    """Formats a candidate output document as a JSON string."""

    @staticmethod
    def format(document: Dict[str, Any], config: OutputConfig) -> str:
        """Serializes the document to a JSON string per the config.

        Args:
            document: The output document (e.g. {"metadata": ..., "candidate": ...}).
            config: Resolved OutputConfig (controls pretty_print).

        Returns:
            str: UTF-8 safe JSON text.
        """
        if config.pretty_print:
            return json.dumps(
                document, indent=2, sort_keys=True, ensure_ascii=False, default=str
            ) + "\n"
        return json.dumps(
            document, separators=(",", ":"), sort_keys=True, ensure_ascii=False, default=str
        )
