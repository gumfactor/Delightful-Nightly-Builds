import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from formatter import build_handout_md, build_outline_md  # noqa: E402
from parser import parse_lecture  # noqa: E402
from timing import build_report  # noqa: E402

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_over_budget_flag_matches_hand_computed_value(tmp_path):
    path = tmp_path / "overrun.md"
    path.write_text(
        "# Overrun Lecture\n\n## Section One\n- one two three four five six seven eight nine ten\n",
        encoding="utf-8",
    )
    lecture = parse_lecture(path)
    # 10 words at 10 wpm = exactly 1.0 minute, hand-computed.
    report = build_report(lecture, wpm=10.0, target_minutes=0.5)
    assert report.total_minutes == pytest.approx(1.0)
    assert report.budget_status == "over_budget"
    assert report.worst_section == "Section One"


def test_under_budget_flag_on_short_lecture(tmp_path):
    path = tmp_path / "short.md"
    path.write_text("# Short\n\n## Only Section\n- five six seven eight nine\n", encoding="utf-8")
    lecture = parse_lecture(path)
    report = build_report(lecture, wpm=5.0, target_minutes=100.0)
    assert report.budget_status == "under_budget"


def test_well_formed_fixture_has_ok_objective_flag():
    lecture = parse_lecture(FIXTURES / "well_formed_lecture.md")
    report = build_report(lecture, wpm=130.0, target_minutes=50.0)
    assert report.objective_flag == "ok"


def test_no_objectives_fixture_flags_missing():
    lecture = parse_lecture(FIXTURES / "no_objectives_lecture.md")
    report = build_report(lecture, wpm=130.0, target_minutes=50.0)
    assert report.objective_flag == "missing"


def test_dense_section_detected_from_real_parsed_file(tmp_path):
    path = tmp_path / "dense.md"
    path.write_text(
        "# Dense Lecture\n\n"
        "## Balanced A\n- one\n- two\n"
        "## Balanced B\n- one\n- two\n"
        "## Overloaded\n"
        + "".join(f"- point {i}\n" for i in range(10))
        + "",
        encoding="utf-8",
    )
    lecture = parse_lecture(path)
    report = build_report(lecture, wpm=130.0, target_minutes=50.0)
    assert report.dense_sections == ["Overloaded"]


def test_heading_skip_warning_propagates_into_report():
    lecture = parse_lecture(FIXTURES / "heading_skip_lecture.md")
    report = build_report(lecture, wpm=130.0, target_minutes=50.0)
    assert report.heading_skip_warning is True


def test_outline_md_includes_timing_and_flags(tmp_path):
    path = tmp_path / "overrun.md"
    path.write_text(
        "# Overrun Lecture\n\n## Section One\n- one two three four five six seven eight nine ten\n",
        encoding="utf-8",
    )
    lecture = parse_lecture(path)
    report = build_report(lecture, wpm=10.0, target_minutes=0.5)
    outline = build_outline_md(lecture, report)
    assert "Status: Over budget" in outline
    assert "Longest section: Section One" in outline
    assert "~1.0 min" in outline


def test_outline_md_flags_missing_objectives():
    lecture = parse_lecture(FIXTURES / "no_objectives_lecture.md")
    report = build_report(lecture, wpm=130.0, target_minutes=50.0)
    outline = build_outline_md(lecture, report)
    assert "none detected" in outline


def test_handout_md_omits_timing_annotations():
    lecture = parse_lecture(FIXTURES / "well_formed_lecture.md")
    handout = build_handout_md(lecture)
    assert not any("~" in line and "min" in line for line in handout.splitlines())
    assert "The HPA Axis" in handout
