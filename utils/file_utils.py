"""
File utility helpers for the Multi-Source Candidate Data Transformer.

Provides lightweight, side-effect-free helpers for path checking, size
calculation, and pre-parse validation.  All validation failures raise typed
exceptions from ``utils.exceptions`` so callers can handle each case precisely
without parsing generic error messages.
"""
import os
from typing import List

from utils.exceptions import FileValidationError, UnsupportedFileTypeError

# Default maximum file size accepted by validate_file()
_DEFAULT_MAX_SIZE_MB: float = 50.0


def file_exists(file_path: str) -> bool:
    """Checks if a file exists and is a regular file.

    Args:
        file_path (str): Path to the file.

    Returns:
        bool: True if the file exists and is a file, False otherwise.
    """
    return os.path.exists(file_path) and os.path.isfile(file_path)


def is_file_empty(file_path: str) -> bool:
    """Checks if a file has size 0 (is empty).

    Args:
        file_path (str): Path to the file.

    Returns:
        bool: True if the file is empty or does not exist, False otherwise.
    """
    if not file_exists(file_path):
        return True
    return os.path.getsize(file_path) == 0


def get_file_extension(file_path: str) -> str:
    """Extracts the file extension in lowercase.

    Args:
        file_path (str): Path to the file.

    Returns:
        str: The lowercase extension including the leading dot (e.g. '.csv', '.pdf').
    """
    return os.path.splitext(file_path)[1].lower()


def get_file_size_mb(file_path: str) -> float:
    """Returns the size of a file in megabytes.

    Args:
        file_path (str): Path to the file.

    Returns:
        float: File size in MB, or 0.0 if the file does not exist.
    """
    if not file_exists(file_path):
        return 0.0
    return os.path.getsize(file_path) / (1024 * 1024)


def is_file_readable(file_path: str) -> bool:
    """Checks whether the current process has read permission for the file.

    Args:
        file_path (str): Path to the file.

    Returns:
        bool: True if the file exists and is readable, False otherwise.
    """
    return file_exists(file_path) and os.access(file_path, os.R_OK)


def validate_file(
    file_path: str,
    allowed_extensions: List[str],
    max_size_mb: float = _DEFAULT_MAX_SIZE_MB,
) -> None:
    """Validates a file before parsing begins.

    Checks performed in order:
    1. File exists and is a regular file.
    2. File has read permission.
    3. File extension is in ``allowed_extensions``.
    4. File is not empty (0 bytes).
    5. File size does not exceed ``max_size_mb``.

    Args:
        file_path (str): Path to the file to validate.
        allowed_extensions (List[str]): Accepted extensions, e.g. ``[".pdf"]``.
            Values should be lowercase and include the leading dot.
        max_size_mb (float): Maximum allowed file size in megabytes.
            Defaults to 50 MB.

    Raises:
        FileValidationError: If the file does not exist, is unreadable, is
            empty, or exceeds the size limit.
        UnsupportedFileTypeError: If the file extension is not in
            ``allowed_extensions``.
    """
    if not file_exists(file_path):
        raise FileValidationError(f"File not found: {file_path}")

    if not is_file_readable(file_path):
        raise FileValidationError(
            f"File is not readable (permission denied): {file_path}"
        )

    ext = get_file_extension(file_path)
    normalised_allowed = [e.lower() for e in allowed_extensions]
    if ext not in normalised_allowed:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{ext}'. "
            f"Expected one of: {allowed_extensions}"
        )

    if is_file_empty(file_path):
        raise FileValidationError(f"File is empty (0 bytes): {file_path}")

    size_mb = get_file_size_mb(file_path)
    if size_mb > max_size_mb:
        raise FileValidationError(
            f"File exceeds maximum allowed size of {max_size_mb} MB "
            f"(actual: {size_mb:.1f} MB): {file_path}"
        )
