"""
api.py — Flask HTTP API for the Multi-Source Candidate Data Transformer.

Wraps the existing CLI pipeline (parsers → normalizer → merger → output layer)
behind a single REST endpoint so the React frontend can consume it.

Endpoint
--------
POST /api/transform
    Form fields:
        resume  (file, required)  — PDF resume
        csv     (file, optional)  — Recruiter CSV
        config  (str,  optional)  — Output profile: default | minimal | recruiter | analytics

Response (200)
--------------
{
    "candidate":          { ... },   // projected candidate document
    "validation_report":  { ... }    // SchemaValidator report dict
}

Error responses
---------------
400  Bad Request   — missing resume, unsupported file type, validation failure
500  Internal      — unexpected processing error
"""

import json
import os
import tempfile
import traceback

from flask import Flask, jsonify, request
from flask_cors import CORS

# ── Make sure the project root is on the path so all existing imports work ──
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parsers.csv_parser import CSVParser
from parsers.resume_parser import ResumeParser
from parsers.base_parser import ParserError
from transformers.normalization_pipeline import NormalizationPipeline
from merger.candidate_merger import CandidateMerger
from config.config_loader import ConfigLoader
from projection.serializer import CandidateSerializer
from projection.output_formatter import OutputFormatter
from validation.schema_validator import SchemaValidator
from utils.exceptions import (
    UnsupportedFileTypeError,
    CorruptedPDFError,
    EmptyResumeError,
    FileValidationError,
    CorruptedCSVError,
)
from utils.logger import logger

# ── App ────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

ALLOWED_RESUME_EXT = {".pdf"}
ALLOWED_CSV_EXT    = {".csv"}
VALID_CONFIGS      = {"default", "minimal", "recruiter", "analytics"}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _save_upload(file_storage, suffix: str) -> str:
    """Writes a Werkzeug FileStorage to a named temp file and returns its path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        file_storage.save(path)
    finally:
        os.close(fd)
    return path


def _run_pipeline(resume_path: str | None, csv_path: str | None, config_name: str) -> dict:
    """Runs the full parse → normalize → merge → project → validate pipeline.

    Returns:
        dict with keys "candidate" and "validation_report".
    """
    csv_data    = {}
    resume_data = {}

    # 1. Parse CSV (optional)
    if csv_path:
        try:
            csv_data = CSVParser(csv_path).parse()
        except (ParserError, CorruptedCSVError) as exc:
            logger.warning(f"CSV skipped: {exc}")

    # 2. Parse Resume
    if resume_path:
        resume_data = ResumeParser(resume_path).parse()   # raises on error

    if not csv_data and not resume_data:
        raise ValueError("No candidate data could be extracted from any source.")

    # 3. Normalize
    pipeline   = NormalizationPipeline()
    norm_csv    = pipeline.normalize_candidate(csv_data)    if csv_data    else {}
    norm_resume = pipeline.normalize_candidate(resume_data) if resume_data else {}

    # 4. Merge
    canonical_profile = CandidateMerger().merge(norm_csv, norm_resume)

    # 5. Project / Serialize
    loader = ConfigLoader()
    config, _ = loader.load(config_name)

    source_count = len({
        s for s in (
            norm_csv.get("source", ""),
            norm_resume.get("source", ""),
        ) if s
    })

    serializer = CandidateSerializer()
    document   = serializer.serialize(canonical_profile, config, candidate_sources=source_count)

    # 6. Validate
    report = SchemaValidator().validate(document, config)

    if config.metadata.get("include_validation_summary") and "metadata" in document:
        document["metadata"]["validation_summary"] = report.summary()

    # 7. Format
    formatted_json = OutputFormatter.format(document, config)

    # OutputFormatter may return a JSON string or a dict depending on config.
    # Always return a dict so Flask's jsonify doesn't double-encode.
    import json as _json
    if isinstance(formatted_json, str):
        try:
            formatted_json = _json.loads(formatted_json)
        except _json.JSONDecodeError:
            pass  # leave as-is if it's not valid JSON

    return {
        "candidate":         formatted_json,
        "validation_report": report.to_dict(),
    }



# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/api/transform", methods=["POST"])
def transform():
    """Main transformation endpoint consumed by the React frontend."""

    # ── Validate resume upload ────────────────────────────────────────────────
    if "resume" not in request.files or request.files["resume"].filename == "":
        return jsonify({"error": "A resume PDF file is required."}), 400

    resume_file = request.files["resume"]
    resume_name = resume_file.filename.lower()
    if not any(resume_name.endswith(ext) for ext in ALLOWED_RESUME_EXT):
        return jsonify({"error": "Resume must be a PDF file (.pdf)."}), 400

    # ── Optional CSV ──────────────────────────────────────────────────────────
    csv_file = None
    if "csv" in request.files and request.files["csv"].filename != "":
        csv_file = request.files["csv"]
        csv_name = csv_file.filename.lower()
        if not any(csv_name.endswith(ext) for ext in ALLOWED_CSV_EXT):
            return jsonify({"error": "Recruiter file must be a CSV (.csv)."}), 400

    # ── Config profile ────────────────────────────────────────────────────────
    config_name = (request.form.get("config") or "default").lower().strip()
    if config_name not in VALID_CONFIGS:
        config_name = "default"

    # ── Save uploads to temp files ────────────────────────────────────────────
    resume_path = None
    csv_path    = None
    try:
        resume_path = _save_upload(resume_file, suffix=".pdf")
        if csv_file:
            csv_path = _save_upload(csv_file, suffix=".csv")

        # ── Run pipeline ──────────────────────────────────────────────────────
        result = _run_pipeline(resume_path, csv_path, config_name)
        return jsonify(result), 200

    except (UnsupportedFileTypeError, FileValidationError) as exc:
        return jsonify({"error": f"File error: {exc}"}), 400

    except (CorruptedPDFError, EmptyResumeError) as exc:
        return jsonify({"error": f"Could not read PDF: {exc}"}), 400

    except (CorruptedCSVError, ParserError) as exc:
        return jsonify({"error": f"Could not parse file: {exc}"}), 400

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    except Exception as exc:          # pylint: disable=broad-except
        logger.error(f"Unexpected error: {exc}\n{traceback.format_exc()}")
        return jsonify({"error": "An unexpected server error occurred. Please try again."}), 500

    finally:
        # Always clean up temp files
        for path in (resume_path, csv_path):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


@app.route("/api/health", methods=["GET"])
def health():
    """Simple liveness probe."""
    return jsonify({"status": "ok", "service": "candidate-transformer"}), 200


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
