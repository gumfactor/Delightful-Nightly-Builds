import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import render

SAMPLE_ROW = {
    "id": 1,
    "created_at": "2026-07-12T00:00:00+00:00",
    "population": "p_healthy_controls",
    "construct": "c_empathic_accuracy",
    "outcome": "o_prosocial_behavior",
    "method": "m_behavioral_task",
    "frame": "f_dual_process_empathy",
    "skeleton": "Does empathic accuracy predict prosocial behavior?",
    "rationale": "Measured via a behavioral task.",
    "testability": "feasible-now",
    "novelty_score": 0.95,
    "ai_polish": None,
    "ai_source": "template",
    "starred": False,
    "used": False,
    "tag": "",
}


def test_render_html_includes_all_questions():
    rows = [SAMPLE_ROW, dict(SAMPLE_ROW, id=2, skeleton="Does cortisol reactivity predict burnout?")]
    output = render.render_html(rows)
    assert "empathic accuracy predict prosocial behavior" in output
    assert "cortisol reactivity predict burnout" in output


def test_render_html_reflects_starred_state():
    starred_row = dict(SAMPLE_ROW, starred=True)
    output = render.render_html([starred_row])
    assert '"starred": true' in output


def test_render_html_escapes_script_injection_in_tag_field():
    malicious_row = dict(SAMPLE_ROW, tag="</script><script>alert(1)</script>")
    output = render.render_html([malicious_row])
    # The literal closing-script sequence must never appear unescaped in the output,
    # otherwise the injected payload would execute in the browser.
    assert "</script><script>alert(1)</script>" not in output
    assert "<\\/script><script>alert(1)<\\/script>" in output


def test_render_html_handles_empty_library():
    output = render.render_html([])
    assert "0 questions" in output
    assert "<html" in output


def test_write_html_creates_output_file(tmp_path):
    output_path = tmp_path / "nested" / "forge.html"
    written = render.write_html([SAMPLE_ROW], output_path)
    assert written == output_path
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "empathic accuracy" in content
