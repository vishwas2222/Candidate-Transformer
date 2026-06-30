import os
import io
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
from utils.exceptions import CorruptedCSVError
from utils.logger import logger


class CSVParser(BaseParser):
    """Parser for extracting candidate information from recruiter CSV files.

    Robustness features:
    - Encoding fallback: tries UTF-8 first, then latin-1.
    - Delimiter sniffing: tries comma, then semicolon, then tab.
    - Warns (does not crash) when a non-comma delimiter is auto-detected.
    - Raises typed ``CorruptedCSVError`` when the file cannot be parsed at all.
    - Required columns: Name, Email, Phone, Company, Title.
    """

    # Encodings to try in order
    _ENCODINGS = ["utf-8", "latin-1"]
    # Delimiters to try in order
    _DELIMITERS = [",", ";", "\t"]
    # Columns that must be present for the parser to proceed
    REQUIRED_COLUMNS = {"Name", "Email", "Phone", "Company", "Title"}

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.df: Optional[pd.DataFrame] = None

    def load(self) -> pd.DataFrame:
        """Loads and reads the CSV file into a pandas DataFrame.

        Attempts multiple encodings and delimiters before giving up.

        Raises:
            ParserFileNotFoundError: File does not exist.
            ParserEmptyFileError: File has 0 bytes or contains no data rows.
            CorruptedCSVError: File cannot be parsed with any known
                encoding/delimiter combination.
        """
        basename = os.path.basename(self.file_path)
        logger.info(f"Loading CSV: {basename}")

        if not file_exists(self.file_path):
            logger.error(f"Missing File: {self.file_path}")
            raise ParserFileNotFoundError(
                f"CSV file not found: {self.file_path}"
            )

        if is_file_empty(self.file_path):
            logger.error(f"Empty CSV: {self.file_path}")
            raise ParserEmptyFileError(
                f"CSV file is empty (0 bytes): {self.file_path}"
            )

        # ── Encoding + delimiter auto-detection ───────────────────────────────
        raw_bytes = self._read_raw_bytes()
        self.df, detected_enc, detected_sep = self._load_dataframe(
            raw_bytes, basename
        )

        # Warn when a non-standard delimiter was detected
        if detected_sep != ",":
            sep_name = {";": "semicolon", "\t": "tab"}.get(detected_sep, repr(detected_sep))
            logger.warning(
                f"Non-comma delimiter detected in {basename}: "
                f"using '{sep_name}' separator."
            )

        if detected_enc != "utf-8":
            logger.warning(
                f"Non-UTF-8 encoding detected in {basename}: "
                f"loaded as '{detected_enc}'."
            )

        # A file with only headers and no data rows is empty for our purposes
        if self.df.empty:
            logger.error(f"Empty CSV: {basename} (no data rows)")
            raise ParserEmptyFileError(
                f"CSV file has no candidate data rows: {self.file_path}"
            )

        logger.info(
            f"CSV Loaded: {basename} "
            f"({len(self.df)} row(s), {len(self.df.columns)} column(s))"
        )
        return self.df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _read_raw_bytes(self) -> bytes:
        """Reads the raw bytes of the CSV file."""
        with open(self.file_path, "rb") as fh:
            return fh.read()

    def _load_dataframe(
        self, raw_bytes: bytes, basename: str
    ):
        """Tries all encoding × delimiter combinations until one succeeds.

        Returns:
            Tuple (DataFrame, encoding_used, delimiter_used)

        Raises:
            CorruptedCSVError: If all attempts fail.
        """
        last_error: Optional[Exception] = None

        for encoding in self._ENCODINGS:
            try:
                text = raw_bytes.decode(encoding)
            except (UnicodeDecodeError, LookupError) as exc:
                last_error = exc
                continue  # try next encoding

            for sep in self._DELIMITERS:
                try:
                    # dtype=str preserves phone numbers, IDs, etc.
                    df = pd.read_csv(
                        io.StringIO(text),
                        sep=sep,
                        dtype=str,
                        engine="python",  # required for multi-char separators
                    )
                    # A single-column result from a comma-separated CSV usually
                    # means the delimiter guess was wrong — try the next one.
                    if len(df.columns) == 1 and sep != self._DELIMITERS[-1]:
                        continue
                    return df, encoding, sep
                except Exception as exc:
                    last_error = exc
                    continue

        raise CorruptedCSVError(
            f"Failed to parse CSV '{basename}' with any supported "
            f"encoding ({self._ENCODINGS}) or delimiter "
            f"({self._DELIMITERS}). Last error: {last_error}"
        )

    def parse(self) -> Dict[str, Any]:
        """Parses candidate information from the loaded CSV DataFrame.

        Returns:
            Dict[str, Any]: Standard candidate dictionary.

        Raises:
            ParserInvalidFormatError: Required columns are missing.
        """
        if self.df is None:
            self.load()

        actual_cols = set(self.df.columns)
        missing_cols = self.REQUIRED_COLUMNS - actual_cols
        if missing_cols:
            logger.error(
                f"Wrong CSV columns: missing {missing_cols} "
                f"in {os.path.basename(self.file_path)}"
            )
            raise ParserInvalidFormatError(
                f"CSV is missing required columns: {missing_cols}"
            )

        # Use the first candidate row
        row = self.df.iloc[0]

        def safe_str(val: Any) -> str:
            """Converts a pandas cell value (may be NaN) to a clean string."""
            if pd.isna(val) or val is None:
                return ""
            return str(val).strip()

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
            source=os.path.basename(self.file_path),
        )

        return candidate.to_dict()
