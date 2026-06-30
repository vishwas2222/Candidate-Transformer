import json
import pytest
from config.config_loader import ConfigLoader, OutputConfig


def test_load_default_profile():
    loader = ConfigLoader()
    config, issues = loader.load("default")
    assert isinstance(config, OutputConfig)
    assert config.profile == "default"
    assert "full_name" in config.include_fields
    assert not any(i.severity == "ERROR" for i in issues)


def test_load_all_builtin_profiles():
    loader = ConfigLoader()
    for profile in ["default", "minimal", "recruiter", "analytics", "developer"]:
        config, issues = loader.load(profile)
        assert config.profile == profile
        assert not any(i.severity == "ERROR" for i in issues)


def test_missing_config_falls_back_gracefully():
    loader = ConfigLoader()
    config, issues = loader.load("does_not_exist_profile")
    assert isinstance(config, OutputConfig)
    assert any(i.severity == "ERROR" for i in issues)


def test_malformed_json_falls_back_gracefully(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json")
    loader = ConfigLoader()
    config, issues = loader.load(str(bad_file))
    assert isinstance(config, OutputConfig)
    assert any(i.severity == "ERROR" and "Malformed JSON" in i.message for i in issues)


def test_unknown_config_key_is_warning(tmp_path):
    cfg_file = tmp_path / "custom.json"
    cfg_file.write_text(json.dumps({"profile": "custom", "totally_unknown_key": True}))
    loader = ConfigLoader()
    config, issues = loader.load(str(cfg_file))
    assert any(i.severity == "WARNING" and "totally_unknown_key" in i.message for i in issues)


def test_duplicate_include_fields_warns(tmp_path):
    cfg_file = tmp_path / "dup.json"
    cfg_file.write_text(json.dumps({"include_fields": ["full_name", "full_name"]}))
    loader = ConfigLoader()
    config, issues = loader.load(str(cfg_file))
    assert any("Duplicate entry" in i.message for i in issues)


def test_invalid_empty_field_policy_is_error(tmp_path):
    cfg_file = tmp_path / "bad_policy.json"
    cfg_file.write_text(json.dumps({"empty_field_policy": "delete_everything"}))
    loader = ConfigLoader()
    config, issues = loader.load(str(cfg_file))
    assert any(i.severity == "ERROR" and "empty_field_policy" in i.message for i in issues)
    # Falls back to a valid default rather than crashing or using the bad value
    assert config.empty_field_policy in ("keep", "remove", "null")


def test_field_mapping_duplicate_targets_is_error(tmp_path):
    cfg_file = tmp_path / "dup_map.json"
    cfg_file.write_text(json.dumps({
        "field_mapping": {"full_name": "name", "title": "name"}
    }))
    loader = ConfigLoader()
    config, issues = loader.load(str(cfg_file))
    assert any(i.severity == "ERROR" and "unique" in i.message for i in issues)


def test_malformed_field_type_falls_back(tmp_path):
    cfg_file = tmp_path / "bad_types.json"
    cfg_file.write_text(json.dumps({"include_confidence": "yes", "pretty_print": "no"}))
    loader = ConfigLoader()
    config, issues = loader.load(str(cfg_file))
    assert isinstance(config.include_confidence, bool)
    assert isinstance(config.pretty_print, bool)
    assert any(i.severity == "ERROR" for i in issues)
