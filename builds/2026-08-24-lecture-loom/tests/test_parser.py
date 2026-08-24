import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from parser import parse_lecture  # noqa: E402

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def test_title_extracted_from_h1():
    lecture = parse_lecture(FIXTURES / "well_formed_lecture.md")
    assert lecture.title == "Stress Physiology 101"


def test_title_falls_back_to_filename_when_no_h1(tmp_path):
    path = tmp_path / "my_cool_lecture.md"
    path.write_text("## Just a section\n- one bullet\n", encoding="utf-8")
    lecture = parse_lecture(path)
    assert lecture.title == "My Cool Lecture"


def test_sections_split_on_h2():
    lecture = parse_lecture(FIXTURES / "well_formed_lecture.md")
    headings = [s.heading for s in lecture.sections]
    assert headings == ["Introduction", "The HPA Axis", "Wrap-up"]


def test_bullets_extracted_per_section():
    lecture = parse_lecture(FIXTURES / "well_formed_lecture.md")
    hpa_section = next(s for s in lecture.sections if s.heading == "The HPA Axis")
    assert hpa_section.bullets == [
        "Hypothalamus releases CRH",
        "Pituitary releases ACTH",
        "Adrenal cortex releases cortisol",
    ]
    assert hpa_section.bullet_count == 3


def test_explicit_objectives_heading_extracted():
    lecture = parse_lecture(FIXTURES / "well_formed_lecture.md")
    assert lecture.objectives == [
        "Describe the HPA axis",
        "Explain cortisol's role in the stress response",
    ]


def test_no_objectives_detected_when_absent():
    lecture = parse_lecture(FIXTURES / "no_objectives_lecture.md")
    assert lecture.objectives == []


def test_by_the_end_pattern_extracted_without_explicit_heading():
    lecture = parse_lecture(FIXTURES / "overlong_lecture.md")
    assert len(lecture.objectives) == 1
    assert "students will" in lecture.objectives[0].lower()
    assert lecture.objectives[0].startswith("By the end of this lecture")


def test_heading_skip_detected():
    lecture = parse_lecture(FIXTURES / "heading_skip_lecture.md")
    assert lecture.heading_skip_warning is True


def test_no_heading_skip_on_well_formed_lecture():
    lecture = parse_lecture(FIXTURES / "well_formed_lecture.md")
    assert lecture.heading_skip_warning is False


def test_numbered_list_treated_as_bullets(tmp_path):
    path = tmp_path / "numbered.md"
    path.write_text("# Title\n\n## Section\n1. First point\n2. Second point\n", encoding="utf-8")
    lecture = parse_lecture(path)
    assert lecture.sections[0].bullets == ["First point", "Second point"]


def test_prose_paragraphs_captured(tmp_path):
    path = tmp_path / "prose.md"
    path.write_text(
        "# Title\n\n## Section\nThis is a plain prose paragraph with no bullet marker.\n",
        encoding="utf-8",
    )
    lecture = parse_lecture(path)
    assert lecture.sections[0].prose == [
        "This is a plain prose paragraph with no bullet marker."
    ]


def test_empty_lecture_produces_no_sections(tmp_path):
    path = tmp_path / "empty.md"
    path.write_text("# Just a Title\n", encoding="utf-8")
    lecture = parse_lecture(path)
    assert lecture.sections == []
    assert lecture.objectives == []
