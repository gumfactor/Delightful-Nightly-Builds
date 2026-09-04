import json
import re

from src import db, render


def _make_case(pmid, title, vignette, course="Stress and Coping"):
    return db.Case(
        pmid=pmid,
        course=course,
        topic_query="stress",
        title=title,
        journal="Journal of Testing",
        pub_year=2023,
        citation=f"{title}. PMID:{pmid}",
        abstract_text="abstract text",
        sample_size=40,
        population="undergraduate sample",
        methodology="survey",
        effect_size_text="r = 0.3",
        p_value_text="p < .05",
        vignette_text=vignette,
        vignette_source="deterministic",
        discussion_questions=["Q1?", "Q2?", "Q3?"],
        created_at="2026-09-04T08:00:00Z",
    )


def test_render_dashboard_includes_case_count():
    cases = [_make_case("1", "Title One", "Vignette one.")]
    html = render.render_dashboard(cases)
    assert '<span id="case-count">1</span>' in html


def test_render_dashboard_handles_empty_case_list():
    html = render.render_dashboard([])
    assert '<span id="case-count">0</span>' in html
    assert "CaseForge" in html


def test_render_dashboard_embeds_valid_json_payload():
    cases = [_make_case("1", "Title One", "Vignette one.")]
    html = render.render_dashboard(cases)
    match = re.search(
        r'<script id="case-data" type="application/json">(.*?)</script>', html, re.DOTALL
    )
    assert match is not None
    payload = json.loads(match.group(1))
    assert payload[0]["title"] == "Title One"
    assert payload[0]["pmid"] == "1"


def test_render_dashboard_lists_distinct_courses():
    cases = [
        _make_case("1", "Title One", "V1", course="Stress and Coping"),
        _make_case("2", "Title Two", "V2", course="Stress and Coping"),
        _make_case("3", "Title Three", "V3", course="Social Affective Neuroscience"),
    ]
    html = render.render_dashboard(cases)
    match = re.search(
        r'<script id="course-data" type="application/json">(.*?)</script>', html, re.DOTALL
    )
    courses = json.loads(match.group(1))
    assert sorted(courses) == ["Social Affective Neuroscience", "Stress and Coping"]


def test_render_dashboard_escapes_script_close_tag_in_title():
    malicious_title = "Innocuous</script><script>window.__xss=true;</script>"
    cases = [_make_case("1", malicious_title, "A vignette.")]
    html = render.render_dashboard(cases)

    # The raw payload script tag must never contain a literal "</script>"
    # sequence pulled from case data — only the build's own two intentional
    # closing script tags for case-data/course-data should exist verbatim.
    data_script_match = re.search(
        r'<script id="case-data" type="application/json">(.*?)</script>', html, re.DOTALL
    )
    assert data_script_match is not None
    raw_payload_text = data_script_match.group(1)
    assert "</script>" not in raw_payload_text
    assert "<\\/script>" in raw_payload_text

    # And parsing it back out must still recover the exact original string,
    # proving the escape is reversible and no content was corrupted.
    payload = json.loads(data_script_match.group(1))
    assert payload[0]["title"] == malicious_title

    # The malicious payload must never appear as a real executable script tag.
    assert "window.__xss=true;</script>" not in html.replace("<\\/script>", "")


def test_render_dashboard_escapes_img_onerror_in_vignette():
    malicious_vignette = '<img src=x onerror="window.__pwned=true">'
    cases = [_make_case("1", "Title", malicious_vignette)]
    html = render.render_dashboard(cases)
    # The raw HTML (outside the JSON-in-script payload) must never contain
    # an actual <img ...onerror=...> tag — only its JSON-escaped string form.
    outside_script = re.sub(
        r'<script id="case-data" type="application/json">.*?</script>', "", html, flags=re.DOTALL
    )
    assert "onerror=" not in outside_script


def test_render_dashboard_never_uses_innerhtml():
    cases = [_make_case("1", "Title", "Vignette.")]
    html = render.render_dashboard(cases)
    assert "innerHTML" not in html
