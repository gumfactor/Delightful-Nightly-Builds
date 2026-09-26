from classify import Commit
from render import ChangelogResult, render_html, render_markdown


def _commit(sha, subject, type_="feat"):
    return Commit(
        sha=sha, subject=subject, body="", author_date="2026-09-01",
        type=type_, scope=None, breaking=False, pr_number=None, source="keyword",
    )


def _result(sections, section_text, cancelled_pairs=None, bump="minor"):
    return ChangelogResult(
        range_label="v1.0.0..HEAD",
        total_commits=sum(len(v) for v in sections.values()),
        sections=sections,
        section_text=section_text,
        cancelled_pairs=cancelled_pairs or [],
        suggested_bump=bump,
    )


def test_markdown_includes_section_headers_and_bump():
    sections = {"Features": [_commit("aaa1111", "add widget")]}
    result = _result(sections, {"Features": "Added a widget."})
    md = render_markdown(result)
    assert "## Features" in md
    assert "Added a widget." in md
    assert "`minor`" in md


def test_markdown_omits_empty_sections():
    sections = {"Features": [_commit("aaa1111", "add widget")]}
    result = _result(sections, {"Features": "Added a widget."})
    md = render_markdown(result)
    assert "## Fixes" not in md
    assert "## Breaking Changes" not in md


def test_markdown_notes_cancelled_pairs():
    original = _commit("aaa1111", "feat: risky change")
    revert = _commit("bbb2222", 'Revert "feat: risky change"', type_="revert")
    sections = {"Features": [_commit("ccc3333", "add stable widget")]}
    result = _result(sections, {"Features": "text"}, cancelled_pairs=[(original, revert)])
    md = render_markdown(result)
    assert "Cancelled revert/re-revert pairs:** 1" in md


def test_markdown_no_changes_message():
    result = _result({}, {}, bump="none")
    md = render_markdown(result)
    assert "No changes in this range" in md


def test_html_is_self_contained_and_has_no_inner_html():
    sections = {"Features": [_commit("aaa1111", "add widget")]}
    result = _result(sections, {"Features": "Added a widget."})
    html = render_html(result)
    assert "<!doctype html>" in html
    assert "innerHTML" not in html
    assert "chart.js@4.4.4" in html


def test_html_escapes_script_tag_breakout_in_json_payload():
    # A section name/commit subject containing "</script>" must not break out of the <script> block.
    sections = {"Features": [_commit("aaa1111", "add </script><script>alert(1)</script> widget")]}
    result = _result(sections, {"Features": "text"})
    html = render_html(result)
    assert "</script><script>alert(1)" not in html


def test_html_escapes_hostile_commit_subject_in_body():
    sections = {"Features": [_commit("aaa1111", "<img src=x onerror=alert(1)>")]}
    result = _result(sections, {"Features": "text"})
    html = render_html(result)
    assert "<img src=x onerror=alert(1)>" not in html
    assert "&lt;img" in html
