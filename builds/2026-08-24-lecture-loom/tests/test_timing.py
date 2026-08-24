import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from parser import Lecture, Section  # noqa: E402
from timing import (  # noqa: E402
    build_report,
    classify_budget,
    classify_objectives,
    estimate_minutes,
    find_dense_sections,
)


def make_section(heading: str, bullets, word_padding: int = 0) -> Section:
    section = Section(heading=heading, level=2, bullets=list(bullets))
    if word_padding:
        section.prose.append(" ".join(["pad"] * word_padding))
    return section


def test_estimate_minutes_basic_math():
    assert estimate_minutes(130, wpm=130) == pytest.approx(1.0)
    assert estimate_minutes(65, wpm=130) == pytest.approx(0.5)


def test_estimate_minutes_rejects_nonpositive_wpm():
    with pytest.raises(ValueError):
        estimate_minutes(100, wpm=0)
    with pytest.raises(ValueError):
        estimate_minutes(100, wpm=-5)


def test_classify_budget_on_target_inclusive_boundaries():
    assert classify_budget(45.0, target_minutes=50.0) == "on_target"
    assert classify_budget(55.0, target_minutes=50.0) == "on_target"
    assert classify_budget(50.0, target_minutes=50.0) == "on_target"


def test_classify_budget_just_outside_boundaries():
    assert classify_budget(44.99, target_minutes=50.0) == "under_budget"
    assert classify_budget(55.01, target_minutes=50.0) == "over_budget"


def test_classify_budget_rejects_nonpositive_target():
    with pytest.raises(ValueError):
        classify_budget(10.0, target_minutes=0)
    with pytest.raises(ValueError):
        classify_budget(10.0, target_minutes=-1)


def test_find_dense_sections_uniform_lecture_flags_nothing():
    sections = [make_section(f"S{i}", ["a", "b"]) for i in range(3)]
    assert find_dense_sections(sections) == []


def test_find_dense_sections_flags_true_outlier():
    sections = [
        make_section("Balanced A", ["a", "b"]),
        make_section("Balanced B", ["a", "b"]),
        make_section("Overloaded", ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]),
    ]
    assert find_dense_sections(sections) == ["Overloaded"]


def test_find_dense_sections_skips_when_fewer_than_two_sections():
    sections = [make_section("Only One", ["a", "b", "c", "d", "e", "f", "g", "h"])]
    assert find_dense_sections(sections) == []


def test_find_dense_sections_all_zero_bullets_flags_nothing():
    sections = [make_section("A", []), make_section("B", [])]
    assert find_dense_sections(sections) == []


def test_classify_objectives_missing():
    sections = [make_section("A", ["x"]), make_section("B", ["y"])]
    assert classify_objectives([], sections) == "missing"


def test_classify_objectives_sparse():
    sections = [make_section(f"S{i}", ["x"]) for i in range(5)]
    assert classify_objectives(["only one objective"], sections) == "sparse"


def test_classify_objectives_ok():
    sections = [make_section(f"S{i}", ["x"]) for i in range(5)]
    assert classify_objectives(["obj one", "obj two"], sections) == "ok"


def test_build_report_computes_total_and_worst_section():
    sections = [
        make_section("Short", ["one two three four five"]),
        make_section("Long", ["one two three four five six seven eight nine ten"]),
    ]
    lecture = Lecture(
        path="fake.md",
        title="Fake Lecture",
        objectives=["obj"],
        sections=sections,
        heading_skip_warning=False,
    )
    report = build_report(lecture, wpm=5.0, target_minutes=10.0)
    assert report.section_timings[0].estimated_minutes == pytest.approx(1.0)
    assert report.section_timings[1].estimated_minutes == pytest.approx(2.0)
    assert report.total_minutes == pytest.approx(3.0)
    assert report.worst_section == "Long"
    assert report.budget_status == "under_budget"


def test_build_report_worst_section_none_when_all_empty():
    sections = [make_section("Empty A", []), make_section("Empty B", [])]
    lecture = Lecture(
        path="fake.md", title="Empty", objectives=[], sections=sections, heading_skip_warning=False
    )
    report = build_report(lecture, wpm=130.0, target_minutes=10.0)
    assert report.worst_section is None
    assert report.objective_flag == "missing"
