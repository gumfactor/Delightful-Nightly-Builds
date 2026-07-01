"""Tests for the full scan + validation pipeline."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scanner import validate_dataset


def _touch(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")


def _make_valid_dataset(root: Path):
    (root / "dataset_description.json").write_text(
        '{"Name": "Test Study", "BIDSVersion": "1.9.0"}'
    )
    _touch(root / "sub-01/anat/sub-01_T1w.nii.gz")
    _touch(root / "sub-01/anat/sub-01_T1w.json")
    _touch(root / "sub-01/func/sub-01_task-rest_bold.nii.gz")
    _touch(root / "sub-01/func/sub-01_task-rest_bold.json")
    _touch(root / "sub-02/anat/sub-02_T1w.nii.gz")
    _touch(root / "sub-02/anat/sub-02_T1w.json")
    _touch(root / "sub-02/func/sub-02_task-rest_bold.nii.gz")
    _touch(root / "sub-02/func/sub-02_task-rest_bold.json")


def test_fully_valid_dataset_has_zero_errors(tmp_path):
    _make_valid_dataset(tmp_path)
    result = validate_dataset(tmp_path)
    errors = [f for f in result.findings if f.severity == "error"]
    assert errors == []


def test_dataset_with_planted_violations_flags_all_of_them(tmp_path):
    # Valid baseline plus five deliberately planted violations.
    _make_valid_dataset(tmp_path)

    # 1. Missing sidecar
    _touch(tmp_path / "sub-01/anat/sub-01_T2w.nii.gz")

    # 2. Missing dataset_description.json field — overwrite the valid one
    (tmp_path / "dataset_description.json").write_text('{"Name": "Test Study"}')

    # 3. Inconsistent zero-padding (sub-3 vs sub-01/sub-02)
    _touch(tmp_path / "sub-3/anat/sub-3_T1w.nii.gz")
    _touch(tmp_path / "sub-3/anat/sub-3_T1w.json")

    # 4. Duplicate file (same entities/suffix, different directory)
    _touch(tmp_path / "sub-01/extra/sub-01_T1w.nii.gz")

    # 5. Missing events.tsv for a non-rest task run
    _touch(tmp_path / "sub-01/func/sub-01_task-nback_bold.nii.gz")
    _touch(tmp_path / "sub-01/func/sub-01_task-nback_bold.json")

    result = validate_dataset(tmp_path)
    codes = {f.code for f in result.findings}

    assert "MISSING_SIDECAR" in codes
    assert "MISSING_DATASET_DESCRIPTION_FIELD" in codes
    assert "INCONSISTENT_PADDING" in codes
    assert "DUPLICATE_FILE" in codes
    assert "MISSING_EVENTS" in codes


def test_nonexistent_dataset_path_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        validate_dataset(tmp_path / "does-not-exist")


def test_dataset_path_that_is_a_file_raises_not_a_directory(tmp_path):
    f = tmp_path / "not_a_dir.txt"
    f.write_text("x")
    with pytest.raises(NotADirectoryError):
        validate_dataset(f)


def test_empty_directory_does_not_crash(tmp_path):
    result = validate_dataset(tmp_path)
    assert result.files == []
    assert any(f.code == "MISSING_DATASET_DESCRIPTION" for f in result.findings)


def test_hidden_files_are_ignored(tmp_path):
    _make_valid_dataset(tmp_path)
    _touch(tmp_path / ".DS_Store")
    result = validate_dataset(tmp_path)
    assert all(".DS_Store" not in f.relpath for f in result.files)
