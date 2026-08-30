import json
from unittest.mock import MagicMock, patch

from src.ai import build_note
from src.graph import Cycle, Edge, Evidence, ModuleMetrics
from src.layers import Violation


def _cycle():
    edge = Edge(importer="a", importee="b", evidence=(Evidence("f.py", 1, "import b"),))
    return Cycle(modules=("a", "b", "a"), edges=(edge,))


def _violation():
    return Violation(
        importer="core_mod",
        importer_layer="core",
        importee="ui_mod",
        importee_layer="ui",
        evidence=(Evidence("f.py", 2, "import ui_mod"),),
    )


def _risky_metric():
    return ModuleMetrics(module="hub", afferent=3, efferent=9, instability=0.75, structural_risk=True)


def test_deterministic_note_when_everything_clean():
    note = build_note([], [], [], api_key=None)
    assert "healthy" in note.lower()


def test_deterministic_note_mentions_cycle_and_violation():
    note = build_note([_cycle()], [_violation()], [_risky_metric()], api_key=None)
    assert "a -> b -> a" in note
    assert "core_mod" in note
    assert "hub" in note


def test_no_api_key_makes_zero_network_calls():
    with patch("urllib.request.urlopen") as mock_urlopen:
        build_note([_cycle()], [], [], api_key=None)
        mock_urlopen.assert_not_called()


def test_api_key_set_uses_mocked_anthropic_response():
    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps({"content": [{"text": "Fix the a<->b cycle first."}]}).encode()
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=fake_response) as mock_urlopen:
        note = build_note([_cycle()], [], [], api_key="sk-test-key")
        mock_urlopen.assert_called_once()
        assert note == "Fix the a<->b cycle first."


def test_api_call_failure_falls_back_to_deterministic_note():
    with patch("urllib.request.urlopen", side_effect=OSError("network unreachable")):
        note = build_note([_cycle()], [], [], api_key="sk-test-key")
    assert "a -> b -> a" in note
