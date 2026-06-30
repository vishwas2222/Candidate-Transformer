import argparse
import json
from parsers.csv_parser import CSVParser
from parsers.resume_parser import ResumeParser
from parsers.base_parser import ParserError
from transformers.normalization_pipeline import NormalizationPipeline
from merger.candidate_merger import CandidateMerger
from models.project import Project
from models.experience import Experience
from models.education import Education
from utils.logger import logger

from config.config_loader import ConfigLoader
from projection.serializer import CandidateSerializer
from projection.output_formatter import OutputFormatter
from validation.schema_validator import SchemaValidator
from exporter.file_exporter import FileExporter


def _fmt_list(items, indent=6):
    """Format a list of strings as indented bullet lines."""
    if not items:
        return "(none)"
    return "\n" + "\n".join(" " * indent + f"- {item}" for item in items)


def format_canonical_candidate(cc) -> str:
    """Formats the CanonicalCandidate object for console display."""
    SEP = "=" * 64
    DASH = "-" * 64
    lines = ["\nCanonical Candidate Profile", SEP]

    for key, field_meta in cc.__dict__.items():
        lines.append(f"  {key.upper()}")

        # Plain scalar (e.g. overall_confidence: float) — not a CandidateField
        if not hasattr(field_meta, "value"):
            lines.append(f"    Value      : {field_meta}")
            continue

        val = field_meta.value

        # ── Scalar fields ──────────────────────────────────────────
        if isinstance(val, str) or not hasattr(val, '__iter__'):
            lines.append(f"    Value      : {val}")

        # ── List of strings (emails, phones, skills) ───────────────
        elif isinstance(val, list) and (not val or isinstance(val[0], str)):
            lines.append(f"    Value      : {val}")

        # ── List of structured objects ─────────────────────────────
        elif isinstance(val, list):
            for i, obj in enumerate(val, 1):
                if isinstance(obj, Experience):
                    lines.append(f"    [{i}] Experience")
                    lines.append(f"        Title    : {obj.title}")
                    lines.append(f"        Company  : {obj.company}")
                    lines.append(f"        Location : {obj.location}")
                    lines.append(f"        Period   : {obj.start_date} – {obj.end_date}")
                    if obj.description:
                        lines.append(f"        Bullets  :{_fmt_list(obj.description, indent=10)}")

                elif isinstance(obj, Education):
                    lines.append(f"    [{i}] Education")
                    lines.append(f"        Degree         : {obj.degree}")
                    lines.append(f"        Specialization : {obj.specialization}")
                    lines.append(f"        Institution    : {obj.institution or obj.school}")
                    lines.append(f"        Period         : {obj.start_date} – {obj.end_date}")
                    if obj.cgpa:
                        lines.append(f"        CGPA           : {obj.cgpa}")
                    if obj.percentage:
                        lines.append(f"        Percentage     : {obj.percentage}%")
                    if obj.grade:
                        lines.append(f"        Grade          : {obj.grade}")
                    if obj.description:
                        lines.append(f"        Notes          :{_fmt_list(obj.description, indent=10)}")

                elif isinstance(obj, Project):
                    lines.append(f"    [{i}] Project")
                    lines.append(f"        Name   : {obj.project_name}")
                    lines.append(f"        Period : {obj.start_date} – {obj.end_date}")
                    lines.append(f"        Tech   : {', '.join(obj.technology_stack) or '(none)'}")
                    if obj.description:
                        lines.append(f"        Desc   :{_fmt_list(obj.description, indent=10)}")

                else:
                    lines.append(f"    [{i}] {str(obj)}")

        lines.append(f"    Confidence : {field_meta.confidence:.2f}")
        lines.append(f"    Sources    : {field_meta.sources}")
        lines.append(DASH)

    return "\n".join(lines)


def run_output_layer(canonical_profile, profile_name: str, candidate_sources: int = 2) -> None:
    """Runs Part 3 (the Output Layer) against an already-built CanonicalCandidate.

    This is purely additive on top of the existing parse/normalize/merge
    pipeline: it never reads from or modifies the canonical profile in place,
    it only projects a NEW view of it per the selected config profile.

    Args:
        canonical_profile: The CanonicalCandidate produced by Part 2 (merger).
        profile_name: Name of the output config profile to use (e.g. "default").
        candidate_sources: Number of source systems merged into the candidate,
            used for output metadata.
    """
    logger.info(f"Loading Config: {profile_name}")
    loader = ConfigLoader()
    config, config_issues = loader.load(profile_name)
    for issue in config_issues:
        log_fn = {"ERROR": logger.error, "WARNING": logger.warning, "INFO": logger.info}.get(
            issue.severity, logger.info
        )
        log_fn(f"Config[{issue.severity}] {issue.message}")

    logger.info("Validating Config")
    logger.info("Projection Started")
    serializer = CandidateSerializer()
    document = serializer.serialize(canonical_profile, config, candidate_sources=candidate_sources)
    logger.info("Projection Completed")

    logger.info("Schema Validation Started")
    report = SchemaValidator().validate(document, config)
    if report.is_valid:
        logger.info("Schema Validation Passed")
    else:
        logger.error(f"Schema Validation Failed: {len(report.errors)} error(s)")
    logger.info("Validation Report Generated")

    if config.metadata.get("include_validation_summary") and "metadata" in document:
        document["metadata"]["validation_summary"] = report.summary()

    logger.info("Serialization Started")
    formatted_json = OutputFormatter.format(document, config)
    logger.info("Output Generated")

    exporter = FileExporter()
    candidate_result = exporter.export_candidate(formatted_json, config.output_directory, config.output_filename)
    report_result = exporter.export_validation_report(report.to_dict(), config.output_directory)

    if candidate_result.success:
        logger.info(f"Files Saved: {candidate_result.path}")
    else:
        logger.error(f"Could not save candidate output: {candidate_result.error}")

    if report_result.success:
        logger.info(f"Files Saved: {report_result.path}")
    else:
        logger.error(f"Could not save validation report: {report_result.error}")


def _parse_args():
    parser = argparse.ArgumentParser(description="Multi-Source Candidate Data Transformer")
    parser.add_argument(
        "--config", dest="config", default="default",
        help="Output config profile to use (default, recruiter, analytics, minimal, developer).",
    )
    return parser.parse_args()


def main():
    """Main CLI entrypoint to execute parsing, normalization, merging, and output."""
    args = _parse_args()

    csv_path = "inputs/recruiter.csv"
    resume_path = "inputs/sample_resume.pdf"

    csv_data = {}
    resume_data = {}

    # 1. Process and Extract Recruiter CSV
    try:
        csv_parser = CSVParser(csv_path)
        csv_data = csv_parser.parse()
    except ParserError as e:
        logger.error(f"Gracefully skipped CSV parsing: {str(e)}")

    # 2. Process and Extract Resume PDF
    try:
        resume_parser = ResumeParser(resume_path)
        resume_data = resume_parser.parse()
    except ParserError as e:
        logger.error(f"Gracefully skipped Resume parsing: {str(e)}")

    # Proceed to Normalization and Merger if we have parsed candidate data
    if csv_data or resume_data:
        pipeline = NormalizationPipeline()

        norm_csv = pipeline.normalize_candidate(csv_data) if csv_data else {}
        norm_resume = pipeline.normalize_candidate(resume_data) if resume_data else {}

        merger = CandidateMerger()
        canonical_profile = merger.merge(norm_csv, norm_resume)

        print(format_canonical_candidate(canonical_profile))

        source_count = len({s for s in (norm_csv.get("source", ""), norm_resume.get("source", "")) if s})
        run_output_layer(canonical_profile, args.config, candidate_sources=source_count)
    else:
        logger.error("No candidate data extracted from any source. Merge aborted.")


if __name__ == "__main__":
    main()
