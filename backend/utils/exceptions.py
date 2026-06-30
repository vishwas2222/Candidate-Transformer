"""
Domain-specific exception hierarchy for the Multi-Source Candidate Data Transformer.

All custom exceptions extend ``CandidateTransformerError`` so callers can catch
either the specific subclass or the entire family with one ``except`` clause.

The existing ``parsers.base_parser.ParserError`` hierarchy is intentionally kept
for backward compatibility; the exceptions here complement, not replace, them.
"""


class CandidateTransformerError(Exception):
    """Base class for all domain-specific exceptions in this project."""


# ── File / IO ──────────────────────────────────────────────────────────────────

class FileValidationError(CandidateTransformerError):
    """Raised when a file fails pre-parse validation checks.

    Conditions:
    - File does not exist on the filesystem
    - File has 0 bytes
    - File size exceeds the configured maximum
    - File is not readable (permission denied)
    """


class UnsupportedFileTypeError(CandidateTransformerError):
    """Raised when a file has an extension that is not supported by the parser.

    Example: passing a ``.docx`` or ``.txt`` file where a ``.pdf`` is expected.
    """


# ── PDF ───────────────────────────────────────────────────────────────────────

class CorruptedPDFError(CandidateTransformerError):
    """Raised when a PDF file cannot be opened or read.

    Conditions:
    - PDF is encrypted or password-protected
    - PDF internal structure is corrupted / invalid
    - pdfplumber raises an exception during open or page extraction
    """


class EmptyResumeError(CandidateTransformerError):
    """Raised when a PDF contains no extractable text layer.

    This typically happens with scanned PDFs where the content is stored as
    rasterized images rather than selectable text.  The file is structurally
    valid — it simply has no text that pdfplumber can access.
    """


# ── CSV ───────────────────────────────────────────────────────────────────────

class CorruptedCSVError(CandidateTransformerError):
    """Raised when a CSV file cannot be parsed into a usable DataFrame.

    Conditions:
    - File encoding is unrecognizable after all fallback attempts
    - No delimiter can be auto-detected
    - Required columns are absent after loading
    - The CSV structure is fundamentally malformed
    """


# ── Pipeline ──────────────────────────────────────────────────────────────────

class PipelineError(CandidateTransformerError):
    """Raised when the pipeline cannot proceed because all input sources failed.

    This is the terminal error when both the resume and the CSV are unavailable
    or unreadable, leaving no candidate data to process.
    """


# ── Validation & Output ───────────────────────────────────────────────────────

class ValidationError(CandidateTransformerError):
    """Raised when schema validation encounters an unrecoverable structural error.

    Distinct from ``ValidationReport`` warnings/errors which are non-fatal and
    returned as part of the normal output; this exception signals a failure that
    prevents output generation entirely.
    """


class SerializationError(CandidateTransformerError):
    """Raised when the candidate document cannot be serialized to JSON.

    Example: a field contains a value that the JSON encoder cannot handle.
    """


class ConfigurationError(CandidateTransformerError):
    """Raised when an output configuration profile is invalid or unresolvable.

    Example: a requested profile name does not exist and no default fallback
    is available.
    """
