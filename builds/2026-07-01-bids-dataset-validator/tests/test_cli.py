"""Tests for the CLI entry point."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import run


def _touch(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")


def _make_valid_dataset(root: Path):
    (root / "dataset_description.json").write_text(
        '{"Name": "Test Study", "BIDSVersion": "1.9.0"}'
    )
    _touch(root / "sub-01/anat/sub-01_T1w.nii.gz")
    _touch(root / "sub-01/anat/sub-01_T1w.json")


def test_nonexistent_dataset_path_exits_cleanly(capsys):
    exit_code = run(["/nonexistent/path/does-not-exist"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error" in captured.err


def test_valid_dataset_exits_zero(tmp_path, capsys):
    _make_valid_dataset(tmp_path)
    exit_code = run([str(tmp_path)])
    assert exit_code == 0
    assert "No violations found." in capsys.readouterr().out


def test_dataset_with_errors_exits_one(tmp_path, capsys):
    # No dataset_description.json at all -> an error-level finding.
    _touch(tmp_path / "sub-01/anat/sub-01_T1w.nii.gz")
    exit_code = run([str(tmp_path)])
    assert exit_code == 1


def test_json_report_is_written_with_expected_structure(tmp_path):
    _make_valid_dataset(tmp_path)
    report_path = tmp_path / "report.json"
    run([str(tmp_path), "--json-report", str(report_path)])
    data = json.loads(report_path.read_text())
    assert "summary" in data and "findings" in data


def test_html_report_is_written(tmp_path):
    _make_valid_dataset(tmp_path)
    report_path = tmp_path / "report.html"
    run([str(tmp_path), "--html-report", str(report_path)])
    content = report_path.read_text()
    assert content.strip().startswith("<!DOCTYPE html>")


def test_apply_flag_renames_padding_mismatch_on_disk(tmp_path):
    _make_valid_dataset(tmp_path)
    _touch(tmp_path / "sub-2/anat/sub-2_T1w.nii.gz")

    run([str(tmp_path), "--apply"])

    assert not (tmp_path / "sub-2/anat/sub-2_T1w.nii.gz").exists()
    assert (tmp_path / "sub-2/anat/sub-02_T1w.nii.gz").exists()


def test_dry_run_default_does_not_rename(tmp_path):
    _make_valid_dataset(tmp_path)
    _touch(tmp_path / "sub-2/anat/sub-2_T1w.nii.gz")

    run([str(tmp_path)])

    assert (tmp_path / "sub-2/anat/sub-2_T1w.nii.gz").exists()
    assert not (tmp_path / "sub-2/anat/sub-02_T1w.nii.gz").exists()


def test_ai_summary_flag_without_api_key_does_not_crash(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _make_valid_dataset(tmp_path)
    exit_code = run([str(tmp_path), "--ai-summary"])
    assert exit_code == 0
