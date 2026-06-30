from abc import ABC, abstractmethod
from typing import Dict, Any

# Re-export new domain exceptions so callers can import them from here
# without breaking any existing "from parsers.base_parser import ..." statements.
from utils.exceptions import (  # noqa: F401
    CandidateTransformerError,
    FileValidationError,
    UnsupportedFileTypeError,
    CorruptedPDFError,
    EmptyResumeError,
    CorruptedCSVError,
    PipelineError,
    ValidationError,
    SerializationError,
    ConfigurationError,
)

class ParserError(Exception):
    """Base class for all parser exceptions."""
    pass

class ParserFileNotFoundError(ParserError):
    """Raised when the file to be parsed is not found on the filesystem."""
    pass

class ParserEmptyFileError(ParserError):
    """Raised when the file to be parsed has a size of 0 bytes."""
    pass

class ParserInvalidFormatError(ParserError):
    """Raised when the file format or file contents are malformed or invalid."""
    pass

class BaseParser(ABC):
    """Abstract base class for all candidate source parsers."""

    def __init__(self, file_path: str):
        """Initializes the parser with a file path.
        
        Args:
            file_path (str): Path to the input file.
        """
        self.file_path = file_path

    @abstractmethod
    def load(self) -> Any:
        """Loads the content of the file.
        
        This method should verify file existence, file size (empty checks),
        and open the file, returning raw file data or text content.
        
        Raises:
            ParserFileNotFoundError: If the file does not exist.
            ParserEmptyFileError: If the file is empty.
            ParserInvalidFormatError: If the file is unreadable or incorrect format.
        """
        pass

    @abstractmethod
    def parse(self) -> Dict[str, Any]:
        """Parses candidate data and returns it in the standard candidate dictionary format.
        
        Returns:
            Dict[str, Any]: Unified candidate dictionary representation.
            
        Raises:
            ParserError: If any parsing or extraction error occurs.
        """
        pass
