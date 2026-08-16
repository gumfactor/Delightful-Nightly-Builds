import json
import re

from src import report


def _sample_payload(course_name="Stress and Coping", concept_name="HPA Axis"):
    return {
        "generated_at": "2026-08-16T00:00:00Z",
        "courses": [{
            "name": course_name,
            "terms": [{
                "term": "Fall 2026",
                "documents": [{"source_path": "w3.md"}],
                "concepts": [{"display_name": concept_name, "source": "marker", "note": ""}],
                "objectives": [{
                    "objective_text": "explain the HPA axis",
                    "best_concept": concept_name,
                    "best_score": 0.5,
                    "flagged": False,
                }],
            }],
        }],
        "overlap": [{
            "normalized_name": "hpa axi",
            "display_name": concept_name,
            "course_count": 2,
            "locations": [
                {"course_name": course_name, "term": "Fall 2026", "source_path": "w3.md"},
            ],
        }],
    }


def test_render_dashboard_writes_a_nonempty_file(tmp_path):
    out = tmp_path / "report.html"
    report.render_dashboard(_sample_payload(), str(out))
    assert out.exists()
    assert out.stat().st_size > 0


def _extract_embedded_json(html_text):
    m = re.search(
        r'<script type="application/json" id="atlas-data">(.*?)</script>',
        html_text,
        re.DOTALL,
    )
    assert m, "could not find embedded JSON payload in rendered HTML"
    return m.group(1)


def test_embedded_json_round_trips_through_json_loads(tmp_path):
    out = tmp_path / "report.html"
    payload = _sample_payload()
    report.render_dashboard(payload, str(out))
    html_text = out.read_text(encoding="utf-8")
    raw_json = _extract_embedded_json(html_text)
    parsed = json.loads(raw_json)
    assert parsed["courses"][0]["name"] == "Stress and Coping"


def test_script_injection_payload_in_course_name_is_inert():
    payload = _sample_payload(course_name="</script><script>alert(1)</script>")
    import tempfile, os
    fd, path = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    try:
        report.render_dashboard(payload, path)
        html_text = open(path, encoding="utf-8").read()
        # The literal closing-script sequence must never appear unescaped inside
        # the data script tag; it must be escaped to <\/script instead.
        raw_json = _extract_embedded_json(html_text)
        assert "</script>" not in raw_json
        parsed = json.loads(raw_json)
        assert parsed["courses"][0]["name"] == "</script><script>alert(1)</script>"
    finally:
        os.remove(path)


def test_img_onerror_payload_in_concept_name_is_inert():
    payload = _sample_payload(concept_name='<img src=x onerror="alert(1)">')
    import tempfile, os
    fd, path = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    try:
        report.render_dashboard(payload, path)
        html_text = open(path, encoding="utf-8").read()
        raw_json = _extract_embedded_json(html_text)
        parsed = json.loads(raw_json)
        assert parsed["courses"][0]["terms"][0]["concepts"][0]["display_name"] == (
            '<img src=x onerror="alert(1)">'
        )
        # The DOM-building JS only ever uses textContent/createElement — confirm
        # the template never uses innerHTML anywhere it would receive this data.
        assert "innerHTML" not in html_text
    finally:
        os.remove(path)


def test_safe_json_for_script_escapes_closing_script_tag():
    raw = report._safe_json_for_script({"x": "</script><script>evil()</script>"})
    assert "</script>" not in raw
    assert json.loads(raw) == {"x": "</script><script>evil()</script>"}


def test_render_dashboard_embeds_generated_at_in_header():
    import tempfile, os
    fd, path = tempfile.mkstemp(suffix=".html")
    os.close(fd)
    try:
        report.render_dashboard(_sample_payload(), path)
        html_text = open(path, encoding="utf-8").read()
        assert "2026-08-16T00:00:00Z" in html_text
        assert "__GENERATED_AT__" not in html_text
    finally:
        os.remove(path)
