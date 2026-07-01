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


def _unwrap(v):
    """Unwrap a CandidateField dict to its plain value."""
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    return v


def _shape_to_schema(raw: dict, config_name: str) -> dict:
    """Map the internal pipeline output to the exact Eightfold assignment schema.

    Assignment schema fields:
      candidate_id, full_name, emails, phones (E.164), location, links,
      headline, years_experience, skills [{name,confidence,sources}],
      experience [{company,title,start,end,summary}],
      education [{institution,degree,field,end_year}],
      provenance [{field,source,method}], overall_confidence
    """
    # The serializer may nest the candidate under a "candidate" key
    raw_c = raw.get("candidate", raw) if isinstance(raw, dict) else raw

    # ── Unwrap all top-level CandidateField wrappers ───────────────────────
    def uw(key):
        return _unwrap(raw_c.get(key))

    # ── Skills → [{name, confidence, sources}] ────────────────────────────
    raw_skills = uw("skills") or []
    if raw_skills and isinstance(raw_skills[0], str):
        # Plain string list — wrap in schema shape
        skills_out = [
            {"name": s, "confidence": 0.9, "sources": ["resume"]}
            for s in raw_skills
        ]
    elif raw_skills and isinstance(raw_skills[0], dict) and "name" in raw_skills[0]:
        skills_out = raw_skills      # already shaped
    else:
        skills_out = [
            {"name": str(s), "confidence": 0.9, "sources": ["resume"]}
            for s in raw_skills if s
        ]

    # ── Education → [{institution, degree, field, end_year}] ─────────────
    raw_edu = uw("education") or []
    edu_out = []
    for e in raw_edu:
        if not isinstance(e, dict):
            continue
        field_name = (
            e.get("specialization") or e.get("field") or ""
        ).rstrip(".")
        end_year_raw = e.get("end_date") or e.get("end_year") or ""
        if isinstance(end_year_raw, str) and "-" in end_year_raw:
            end_year = end_year_raw.split("-")[0]
        else:
            end_year = str(end_year_raw) if end_year_raw else ""

        edu_entry = {
            "institution": e.get("institution") or e.get("school") or "",
            "degree":      e.get("degree") or "",
            "field":       field_name,
            "end_year":    end_year,
        }
        # Include grade info if present (bonus info, not in base schema)
        cgpa = e.get("cgpa") or ""
        pct  = e.get("percentage") or ""
        if cgpa:
            edu_entry["cgpa"] = cgpa
        if pct:
            edu_entry["percentage"] = pct
        edu_out.append(edu_entry)

    # ── Experience → [{company, title, start, end, summary}] ─────────────
    raw_exp = uw("experience") or []
    exp_out = []
    for e in raw_exp:
        if not isinstance(e, dict):
            continue
        desc = e.get("description") or e.get("summary") or []
        summary = " ".join(desc) if isinstance(desc, list) else str(desc)
        exp_out.append({
            "company": e.get("company") or e.get("organisation") or "",
            "title":   e.get("title")   or e.get("role")         or "",
            "start":   e.get("start_date") or e.get("start")     or "",
            "end":     e.get("end_date")   or e.get("end")       or "",
            "summary": summary,
        })

    # ── Provenance → [{field, source, method}] ────────────────────────────
    provenance = []
    for key in ("full_name", "emails", "phones", "skills", "education",
                "experience", "location", "links", "headline", "years_experience"):
        raw_field = raw_c.get(key)
        if isinstance(raw_field, dict) and "sources" in raw_field:
            provenance.append({
                "field":  key,
                "source": ", ".join(raw_field["sources"]) if raw_field["sources"] else "resume",
                "method": "regex-extraction" if "resume" in str(raw_field.get("sources", [])) else "csv-parse",
            })

    # ── Location ─────────────────────────────────────────────────────────
    loc_raw = uw("location") or {}
    location = {
        "city":    loc_raw.get("city", "")    if isinstance(loc_raw, dict) else "",
        "region":  loc_raw.get("region", "")  if isinstance(loc_raw, dict) else "",
        "country": loc_raw.get("country", "") if isinstance(loc_raw, dict) else "",
    }

    # ── Links ────────────────────────────────────────────────────────────
    links_raw = uw("links") or {}
    links = {
        "linkedin":  links_raw.get("linkedin", "")  if isinstance(links_raw, dict) else "",
        "github":    links_raw.get("github", "")    if isinstance(links_raw, dict) else "",
        "portfolio": links_raw.get("portfolio", "") if isinstance(links_raw, dict) else "",
        "other":     links_raw.get("other", [])     if isinstance(links_raw, dict) else [],
    }

    # ── Include provenance / confidence only for analytics config ─────────
    include_conf = config_name == "analytics"

    shaped = {
        "candidate_id":       uw("candidate_id")      or "",
        "full_name":          uw("full_name")          or "",
        "emails":             uw("emails")             or [],
        "phones":             uw("phones")             or [],
        "location":           location,
        "links":              links,
        "headline":           uw("headline")           or None,
        "years_experience":   uw("years_experience"),
        "skills":             skills_out,
        "experience":         exp_out,
        "education":          edu_out,
        "provenance":         provenance if include_conf else [],
        "overall_confidence": raw_c.get("overall_confidence"),
    }

    return shaped


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

    shaped = _shape_to_schema(formatted_json, config_name)
    return {
        "candidate":         shaped,
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


@app.route("/api/transform/batch", methods=["POST"])
def transform_batch():
    """Batch transformation endpoint — accepts multiple resume PDFs.

    Form fields:
        resumes   (files, required) — one or more PDF resumes
        csv       (file,  optional) — single recruiter CSV applied to all
        config    (str,   optional) — output profile
    """
    resume_files = request.files.getlist("resumes")
    resume_files = [f for f in resume_files if f.filename != ""]

    if not resume_files:
        return jsonify({"error": "At least one resume PDF is required."}), 400

    # Validate each resume extension
    for rf in resume_files:
        if not rf.filename.lower().endswith(".pdf"):
            return jsonify({
                "error": f'"{rf.filename}" is not a PDF. Only .pdf files are accepted.'
            }), 400

    # Optional CSV
    csv_file = None
    if "csv" in request.files and request.files["csv"].filename != "":
        csv_file = request.files["csv"]
        if not csv_file.filename.lower().endswith(".csv"):
            return jsonify({"error": "Recruiter file must be a CSV (.csv)."}), 400

    config_name = (request.form.get("config") or "default").lower().strip()
    if config_name not in VALID_CONFIGS:
        config_name = "default"

    # Save shared CSV once
    csv_path = None
    temp_paths = []
    try:
        if csv_file:
            csv_path = _save_upload(csv_file, suffix=".csv")
            temp_paths.append(csv_path)

        results = []
        for rf in resume_files:
            resume_path = _save_upload(rf, suffix=".pdf")
            temp_paths.append(resume_path)
            try:
                result = _run_pipeline(resume_path, csv_path, config_name)
                result["filename"] = rf.filename
                result["status"]   = "success"
            except (UnsupportedFileTypeError, FileValidationError,
                    CorruptedPDFError, EmptyResumeError,
                    CorruptedCSVError, ParserError, ValueError) as exc:
                result = {
                    "filename": rf.filename,
                    "status":   "error",
                    "error":    str(exc),
                }
            except Exception as exc:          # pylint: disable=broad-except
                logger.error(f"Batch error on {rf.filename}: {exc}\n{traceback.format_exc()}")
                result = {
                    "filename": rf.filename,
                    "status":   "error",
                    "error":    "Unexpected server error processing this file.",
                }
            results.append(result)

        return jsonify({"results": results, "total": len(results)}), 200

    finally:
        for path in temp_paths:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
