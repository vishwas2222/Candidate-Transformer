import json
import os
import subprocess
import sys

import pytest

from config.config_loader import OutputConfig
from projection.output_formatter import OutputFormatter
from exporter.file_exporter import FileExporter


def test_output_formatter_pretty_print():
    doc = {"b": 1, "a": 2}
    config = OutputConfig(pretty_print=True)
    text = OutputFormatter.format(doc, config)
    assert text.startswith("{\n")
    assert '"a": 2' in text
    # Sorted keys: 'a' should come before 'b'
    assert text.index('"a"') < text.index('"b"')


def test_output_formatter_compact():
    doc = {"a": 1}
    config = OutputConfig(pretty_print=False)
    text = OutputFormatter.format(doc, config)
    assert "\n" not in text
    assert " " not in text


def test_output_formatter_handles_unicode():
    doc = {"name": "José Müller"}
    config = OutputConfig(pretty_print=True)
    text = OutputFormatter.format(doc, config)
    assert "José Müller" in text


def test_exporter_writes_candidate_json(tmp_path):
    exporter = FileExporter(base_dir=str(tmp_path))
    result = exporter.export_candidate('{"a": 1}', "output", "candidate.json")
    assert result.success
    out_file = tmp_path / "output" / "candidate.json"
    assert out_file.exists()
    assert json.loads(out_file.read_text()) == {"a": 1}


def test_exporter_creates_directories(tmp_path):
    exporter = FileExporter(base_dir=str(tmp_path))
    exporter.export_candidate('{}', "deeply/nested/output", "candidate.json")
    assert (tmp_path / "deeply" / "nested" / "output" / "candidate.json").exists()
    assert (tmp_path / "reports").exists()
    assert (tmp_path / "logs").exists()


def test_exporter_atomic_write_leaves_no_tmp_file(tmp_path):
    exporter = FileExporter(base_dir=str(tmp_path))
    exporter.export_candidate('{"a": 1}', "output", "candidate.json")
    tmp_file = tmp_path / "output" / "candidate.json.tmp"
    assert not tmp_file.exists()


def test_exporter_validation_report(tmp_path):
    exporter = FileExporter(base_dir=str(tmp_path))
    result = exporter.export_validation_report({"is_valid": True, "errors": [], "warnings": []}, "output")
    assert result.success
    out_file = tmp_path / "output" / "validation_report.json"
    assert out_file.exists()
    assert json.loads(out_file.read_text())["is_valid"] is True


def test_exporter_never_crashes_on_bad_path():
    # A base_dir under a path that doesn't (and won't) exist should be
    # handled gracefully, not raise.
    exporter = FileExporter(base_dir="/nonexistent_root_just_for_test")
    result = exporter.export_candidate("{}", "output", "candidate.json")
    # Either succeeds (dir got created) or fails gracefully with an error message
    assert result.success or result.error is not None


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.parametrize("config_name", ["default", "recruiter", "analytics", "minimal", "developer"])
def test_cli_runs_with_each_profile(config_name):
    """End-to-end smoke test: `python main.py --config <profile>` should exit 0
    and produce candidate.json + validation_report.json."""
    result = subprocess.run(
        [sys.executable, "main.py", "--config", config_name],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "Output Generated" in result.stdout
    candidate_path = os.path.join(PROJECT_ROOT, "output", "candidate.json")
    assert os.path.exists(candidate_path)
    with open(candidate_path) as f:
        data = json.load(f)
    assert "candidate" in data


def test_cli_defaults_to_default_profile_when_omitted():
    result = subprocess.run(
        [sys.executable, "main.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "Loading Config: default" in result.stdout


def test_cli_unknown_profile_falls_back_without_crashing():
    result = subprocess.run(
        [sys.executable, "main.py", "--config", "totally_unknown_profile"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "Output Generated" in result.stdout
