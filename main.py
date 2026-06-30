import json
from parsers.csv_parser import CSVParser
from parsers.resume_parser import ResumeParser
from parsers.base_parser import ParserError
from utils.logger import logger

def main():
    """Main CLI entrypoint to execute parsing of CSV and Resume PDF files."""
    csv_path = "inputs/recruiter.csv"
    resume_path = "inputs/sample_resume.pdf"
    
    # 1. Process Recruiter CSV
    try:
        csv_parser = CSVParser(csv_path)
        csv_data = csv_parser.parse()
        print("CSV Output")
        print(json.dumps(csv_data, indent=4))
    except ParserError as e:
        logger.error(f"Gracefully skipped CSV parsing: {str(e)}")
        
    print()
    
    # 2. Process Resume PDF
    try:
        resume_parser = ResumeParser(resume_path)
        resume_data = resume_parser.parse()
        print("Resume Output")
        print(json.dumps(resume_data, indent=4))
    except ParserError as e:
        logger.error(f"Gracefully skipped Resume parsing: {str(e)}")

if __name__ == "__main__":
    main()
