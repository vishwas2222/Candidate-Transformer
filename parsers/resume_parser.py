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
from models.experience import Experience
from models.education import Education
from models.project import Project
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
                raise ParserEmptyFileError(
                    f"PDF file contains no extractable text content: {self.file_path}"
                )

            self.text = "\n".join(extracted_pages)
            return self.text

        except ParserEmptyFileError:
            raise
        except Exception as e:
            logger.error(f"Corrupted or Unreadable PDF: {self.file_path} - {str(e)}")
            raise ParserInvalidFormatError(
                f"Failed to read PDF file (corrupted or wrong format): {str(e)}"
            )

    def parse(self) -> Dict[str, Any]:
        """Parses candidate information from the extracted resume text.

        Returns:
            Dict[str, Any]: Standard candidate dictionary.
        """
        if self.text is None:
            self.load()

        source_name = os.path.basename(self.file_path)

        # Segment raw resume text into sections
        sections = ResumeExtractor.extract_sections(self.text)

        # ── Contact info ──────────────────────────────────────────────────────
        logger.info("Extracting candidate information")
        name = ResumeExtractor.extract_name(self.text, sections)

        logger.info("Extracting Emails")
        emails = ResumeExtractor.extract_emails(self.text)

        logger.info("Extracting Phones")
        phones = ResumeExtractor.extract_phones(self.text)

        # ── Skills ────────────────────────────────────────────────────────────
        logger.info("Extracting Skills")
        skills = ResumeExtractor.extract_skills(self.text, sections)

        # ── Experience ────────────────────────────────────────────────────────
        logger.info("Extracting Experience")
        exp_dicts = ResumeExtractor.extract_experience(sections)
        experience_objects = [Experience.from_dict(e) for e in exp_dicts]
        logger.info(f"Parsed {len(experience_objects)} Experience entr{'y' if len(experience_objects)==1 else 'ies'}")

        # ── Education ─────────────────────────────────────────────────────────
        logger.info("Extracting Education")
        edu_dicts = ResumeExtractor.extract_education(sections)
        education_objects = [Education.from_dict(e) for e in edu_dicts]
        logger.info(f"Parsed {len(education_objects)} Education entr{'y' if len(education_objects)==1 else 'ies'}")

        # ── Projects ──────────────────────────────────────────────────────────
        logger.info("Extracting Projects")
        proj_dicts = ResumeExtractor.extract_projects(sections)
        project_objects = [Project.from_dict(p) for p in proj_dicts]
        logger.info(f"Found {len(project_objects)} Project{'s' if len(project_objects)!=1 else ''}")
        for proj in project_objects:
            logger.info(f"Project: {proj.project_name}")

        # ── Populate Candidate ────────────────────────────────────────────────
        candidate = Candidate(
            full_name=name,
            emails=emails,
            phones=phones,
            headline="",
            current_company="",
            title="",
            skills=skills,
            experience=experience_objects,
            education=education_objects,
            projects=project_objects,
            source=source_name,
        )

        return candidate.to_dict()
