import os

import pytest

from parsing import ColumnResolutionError, parse_csv, resolve_columns

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_trials.csv")


def test_resolve_columns_auto_detects_common_names():
    header = ["subject", "condition", "block", "trial", "rt", "accuracy"]
    mapping = resolve_columns(header, {})
    assert mapping == {
        "subject": "subject",
        "condition": "condition",
        "block": "block",
        "trial": "trial",
        "rt": "rt",
        "accuracy": "accuracy",
    }


def test_resolve_columns_auto_detects_alternate_naming_convention():
    header = ["participant_id", "trial_type", "response_time", "correct"]
    mapping = resolve_columns(header, {})
    assert mapping["subject"] == "participant_id"
    assert mapping["condition"] == "trial_type"
    assert mapping["rt"] == "response_time"
    assert mapping["accuracy"] == "correct"


def test_resolve_columns_raises_clear_error_when_required_column_missing():
    header = ["subject", "condition"]  # no rt or accuracy column
    with pytest.raises(ColumnResolutionError) as exc_info:
        resolve_columns(header, {})
    message = str(exc_info.value)
    assert "rt" in message
    assert "accuracy" in message


def test_explicit_override_takes_precedence_over_autodetection():
    header = ["subj", "cond", "weird_col_name", "acc"]
    mapping = resolve_columns(header, {"rt": "weird_col_name"})
    assert mapping["rt"] == "weird_col_name"


def test_explicit_override_of_nonexistent_column_raises():
    header = ["subject", "condition", "rt", "accuracy"]
    with pytest.raises(ColumnResolutionError):
        resolve_columns(header, {"subject": "does_not_exist"})


def test_parse_csv_loads_all_trials_from_fixture():
    result = parse_csv(FIXTURE)
    assert len(result.trials) == 24
    subjects = {t.subject for t in result.trials}
    assert subjects == {"S1", "S2", "S3"}


def test_parse_csv_counts_malformed_cells_as_warnings():
    result = parse_csv(FIXTURE)
    # S3 has one blank RT cell and one non-numeric accuracy cell.
    assert result.warnings == 2


def test_parse_csv_coerces_malformed_rt_to_none_without_crashing():
    result = parse_csv(FIXTURE)
    blank_rt_trial = next(t for t in result.trials if t.subject == "S3" and t.trial_num == 3)
    assert blank_rt_trial.rt_ms is None
    assert blank_rt_trial.malformed_rt is True


def test_parse_csv_coerces_malformed_accuracy_to_none_without_crashing():
    result = parse_csv(FIXTURE)
    malformed_acc_trial = next(t for t in result.trials if t.subject == "S3" and t.trial_num == 4)
    assert malformed_acc_trial.correct is None
    assert malformed_acc_trial.malformed_accuracy is True


def test_parse_csv_raises_on_missing_file():
    with pytest.raises(FileNotFoundError):
        parse_csv("/nonexistent/path/does_not_exist.csv")


def test_parse_csv_empty_header_raises():
    import csv
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        path = f.name  # completely empty file -> no header

    try:
        with pytest.raises(ColumnResolutionError):
            parse_csv(path)
    finally:
        os.remove(path)
