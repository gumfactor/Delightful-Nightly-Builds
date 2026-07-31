"""Tests for filename parsing and per-file/cross-file BIDS rules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bids_rules import (
    check_dataset_description,
    check_duplicates,
    check_events,
    check_session_consistency,
    check_sidecars,
    check_zero_padding,
    parse_filename,
)


def test_parses_valid_anat_filename():
    parsed, findings = parse_filename("sub-01/anat/sub-01_T1w.nii.gz")
    assert parsed.entities == {"sub": "01"}
    assert parsed.suffix == "T1w"
    assert parsed.extension == ".nii.gz"
    assert not any(f.severity == "error" for f in findings)


def test_parses_valid_bold_filename_with_all_core_entities():
    parsed, findings = parse_filename(
        "sub-01/func/sub-01_ses-1_task-nback_acq-fast_run-01_echo-1_bold.nii.gz"
    )
    assert parsed.entities == {
        "sub": "01",
        "ses": "1",
        "task": "nback",
        "acq": "fast",
        "run": "01",
        "echo": "1",
    }
    assert not any(f.severity == "error" for f in findings)


def test_missing_sub_entity_is_an_error():
    _, findings = parse_filename("task-rest_bold.nii.gz")
    codes = [f.code for f in findings]
    assert "MISSING_SUB_ENTITY" in codes


def test_malformed_entity_without_dash_is_an_error():
    _, findings = parse_filename("sub-01_badentity_T1w.nii.gz")
    codes = [f.code for f in findings]
    assert "MALFORMED_ENTITY" in codes


def test_out_of_order_entities_is_an_error():
    _, findings = parse_filename("sub-01_run-01_ses-1_bold.nii.gz")
    codes = [f.code for f in findings]
    assert "BAD_ENTITY_ORDER" in codes


def test_unrecognized_suffix_is_a_warning_not_error():
    _, findings = parse_filename("sub-01_weirdsuffix.nii.gz")
    warnings = [f for f in findings if f.code == "UNRECOGNIZED_SUFFIX"]
    assert len(warnings) == 1
    assert warnings[0].severity == "warning"


def test_path_traversal_in_entity_value_is_rejected():
    # Real scanned filenames can never contain "/" (the filesystem forbids
    # it), so the attack surface is a ".." *value* within one path segment.
    parsed, findings = parse_filename("sub-.._T1w.nii.gz")
    codes = [f.code for f in findings]
    assert "INVALID_ENTITY_VALUE" in codes
    # The rejected value must never make it into the parsed entities dict.
    assert ".." not in "".join(parsed.entities.values())


def test_missing_dataset_description_is_an_error(tmp_path):
    findings = check_dataset_description(tmp_path, existing_relpaths=set())
    assert findings[0].code == "MISSING_DATASET_DESCRIPTION"
    assert findings[0].severity == "error"


def test_dataset_description_missing_required_field(tmp_path):
    (tmp_path / "dataset_description.json").write_text('{"Name": "Study"}')
    findings = check_dataset_description(
        tmp_path, existing_relpaths={"dataset_description.json"}
    )
    codes = [f.code for f in findings]
    assert "MISSING_DATASET_DESCRIPTION_FIELD" in codes


def test_valid_dataset_description_produces_no_findings(tmp_path):
    (tmp_path / "dataset_description.json").write_text(
        '{"Name": "Study", "BIDSVersion": "1.9.0"}'
    )
    findings = check_dataset_description(
        tmp_path, existing_relpaths={"dataset_description.json"}
    )
    assert findings == []


def test_missing_sidecar_is_flagged():
    parsed, _ = parse_filename("sub-01/anat/sub-01_T1w.nii.gz")
    findings = check_sidecars([parsed], existing_relpaths={parsed.relpath})
    assert len(findings) == 1
    assert findings[0].code == "MISSING_SIDECAR"


def test_present_sidecar_is_not_flagged():
    parsed, _ = parse_filename("sub-01/anat/sub-01_T1w.nii.gz")
    existing = {parsed.relpath, "sub-01/anat/sub-01_T1w.json"}
    findings = check_sidecars([parsed], existing_relpaths=existing)
    assert findings == []


def test_missing_events_for_task_run_is_flagged():
    parsed, _ = parse_filename("sub-01/func/sub-01_task-nback_bold.nii.gz")
    findings = check_events([parsed], existing_relpaths={parsed.relpath})
    assert len(findings) == 1
    assert findings[0].code == "MISSING_EVENTS"


def test_resting_state_run_does_not_require_events():
    parsed, _ = parse_filename("sub-01/func/sub-01_task-rest_bold.nii.gz")
    findings = check_events([parsed], existing_relpaths={parsed.relpath})
    assert findings == []


def test_inconsistent_zero_padding_is_flagged():
    files = [
        parse_filename("sub-1/anat/sub-1_T1w.nii.gz")[0],
        parse_filename("sub-02/anat/sub-02_T1w.nii.gz")[0],
        parse_filename("sub-03/anat/sub-03_T1w.nii.gz")[0],
    ]
    findings = check_zero_padding(files)
    assert len(findings) == 1
    assert findings[0].code == "INCONSISTENT_PADDING"
    assert findings[0].path == "sub-1/anat/sub-1_T1w.nii.gz"


def test_consistent_padding_produces_no_findings():
    files = [
        parse_filename("sub-01/anat/sub-01_T1w.nii.gz")[0],
        parse_filename("sub-02/anat/sub-02_T1w.nii.gz")[0],
    ]
    assert check_zero_padding(files) == []


def test_duplicate_entity_set_is_flagged():
    files = [
        parse_filename("sub-01/anat/sub-01_T1w.nii.gz")[0],
        parse_filename("sub-01/extra/sub-01_T1w.nii.gz")[0],
    ]
    findings = check_duplicates(files)
    assert len(findings) == 1
    assert findings[0].code == "DUPLICATE_FILE"


def test_no_duplicates_for_distinct_files():
    files = [
        parse_filename("sub-01/anat/sub-01_T1w.nii.gz")[0],
        parse_filename("sub-01/anat/sub-01_T2w.nii.gz")[0],
    ]
    assert check_duplicates(files) == []


def test_inconsistent_session_structure_is_flagged():
    files = [
        parse_filename("sub-01/ses-1/anat/sub-01_ses-1_T1w.nii.gz")[0],
        parse_filename("sub-02/anat/sub-02_T1w.nii.gz")[0],
    ]
    findings = check_session_consistency(files)
    codes = [f.code for f in findings]
    assert "INCONSISTENT_SESSION_STRUCTURE" in codes


def test_all_subjects_with_sessions_is_consistent():
    files = [
        parse_filename("sub-01/ses-1/anat/sub-01_ses-1_T1w.nii.gz")[0],
        parse_filename("sub-02/ses-1/anat/sub-02_ses-1_T1w.nii.gz")[0],
    ]
    assert check_session_consistency(files) == []
