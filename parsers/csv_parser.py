import os
import pandas as pd
from typing import Dict, Any, Optional
from parsers.base_parser import (
    BaseParser,
    ParserFileNotFoundError,
    ParserEmptyFileError,
    ParserInvalidFormatError,
)
from models.candidate import Candidate
from utils.file_utils import file_exists, is_file_empty
from utils.logger import logger

class CSVParser(BaseParser):
    """Parser for extracting candidate information from recruiter CSV files."""

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.df: Optional[pd.DataFrame] = None

    def load(self) -> pd.DataFrame:
        """Loads and reads the CSV file into a pandas DataFrame.
        
        Raises:
            ParserFileNotFoundError: If the file does not exist.
            ParserEmptyFileError: If the file has 0 bytes.
            ParserInvalidFormatError: If pandas fails to parse the CSV file.
        """
        logger.info(f"Reading CSV: {self.file_path}")
        
        if not file_exists(self.file_path):
            logger.error(f"Missing File: {self.file_path}")
            raise ParserFileNotFoundError(f"CSV file not found: {self.file_path}")
            
        if is_file_empty(self.file_path):
            logger.error(f"Empty CSV: {self.file_path}")
            raise ParserEmptyFileError(f"CSV file is empty: {self.file_path}")
            
        try:
            # We enforce dtype=str to avoid converting phone numbers/IDs to numeric types (e.g. floats, losing leading zeroes)
            self.df = pd.read_csv(self.file_path, dtype=str)
        except Exception as e:
            logger.error(f"Malformed CSV: {self.file_path} - {str(e)}")
            raise ParserInvalidFormatError(f"Failed to parse CSV file: {str(e)}")
            
        # A file with just headers and no data rows is still considered an empty dataset
        if self.df.empty:
            logger.error(f"Empty CSV: {self.file_path} (No data rows)")
            raise ParserEmptyFileError("CSV file has no candidate data rows.")
            
        return self.df

    def parse(self) -> Dict[str, Any]:
        """Parses candidate information from the loaded CSV DataFrame.
        
        Returns:
            Dict[str, Any]: Standard candidate dictionary.
            
        Raises:
            ParserInvalidFormatError: If required columns are missing.
        """
        if self.df is None:
            self.load()
            
        required_cols = {"Name", "Email", "Phone", "Company", "Title"}
        actual_cols = set(self.df.columns)
        
        missing_cols = required_cols - actual_cols
        if missing_cols:
            logger.error(f"Wrong CSV columns: Missing {missing_cols}")
            raise ParserInvalidFormatError(f"CSV is missing required columns: {missing_cols}")
            
        # Get the first candidate row in the CSV
        row = self.df.iloc[0]
        
        # Helper to convert pandas values (NaN is float) to strings safely
        def safe_str(val: Any) -> str:
            if pd.isna(val) or val is None:
                return ""
            return str(val)

        email = safe_str(row["Email"])
        phone = safe_str(row["Phone"])
        
        candidate = Candidate(
            full_name=safe_str(row["Name"]),
            emails=[email] if email else [],
            phones=[phone] if phone else [],
            headline="",
            current_company=safe_str(row["Company"]),
            title=safe_str(row["Title"]),
            skills=[],
            experience=[],
            education=[],
            source=os.path.basename(self.file_path)
        )
        
        return candidate.to_dict()
