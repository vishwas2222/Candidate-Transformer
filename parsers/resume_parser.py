import os
import pdfplumber
from typing import Dict, Any, Optional
from parsers.base_parser import (
    BaseParser,
    ParserFileNotFoundError,
    ParserEmptyFileError,
    ParserInvalidFormatError,
)
from extractors.resume_extractor import ResumeExtractor
from models.candidate import Candidate
from utils.file_utils import file_exists, is_file_empty
from utils.logger import logger

class ResumeParser(BaseParser):
    """Parser for extracting candidate details from resume PDF files."""

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.text: Optional[str] = None

    def load(self) -> str:
        """Loads and extracts text from the PDF file using pdfplumber.
        
        Raises:
            ParserFileNotFoundError: If the file does not exist.
            ParserEmptyFileError: If the file is 0 bytes or text cannot be extracted.
            ParserInvalidFormatError: If the PDF is corrupted or unreadable.
        """
        logger.info(f"Reading Resume: {self.file_path}")
        
        if not file_exists(self.file_path):
            logger.error(f"Missing File: {self.file_path}")
            raise ParserFileNotFoundError(f"PDF file not found: {self.file_path}")
            
        if is_file_empty(self.file_path):
            logger.error(f"Empty PDF: {self.file_path}")
            raise ParserEmptyFileError(f"PDF file is empty (0 bytes): {self.file_path}")
            
        try:
            extracted_pages = []
            with pdfplumber.open(self.file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_pages.append(page_text)
                        
            if not extracted_pages:
                logger.error(f"Empty PDF content: {self.file_path}")
                raise ParserEmptyFileError(f"PDF file contains no extractable text content: {self.file_path}")
                
            self.text = "\n".join(extracted_pages)
            return self.text
            
        except ParserEmptyFileError:
            raise
        except Exception as e:
            logger.error(f"Corrupted or Unreadable PDF: {self.file_path} - {str(e)}")
            raise ParserInvalidFormatError(f"Failed to read PDF file (corrupted or wrong format): {str(e)}")

    def parse(self) -> Dict[str, Any]:
        """Parses candidate information from the extracted resume text.
        
        Returns:
            Dict[str, Any]: Standard candidate dictionary.
        """
        if self.text is None:
            self.load()
            
        # Segment raw resume text into sections (Experience, Education, Skills, Header)
        sections = ResumeExtractor.extract_sections(self.text)
        
        # Run extraction pipeline
        logger.info("Extracting candidate information")
        name = ResumeExtractor.extract_name(self.text, sections)
        
        logger.info("Extracting Emails")
        emails = ResumeExtractor.extract_emails(self.text)
        
        logger.info("Extracting Phones")
        phones = ResumeExtractor.extract_phones(self.text)
        
        logger.info("Extracting Skills")
        skills = ResumeExtractor.extract_skills(self.text, sections)
        
        experience = ResumeExtractor.extract_experience(sections)
        education = ResumeExtractor.extract_education(sections)
        
        # Populate unified Candidate dataclass
        candidate = Candidate(
            full_name=name,
            emails=emails,
            phones=phones,
            headline="",
            current_company="",
            title="",
            skills=skills,
            experience=experience,
            education=education,
            source=os.path.basename(self.file_path)
        )
        
        return candidate.to_dict()
