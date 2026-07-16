import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.ai_review import run_ai_review

FIXTURES = Path(__file__).parent / "fixtures"


def _mock_response(text: str):
    response = MagicMock()
    response.read.return_value = json.dumps({
        "content": [{"type": "text", "text": text}]
    }).encode("utf-8")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def test_ai_review_skipped_when_no_api_key():
    with patch("src.ai_review.urllib.request.urlopen") as mock_urlopen:
        findings = run_ai_review("some instructions", api_key=None)
    mock_urlopen.assert_not_called()
    assert len(findings) == 1
    assert findings[0]["severity"] == "info"
    assert "skipped" in findings[0]["message"]


def test_ai_review_parses_valid_json_response():
    canned = json.dumps([
        {"severity": "warning", "message": "Ambiguous instruction.", "excerpt": "do it right"}
    ])
    with patch("src.ai_review.urllib.request.urlopen", return_value=_mock_response(canned)):
        findings = run_ai_review("instructions text", api_key="fake-key-for-test")
    assert len(findings) == 1
    assert findings[0]["severity"] == "warning"
    assert findings[0]["message"] == "Ambiguous instruction."
    assert findings[0]["check"] == "ai_review"


def test_ai_review_handles_malformed_json_gracefully():
    with patch("src.ai_review.urllib.request.urlopen", return_value=_mock_response("not json at all")):
        findings = run_ai_review("instructions text", api_key="fake-key-for-test")
    assert len(findings) == 1
    assert findings[0]["severity"] == "warning"
    assert "unparseable" in findings[0]["message"]


def test_ai_review_handles_network_failure_gracefully():
    import urllib.error
    with patch("src.ai_review.urllib.request.urlopen", side_effect=urllib.error.URLError("no network")):
        findings = run_ai_review("instructions text", api_key="fake-key-for-test")
    assert len(findings) == 1
    assert findings[0]["severity"] == "warning"
    assert "failed" in findings[0]["message"]


def test_ai_review_flags_ground_truth_contradiction():
    """Mirrors the real drift found tonight: a CLAUDE.md-style calibration
    claim ("every build scored <=4/10") contradicted by an index.md-style
    ground-truth catalog showing a 9/10 rating. The mocked response below
    reflects what a real semantic review of these two fixtures would
    plausibly return."""
    instructions_text = (FIXTURES / "mini_claude_md.md").read_text(encoding="utf-8")
    ground_truth_text = (FIXTURES / "mini_index_md.md").read_text(encoding="utf-8")

    canned = json.dumps([
        {
            "severity": "error",
            "message": (
                "The calibration note claims every build scored 4/10 or below, but the "
                "ground-truth catalog shows a 9/10 rating for Qualtrics Survey Data Inspector "
                "(2026-06-17)."
            ),
            "excerpt": "Every rated build to date has scored 4/10 or below.",
        }
    ])

    with patch("src.ai_review.urllib.request.urlopen", return_value=_mock_response(canned)):
        findings = run_ai_review(instructions_text, ground_truth_text, api_key="fake-key-for-test")

    assert len(findings) == 1
    assert findings[0]["severity"] == "error"
    assert "9/10" in findings[0]["message"]
    assert "Qualtrics" in findings[0]["message"]


def test_ai_review_returns_empty_list_when_model_reports_no_issues():
    with patch("src.ai_review.urllib.request.urlopen", return_value=_mock_response("[]")):
        findings = run_ai_review("clean instructions", api_key="fake-key-for-test")
    assert findings == []


def test_ai_review_sends_ground_truth_in_request_payload():
    captured = {}

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _mock_response("[]")

    with patch("src.ai_review.urllib.request.urlopen", side_effect=fake_urlopen):
        run_ai_review("main instructions", "ground truth content", api_key="fake-key-for-test")

    user_message = captured["body"]["messages"][0]["content"]
    assert "main instructions" in user_message
    assert "ground truth content" in user_message
