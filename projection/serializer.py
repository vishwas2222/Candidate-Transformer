"""
High-level candidate serializer.

Ties the Projector (field selection/shaping) together with output metadata
to produce the final ``{"metadata": ..., "candidate": ...}`` structure that
gets handed to the OutputFormatter / FileExporter.
"""
import datetime
from typing import Any, Dict, Optional

from config.config_loader import OutputConfig
from projection.projector import Projector


class CandidateSerializer:
    """Builds the final output document for a candidate under a given config."""

    def __init__(self, projector: Optional[Projector] = None):
        self.projector = projector or Projector()

    def serialize(
        self,
        candidate: Any,
        config: OutputConfig,
        candidate_sources: Optional[int] = None,
        validation_summary: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Produces the full output document for a candidate.

        Args:
            candidate: The CanonicalCandidate to project (never modified).
            config: Resolved OutputConfig.
            candidate_sources: Number of source systems that contributed to
                this candidate (e.g. 2 for resume + CSV), for metadata.
            validation_summary: Optional dict summary of validation results,
                included in metadata when the config requests it (developer
                profile) or always under the "validation" metadata key.

        Returns:
            Dict[str, Any]: {"metadata": {...}, "candidate": {...}}
        """
        projected = self.projector.project(candidate, config)

        document: Dict[str, Any] = {}

        meta_cfg = config.metadata if isinstance(config.metadata, dict) else {}
        if meta_cfg.get("include", True):
            metadata: Dict[str, Any] = {
                "schema_version": meta_cfg.get("schema_version", "1.0"),
                "profile": config.profile,
                "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            }
            if candidate_sources is not None:
                metadata["candidate_sources"] = candidate_sources
            if meta_cfg.get("include_validation_summary") and validation_summary is not None:
                metadata["validation_summary"] = validation_summary
            document["metadata"] = metadata

        document["candidate"] = projected
        return document
