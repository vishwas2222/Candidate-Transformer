import pytest
import os
from parsers.csv_parser import CSVParser
from parsers.base_parser import (
    ParserFileNotFoundError,
    ParserEmptyFileError,
    ParserInvalidFormatError,
)

def test_normal_csv(tmp_path):
    """Test parsing a valid recruiter CSV file."""
    csv_file = tmp_path / "recruiter.csv"
    csv_file.write_text("Name,Email,Phone,Company,Title\nJohn Doe,john@gmail.com,9876543210,Google,SDE\n")
    
    parser = CSVParser(str(csv_file))
    data = parser.parse()
    
    assert data["full_name"] == "John Doe"
    assert data["emails"] == ["john@gmail.com"]
    assert data["phones"] == ["9876543210"]
    assert data["current_company"] == "Google"
    assert data["title"] == "SDE"
    assert data["source"] == "recruiter.csv"

def test_missing_csv():
    """Test that ParserFileNotFoundError is raised for a non-existent file."""
    parser = CSVParser("does_not_exist.csv")
    with pytest.raises(ParserFileNotFoundError):
        parser.parse()

def test_empty_csv(tmp_path):
    """Test that ParserEmptyFileError is raised for an empty (0 bytes) CSV."""
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("")
    
    parser = CSVParser(str(csv_file))
    with pytest.raises(ParserEmptyFileError):
        parser.parse()

def test_csv_no_data_rows(tmp_path):
    """Test that ParserEmptyFileError is raised if the CSV has columns but no data rows."""
    csv_file = tmp_path / "no_data.csv"
    csv_file.write_text("Name,Email,Phone,Company,Title\n")
    
    parser = CSVParser(str(csv_file))
    with pytest.raises(ParserEmptyFileError):
        parser.parse()

def test_malformed_csv_missing_columns(tmp_path):
    """Test that ParserInvalidFormatError is raised if required columns are missing."""
    csv_file = tmp_path / "bad_cols.csv"
    csv_file.write_text("Name,Email,Phone\nJohn Doe,john@gmail.com,9876543210\n")
    
    parser = CSVParser(str(csv_file))
    with pytest.raises(ParserInvalidFormatError):
        parser.parse()
