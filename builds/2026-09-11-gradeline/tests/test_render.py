import json

from src.render import build_payload, render


def make_submission(identifier, criteria, compliance_ok=True):
    return {
        "identifier": identifier,
        "word_count": 300,
        "citation_count": 3,
        "flesch_score": 55.0,
        "compliance": {
            "word_count_ok": compliance_ok,
            "sections_ok": compliance_ok,
            "citations_ok": compliance_ok,
            "sections_found": {"Introduction": True},
        },
        "criteria": criteria,
    }


def test_build_payload_computes_criterion_averages():
    submissions = [
        make_submission("alice", [{"id": "c1", "name": "Thesis", "score": 8.0, "max_points": 10, "manual_only": False}]),
        make_submission("bob", [{"id": "c1", "name": "Thesis", "score": 6.0, "max_points": 10, "manual_only": False}]),
    ]
    payload = build_payload({}, submissions, [])
    assert payload["criterion_averages"] == [{"name": "Thesis", "avg_score": 7.0, "max_points": 10}]


def test_build_payload_excludes_manual_only_from_averages():
    submissions = [
        make_submission(
            "alice",
            [{"id": "m1", "name": "Argument Quality", "score": None, "max_points": 20, "manual_only": True}],
        )
    ]
    payload = build_payload({}, submissions, [])
    assert payload["criterion_averages"] == []


def test_build_payload_includes_similarity_pairs():
    submissions = [make_submission("alice", []), make_submission("bob", [])]
    pairs = [{"a": "alice", "b": "bob", "score": 0.91}]
    payload = build_payload({}, submissions, pairs)
    assert payload["similarity_pairs"] == pairs


def test_render_escapes_script_tag_sequences_in_identifier():
    malicious_identifier = "</script><script>window.__xss=true;</script>"
    batch = {"rubric_name": "Test Rubric", "source_path": "/x", "graded_at": "now"}
    submissions = [make_submission(malicious_identifier, [])]
    html = render(batch, submissions, [])
    assert "</script><script>window.__xss" not in html
    assert "<\\/script><script>window.__xss" in html


def test_render_html_escapes_rubric_name_in_title():
    batch = {"rubric_name": "<script>alert(1)</script>", "source_path": "/x", "graded_at": "now"}
    html = render(batch, [], [])
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "<script>alert(1)</script>" not in html


def test_render_handles_empty_similarity_pairs():
    batch = {"rubric_name": "Rubric", "source_path": "/x", "graded_at": "now"}
    html = render(batch, [make_submission("alice", [])], [])
    payload_start = html.index('id="report-data">') + len('id="report-data">')
    payload_end = html.index("</script>", payload_start)
    payload = json.loads(html[payload_start:payload_end])
    assert payload["similarity_pairs"] == []


def test_render_payload_is_valid_json_after_unescaping():
    batch = {"rubric_name": "Rubric", "source_path": "/x", "graded_at": "now"}
    submissions = [make_submission("alice", [{"id": "c1", "name": "Thesis", "score": 5.0, "max_points": 10, "manual_only": False}])]
    html = render(batch, submissions, [])
    payload_start = html.index('id="report-data">') + len('id="report-data">')
    payload_end = html.index("</script>", payload_start)
    raw = html[payload_start:payload_end]
    payload = json.loads(raw.replace("<\\/", "</"))
    assert payload["submissions"][0]["identifier"] == "alice"


def test_render_produces_a_complete_html_document():
    batch = {"rubric_name": "Rubric", "source_path": "/x", "graded_at": "now"}
    html = render(batch, [], [])
    assert html.strip().startswith("<!DOCTYPE html>")
    assert "</html>" in html
