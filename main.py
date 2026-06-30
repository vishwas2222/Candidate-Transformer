import json
from parsers.csv_parser import CSVParser
from parsers.resume_parser import ResumeParser
from parsers.base_parser import ParserError
from transformers.normalization_pipeline import NormalizationPipeline
from merger.candidate_merger import CandidateMerger
from utils.logger import logger

def format_canonical_candidate(cc) -> str:
    """Formats the CanonicalCandidate object details for display in console."""
    lines = ["\nCanonical Candidate Profile", "=" * 60]
    for key, field_meta in cc.__dict__.items():
        val = field_meta.value
        
        # Nicely represent structured list elements like Experience and Education
        if isinstance(val, list) and len(val) > 0 and hasattr(val[0], '__dict__'):
            val_str = "\n" + "\n".join(f"    - {str(item)}" for item in val)
        else:
            val_str = str(val)
            
        lines.append(f"{key.upper():<16}: {val_str}")
        lines.append(f"  Confidence    : {field_meta.confidence:.2f}")
        lines.append(f"  Sources       : {field_meta.sources}")
        lines.append("-" * 60)
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
        
        # Normalize CSV data if present
        norm_csv = pipeline.normalize_candidate(csv_data) if csv_data else {}
        
        # Normalize Resume data if present
        norm_resume = pipeline.normalize_candidate(resume_data) if resume_data else {}
        
        # Merge candidate profiles
        merger = CandidateMerger()
        canonical_profile = merger.merge(norm_csv, norm_resume)
        
        # Print Canonical Candidate
        print(format_canonical_candidate(canonical_profile))
    else:
        logger.error("No candidate data extracted from any source. Merge aborted.")

if __name__ == "__main__":
    main()
