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
        val = field_meta.value
        lines.append(f"  {key.upper()}")

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


def main():
    """Main CLI entrypoint to execute parsing, normalization, and merging."""
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
    else:
        logger.error("No candidate data extracted from any source. Merge aborted.")


if __name__ == "__main__":
    main()
