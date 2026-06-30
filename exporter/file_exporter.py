"""
Output export layer.

Writes the formatted candidate output and validation report to disk using
atomic writes (write to a .tmp file, then os.replace) so a crash or
concurrent read never sees a half-written file. Creates output/reports/logs
directories on demand. Never raises — failures are logged and reported back
to the caller as a result object instead of propagating.
"""
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from utils.logger import logger

REPORTS_SUBDIR = "reports"
LOGS_SUBDIR = "logs"


@dataclass
class ExportResult:
    """Outcome of an export operation."""
    success: bool
    path: Optional[str] = None
    error: Optional[str] = None


class FileExporter:
    """Writes output files (candidate.json, validation_report.json) atomically."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.getcwd()

    def _ensure_dirs(self, output_directory: str) -> None:
        for d in (
            self._resolve(output_directory),
            self._resolve(REPORTS_SUBDIR),
            self._resolve(LOGS_SUBDIR),
        ):
            try:
                os.makedirs(d, exist_ok=True)
            except OSError as e:
                logger.error(f"Could not create directory '{d}': {e}")

    def _resolve(self, path: str) -> str:
        return path if os.path.isabs(path) else os.path.join(self.base_dir, path)

    def _atomic_write(self, path: str, content: str) -> ExportResult:
        """Writes `content` to `path` atomically (tmp file + os.replace)."""
        tmp_path = f"{path}.tmp"
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
            logger.info(f"Files Saved: {path}")
            return ExportResult(success=True, path=path)
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to write '{path}': {e}")
            # Best-effort cleanup of the partial tmp file
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass
            return ExportResult(success=False, error=str(e))

    def export_candidate(self, formatted_json: str, output_directory: str, output_filename: str) -> ExportResult:
        """Writes the candidate JSON document atomically.

        Args:
            formatted_json: Already-formatted JSON text (see OutputFormatter).
            output_directory: Directory (relative to base_dir, or absolute).
            output_filename: File name, e.g. "candidate.json".

        Returns:
            ExportResult
        """
        self._ensure_dirs(output_directory)
        path = os.path.join(self._resolve(output_directory), output_filename)
        return self._atomic_write(path, formatted_json)

    def export_validation_report(self, report_dict: Dict[str, Any], output_directory: str,
                                  filename: str = "validation_report.json") -> ExportResult:
        """Writes the validation report JSON atomically into reports/.

        Args:
            report_dict: Dict form of the ValidationReport (see to_dict()).
            output_directory: Base output directory (reports/ is created alongside it).
            filename: Report file name.

        Returns:
            ExportResult
        """
        self._ensure_dirs(output_directory)
        path = os.path.join(self._resolve(output_directory), filename)
        try:
            content = json.dumps(report_dict, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        except (TypeError, ValueError) as e:
            logger.error(f"Could not serialize validation report: {e}")
            return ExportResult(success=False, error=str(e))
        return self._atomic_write(path, content)
