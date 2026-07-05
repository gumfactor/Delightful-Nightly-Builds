import csv
import os
import tempfile

from parsing import Trial, parse_csv
from qc import QCConfig, flag_trials, learning_curve, recommend_exclusions, summarize_conditions, summarize_subjects
from report import esc, render_report, write_cleaned_csv, write_exclusions_csv

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_trials.csv")


def build_pipeline(config=None):
    config = config or QCConfig()
    parse_result = parse_csv(FIXTURE)
    trial_flags = flag_trials(parse_result.trials, config)
    subjects = summarize_subjects(parse_result.trials, trial_flags, config)
    conditions = summarize_conditions(parse_result.trials)
    excluded = recommend_exclusions(subjects, config)
    curves = learning_curve(parse_result.trials)
    return parse_result, trial_flags, subjects, conditions, excluded, curves, config


def test_esc_escapes_html_special_characters():
    assert esc("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"


def test_render_report_includes_subject_and_condition_counts():
    parse_result, trial_flags, subjects, conditions, excluded, curves, config = build_pipeline()
    html_out = render_report(
        subjects, conditions, parse_result.trials, excluded, "Test methods paragraph.", "template",
        config, curves, parse_result.warnings,
    )
    assert f"{len(subjects)} subjects" in html_out
    assert f"{len(conditions)} conditions" in html_out
    assert "Test methods paragraph." in html_out


def test_render_report_reflects_malformed_cell_warning_count():
    parse_result, trial_flags, subjects, conditions, excluded, curves, config = build_pipeline()
    html_out = render_report(
        subjects, conditions, parse_result.trials, excluded, "para", "template", config, curves,
        parse_result.warnings,
    )
    assert f"{parse_result.warnings} malformed cell(s)" in html_out


def test_render_report_has_no_external_network_references():
    parse_result, trial_flags, subjects, conditions, excluded, curves, config = build_pipeline()
    html_out = render_report(
        subjects, conditions, parse_result.trials, excluded, "para", "template", config, curves,
        parse_result.warnings,
    )
    assert "http://" not in html_out
    assert "https://" not in html_out
    assert "fetch(" not in html_out
    assert "XMLHttpRequest" not in html_out


def test_render_report_escapes_malicious_subject_id():
    trials = [Trial(subject="<img src=x onerror=alert(1)>", condition="A", rt_ms=400.0, correct=True, block=1, trial_num=1)]
    config = QCConfig()
    flags = flag_trials(trials, config)
    subjects = summarize_subjects(trials, flags, config)
    conditions = summarize_conditions(trials)
    curves = learning_curve(trials)
    html_out = render_report(subjects, conditions, trials, [], "para", "template", config, curves, 0)
    assert "<img src=x onerror=alert(1)>" not in html_out
    assert "&lt;img" in html_out


def test_render_report_handles_zero_subjects_without_crashing():
    html_out = render_report([], [], [], [], "No data.", "template", QCConfig(), {}, 0)
    assert "0 subjects" in html_out
    assert "No trial data found" in html_out


def test_write_cleaned_csv_includes_qc_flag_column():
    parse_result, trial_flags, *_ = build_pipeline()
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "cleaned.csv")
        write_cleaned_csv(out_path, parse_result.trials, trial_flags)
        with open(out_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert "QC_Flag" in rows[0]
        assert len(rows) == len(parse_result.trials)


def test_write_exclusions_csv_lists_reasons():
    config = QCConfig(expected_trials=10, min_completion=0.8, exclude_threshold=1)
    parse_result, trial_flags, subjects, conditions, excluded, curves, _ = build_pipeline(config)
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "exclusions.csv")
        write_exclusions_csv(out_path, excluded)
        with open(out_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == len(excluded)
        if rows:
            assert rows[0]["reasons"]
