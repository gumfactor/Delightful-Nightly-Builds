"""Tests for the safe --apply zero-padding fixer."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bids_rules import parse_filename
from src.fixer import apply_fixes, compute_padding_fixes


def _touch(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")


def test_compute_padding_fixes_targets_minority_width_files():
    files = [
        parse_filename("sub-1/anat/sub-1_T1w.nii.gz")[0],
        parse_filename("sub-02/anat/sub-02_T1w.nii.gz")[0],
        parse_filename("sub-03/anat/sub-03_T1w.nii.gz")[0],
    ]
    plans = compute_padding_fixes(files)
    assert len(plans) == 1
    assert plans[0].old_relpath == "sub-1/anat/sub-1_T1w.nii.gz"
    assert plans[0].new_relpath == "sub-1/anat/sub-01_T1w.nii.gz"


def test_compute_padding_fixes_no_plans_when_consistent():
    files = [
        parse_filename("sub-01/anat/sub-01_T1w.nii.gz")[0],
        parse_filename("sub-02/anat/sub-02_T1w.nii.gz")[0],
    ]
    assert compute_padding_fixes(files) == []


def test_dry_run_never_touches_the_filesystem(tmp_path):
    _touch(tmp_path / "sub-1/anat/sub-1_T1w.nii.gz")
    files = [
        parse_filename("sub-1/anat/sub-1_T1w.nii.gz")[0],
        parse_filename("sub-02/anat/sub-02_T1w.nii.gz")[0],
    ]
    _touch(tmp_path / "sub-02/anat/sub-02_T1w.nii.gz")
    plans = compute_padding_fixes(files)

    results = apply_fixes(plans, tmp_path, dry_run=True)

    assert results[0].status == "planned"
    assert (tmp_path / "sub-1/anat/sub-1_T1w.nii.gz").exists()
    assert not (tmp_path / "sub-1/anat/sub-01_T1w.nii.gz").exists()


def test_apply_renames_file_on_disk(tmp_path):
    _touch(tmp_path / "sub-1/anat/sub-1_T1w.nii.gz")
    _touch(tmp_path / "sub-02/anat/sub-02_T1w.nii.gz")
    files = [
        parse_filename("sub-1/anat/sub-1_T1w.nii.gz")[0],
        parse_filename("sub-02/anat/sub-02_T1w.nii.gz")[0],
    ]
    plans = compute_padding_fixes(files)

    results = apply_fixes(plans, tmp_path, dry_run=False)

    assert results[0].status == "applied"
    assert not (tmp_path / "sub-1/anat/sub-1_T1w.nii.gz").exists()
    assert (tmp_path / "sub-1/anat/sub-01_T1w.nii.gz").exists()


def test_apply_refuses_to_overwrite_existing_target(tmp_path):
    _touch(tmp_path / "sub-1/anat/sub-1_T1w.nii.gz")
    _touch(tmp_path / "sub-1/anat/sub-01_T1w.nii.gz")  # target already exists
    _touch(tmp_path / "sub-02/anat/sub-02_T1w.nii.gz")
    files = [
        parse_filename("sub-1/anat/sub-1_T1w.nii.gz")[0],
        parse_filename("sub-1/anat/sub-01_T1w.nii.gz")[0],
        parse_filename("sub-02/anat/sub-02_T1w.nii.gz")[0],
    ]
    plans = [p for p in compute_padding_fixes(files) if p.old_relpath.endswith("sub-1_T1w.nii.gz")]

    results = apply_fixes(plans, tmp_path, dry_run=False)

    assert results[0].status == "skipped_exists"
    # Both files must still exist, untouched.
    assert (tmp_path / "sub-1/anat/sub-1_T1w.nii.gz").exists()
    assert (tmp_path / "sub-1/anat/sub-01_T1w.nii.gz").exists()
