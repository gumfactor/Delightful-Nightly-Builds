import json

from src.graph import Cycle, Edge, Evidence, ModuleMetrics
from src.layers import LayerAssignment, Violation
from src.report import AnalysisResult, render_html, render_json, render_terminal, to_dict


def _basic_result(**overrides):
    defaults = dict(
        root="/tmp/project",
        modules=["a", "b"],
        edges=[Edge(importer="a", importee="b", evidence=(Evidence("a.py", 3, "import b"),))],
        cycles=[],
        metrics=[
            ModuleMetrics(module="a", afferent=0, efferent=1, instability=1.0, structural_risk=False),
            ModuleMetrics(module="b", afferent=1, efferent=0, instability=0.0, structural_risk=False),
        ],
        layer_assignment=None,
        violations=[],
        ai_note="Looks fine.",
        warnings=[],
    )
    defaults.update(overrides)
    return AnalysisResult(**defaults)


def test_to_dict_json_round_trip():
    result = _basic_result()
    data = json.loads(render_json(result))
    assert data["modules"] == ["a", "b"]
    assert data["edges"][0]["importer"] == "a"
    assert data["edges"][0]["evidence"][0]["line"] == 3
    assert data["layers"] is None
    assert data["ai_note"] == "Looks fine."


def test_to_dict_includes_layers_when_present():
    assignment = LayerAssignment(order=("core", "ui"), assigned={"a": "core", "b": "ui"}, unassigned=())
    result = _basic_result(layer_assignment=assignment)
    data = to_dict(result)
    assert data["layers"]["order"] == ["core", "ui"]
    assert data["layers"]["assigned"]["a"] == "core"


def test_render_terminal_reports_clean_result():
    output = render_terminal(_basic_result(), use_color=False)
    assert "Cycles found: 0" in output
    assert "\033[" not in output  # no ANSI codes when color disabled


def test_render_terminal_reports_cycle():
    edge = Edge(importer="a", importee="b", evidence=(Evidence("a.py", 1, "import b"),))
    cycle = Cycle(modules=("a", "b", "a"), edges=(edge,))
    output = render_terminal(_basic_result(cycles=[cycle]), use_color=False)
    assert "a -> b -> a" in output


def test_render_html_contains_expected_markers():
    html = render_html(_basic_result())
    assert "<title>Layer Guard Report</title>" in html
    assert 'id="lg-data"' in html
    assert "<canvas" in html


def test_render_html_escapes_script_injection_in_evidence():
    payload = "</script><script>alert(1)</script>"
    evidence = (Evidence(file=payload, line=1, statement="import x"),)
    edge = Edge(importer="a", importee="b", evidence=evidence)
    result = _basic_result(edges=[edge])

    html = render_html(result)

    assert "</script><script>alert(1)</script>" not in html

    start = html.index('id="lg-data">') + len('id="lg-data">')
    end = html.index("</script>", start)
    embedded_json = html[start:end]
    parsed = json.loads(embedded_json)
    assert parsed["edges"][0]["evidence"][0]["file"] == payload


def test_render_html_reports_no_layers_message_when_absent():
    html = render_html(_basic_result(layer_assignment=None))
    assert "No layer configuration supplied" in html
