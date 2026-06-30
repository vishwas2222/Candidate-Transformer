from config.config_loader import OutputConfig
from projection.serializer import CandidateSerializer
from validation.schema_validator import SchemaValidator
from validation.validation_report import ValidationReport


def test_valid_document_passes(sample_canonical_candidate):
    config = OutputConfig(include_fields=["full_name", "emails", "phones", "skills"])
    document = CandidateSerializer().serialize(sample_canonical_candidate, config)
    report = SchemaValidator().validate(document, config)
    assert report.is_valid
    assert report.errors == []


def test_missing_candidate_section_is_error():
    report = SchemaValidator().validate({"metadata": {}}, OutputConfig())
    assert not report.is_valid
    assert any(e.field == "candidate" for e in report.errors)


def test_non_dict_document_is_error():
    report = SchemaValidator().validate("not a dict", OutputConfig())
    assert not report.is_valid


def test_duplicate_emails_warns():
    document = {"candidate": {"emails": ["a@example.com", "a@example.com"]}}
    report = SchemaValidator().validate(document, OutputConfig())
    assert any("Duplicate email" in w.message for w in report.warnings)
    assert report.is_valid  # duplicates are warnings, not errors


def test_invalid_email_format_warns():
    document = {"candidate": {"emails": ["not-an-email"]}}
    report = SchemaValidator().validate(document, OutputConfig())
    assert any("valid email" in w.message for w in report.warnings)


def test_invalid_confidence_is_error():
    document = {"candidate": {"full_name": {"value": "Jane", "confidence": 1.5}}}
    report = SchemaValidator().validate(document, OutputConfig())
    assert not report.is_valid
    assert any("Confidence" in e.message for e in report.errors)


def test_unknown_field_warns():
    document = {"candidate": {"not_a_real_field": "x"}}
    report = SchemaValidator().validate(document, OutputConfig())
    assert any("Unknown field" in w.message for w in report.warnings)


def test_non_list_emails_is_error():
    document = {"candidate": {"emails": "not-a-list"}}
    report = SchemaValidator().validate(document, OutputConfig())
    assert not report.is_valid


def test_null_value_does_not_error():
    document = {"candidate": {"headline": None}}
    report = SchemaValidator().validate(document, OutputConfig())
    assert report.is_valid


def test_field_mapping_aware_validation():
    config = OutputConfig(field_mapping={"full_name": "candidate_name"})
    document = {"candidate": {"candidate_name": "Jane Doe"}}
    report = SchemaValidator().validate(document, config)
    # Should resolve candidate_name -> full_name and not flag it unknown
    assert not any("Unknown field" in w.message for w in report.warnings)


def test_invalid_date_format_warns_when_iso_required():
    config = OutputConfig(date_format="ISO")
    document = {"candidate": {"experience": [{"title": "X", "company": "Y", "start_date": "Jan 2020"}]}}
    report = SchemaValidator().validate(document, config)
    assert any("ISO" in w.message for w in report.warnings)


def test_validation_report_to_dict_structure():
    report = ValidationReport()
    report.add("ERROR", "email", "Invalid email")
    report.add("WARNING", "headline", "Headline missing")
    d = report.to_dict()
    assert d["is_valid"] is False
    assert d["errors"][0]["type"] == "ERROR"
    assert d["warnings"][0]["type"] == "WARNING"


def test_validation_report_summary():
    report = ValidationReport()
    report.add("WARNING", "x", "y")
    summary = report.summary()
    assert summary["warning_count"] == 1
    assert summary["error_count"] == 0
    assert summary["is_valid"] is True
