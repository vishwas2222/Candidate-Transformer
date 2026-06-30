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
from utils.file_utils import validate_file, file_exists, is_file_empty
from utils.exceptions import (
    FileValidationError,
    UnsupportedFileTypeError,
    CorruptedPDFError,
    EmptyResumeError,
)
from utils.logger import logger


class ResumeParser(BaseParser):
    """Parser for extracting candidate details from resume PDF files.

    Validates the file before attempting to open it:
    - Must exist and have read permission.
    - Must have a ``.pdf`` extension (not .docx, .txt, etc.).
    - Must not be empty or exceed MAX_SIZE_MB.
    - Must not be encrypted / password-protected.
    - Must contain at least some extractable text (not a scanned-only PDF).

    Raises specific typed exceptions so the pipeline can handle each failure
    mode precisely without parsing error message strings.
    """

    # Only PDF files are accepted
    SUPPORTED_EXTENSIONS = [".pdf"]
    # Files larger than this are rejected before pdfplumber is opened
    MAX_SIZE_MB: float = 50.0

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.text: Optional[str] = None

    def load(self) -> str:
        """Loads and extracts text from the PDF file using pdfplumber.

        Raises:
            ParserFileNotFoundError: File does not exist.
            ParserEmptyFileError: File is 0 bytes.
            UnsupportedFileTypeError: Extension is not ``.pdf``.
            FileValidationError: File is unreadable or exceeds MAX_SIZE_MB.
            CorruptedPDFError: PDF is encrypted, password-protected, or
                otherwise unreadable by pdfplumber.
            EmptyResumeError: PDF opened successfully but yielded no
                extractable text (typical of scanned / image-only PDFs).
        """
        basename = os.path.basename(self.file_path)
        logger.info(f"Loading Resume: {basename}")
        logger.info("Validating Resume")

        # ── 1. Basic existence check (fast, before heavier validation) ────────
        if not file_exists(self.file_path):
            logger.error(f"Missing File: {self.file_path}")
            raise ParserFileNotFoundError(f"PDF file not found: {self.file_path}")

        if is_file_empty(self.file_path):
            logger.error(f"Empty PDF: {self.file_path}")
            raise ParserEmptyFileError(
                f"PDF file is empty (0 bytes): {self.file_path}"
            )

        # ── 2. Extension, readability and size validation ─────────────────────
        try:
            validate_file(
                self.file_path,
                allowed_extensions=self.SUPPORTED_EXTENSIONS,
                max_size_mb=self.MAX_SIZE_MB,
            )
        except UnsupportedFileTypeError:
            ext = os.path.splitext(self.file_path)[1].lower()
            logger.error(
                f"Unsupported file type '{ext}': {self.file_path}. "
                "Only .pdf files are supported."
            )
            raise
        except FileValidationError as exc:
            logger.error(f"File validation failed: {exc}")
            raise

        logger.info(f"Resume Valid: {basename}")

        # ── 3. PDF text extraction ─────────────────────────────────────────────
        try:
            extracted_pages = []
            with pdfplumber.open(self.file_path) as pdf:
                # Detect encrypted / password-protected PDF before iterating pages
                if getattr(pdf.doc, "is_encrypted", False):
                    logger.error(
                        f"Encrypted PDF: {basename} — "
                        "cannot extract text without a password"
                    )
                    raise CorruptedPDFError(
                        f"PDF is encrypted or password-protected: {self.file_path}"
                    )

                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_pages.append(page_text)

        except (CorruptedPDFError, EmptyResumeError):
            raise  # already typed — propagate as-is
        except Exception as exc:
            logger.error(
                f"Corrupted or Unreadable PDF: {basename} — {exc}"
            )
            raise CorruptedPDFError(
                f"Failed to open PDF (corrupted or invalid format): {exc}"
            )

        # ── 4. Scanned / image-only PDF — valid file, zero text ───────────────
        if not extracted_pages:
            logger.warning(
                f"Empty Resume: {basename} — "
                "PDF appears to be scanned; no extractable text found. "
                "OCR is not supported."
            )
            raise EmptyResumeError(
                f"PDF contains no extractable text (likely scanned): "
                f"{self.file_path}"
            )

        self.text = "\n".join(extracted_pages)
        logger.info(
            f"Resume Loaded: {basename} "
            f"({len(self.text):,} chars across {len(extracted_pages)} page(s))"
        )
        return self.text

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
        logger.info("Parsing Experience")
        exp_dicts = ResumeExtractor.extract_experience(sections)
        experience_objects = [Experience.from_dict(e) for e in exp_dicts]
        logger.info(
            f"Parsed {len(experience_objects)} Experience "
            f"entr{'y' if len(experience_objects) == 1 else 'ies'}"
        )

        # ── Education ─────────────────────────────────────────────────────────
        logger.info("Parsing Education")
        edu_dicts = ResumeExtractor.extract_education(sections)
        education_objects = [Education.from_dict(e) for e in edu_dicts]
        logger.info(
            f"Parsed {len(education_objects)} Education "
            f"entr{'y' if len(education_objects) == 1 else 'ies'}"
        )

        # ── Projects ──────────────────────────────────────────────────────────
        logger.info("Parsing Projects")
        proj_dicts = ResumeExtractor.extract_projects(sections)
        project_objects = [Project.from_dict(p) for p in proj_dicts]
        logger.info(
            f"Found {len(project_objects)} "
            f"Project{'s' if len(project_objects) != 1 else ''}"
        )
        for proj in project_objects:
            logger.info(f"Project: {proj.project_name}")

        # ── New fields ────────────────────────────────────────────────────────
        logger.info("Extracting Links")
        links = ResumeExtractor.extract_links(self.text)

        logger.info("Extracting Location")
        location = ResumeExtractor.extract_location(self.text, sections)

        logger.info("Calculating Years of Experience")
        years_experience = ResumeExtractor.extract_years_experience(experience_objects)

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
            location=location,
            links=links,
            years_experience=years_experience,
        )

        return candidate.to_dict()

