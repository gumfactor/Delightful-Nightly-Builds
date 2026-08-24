import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from parser import Lecture, Section  # noqa: E402
from render import build_dashboard_html  # noqa: E402
from timing import build_report  # noqa: E402


def make_lecture(title: str) -> Lecture:
    section = Section(heading="Intro", level=2, bullets=["one two three"])
    return Lecture(path=f"{title}.md", title=title, objectives=["obj"], sections=[section], heading_skip_warning=False)


def test_dashboard_renders_valid_html_shell():
    lecture = make_lecture("Normal Lecture")
    report = build_report(lecture, wpm=130.0, target_minutes=50.0)
    html = build_dashboard_html([(lecture, report)])
    assert html.startswith("<!doctype html>")
    assert "Lecture Loom" in html
    assert '"title": "Normal Lecture"' in html  # delivered as JSON data, not raw HTML markup


def test_dashboard_handles_empty_batch():
    html = build_dashboard_html([])
    assert "<!doctype html>" in html
    assert '"loom-data">[]' in html


def test_xss_payload_in_title_never_breaks_out_of_script_tag():
    malicious_title = "</script><script>window.__xss = true;</script>"
    lecture = make_lecture(malicious_title)
    report = build_report(lecture, wpm=130.0, target_minutes=50.0)
    html = build_dashboard_html([(lecture, report)])

    # The literal, unescaped closing sequence must never appear — otherwise a
    # browser's HTML parser would terminate the JSON <script> tag's raw-text
    # content early and start parsing the rest of the payload as markup. A
    # bare "<script>" with no preceding slash is harmless here: while inside
    # a <script> element's raw-text mode, browsers only look for the "</script"
    # end-tag sequence, so an un-slashed "<script>" in the data is inert text.
    assert "</script><script>window.__xss" not in html
    # Escaped form is present instead.
    assert "<\\/script>" in html
    # Only the two "</script" end-tag sequences this build itself authors
    # (closing the JSON data block and the JS logic block) exist.
    assert html.count("</script") == 2


def test_xss_payload_in_bullet_also_escaped():
    section = Section(heading="Intro", level=2, bullets=['<img src=x onerror="window.__xss2=true">'])
    lecture = Lecture(path="x.md", title="X", objectives=[], sections=[section], heading_skip_warning=False)
    report = build_report(lecture, wpm=130.0, target_minutes=50.0)
    html = build_dashboard_html([(lecture, report)])
    assert "<script" in html
    assert html.count("<script") == 2


def test_dashboard_includes_objective_and_dense_flags_in_payload():
    section_a = Section(heading="A", level=2, bullets=["x"])
    section_c = Section(heading="C", level=2, bullets=["x"])
    section_b = Section(heading="B", level=2, bullets=["x", "x", "x", "x", "x", "x", "x", "x", "x", "x"])
    lecture = Lecture(
        path="x.md", title="X", objectives=[], sections=[section_a, section_c, section_b], heading_skip_warning=False
    )
    report = build_report(lecture, wpm=130.0, target_minutes=50.0)
    html = build_dashboard_html([(lecture, report)])
    assert '"objectiveFlag": "missing"' in html
    assert '"denseSections": ["B"]' in html
