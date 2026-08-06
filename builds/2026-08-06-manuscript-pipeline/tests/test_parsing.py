import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import parsing

ACCEPT_EMAIL = """
Dear Dr. Doe,

We are pleased to accept your manuscript submitted to Journal of Examples
for publication. Congratulations.

Best,
Editor
"""

REJECT_EMAIL = """
Dear Dr. Doe,

I regret to inform you that we are unable to accept your manuscript for
publication in Journal of Examples at this time.

Editor
"""

REVISE_EMAIL = """
Dear Dr. Doe,

Your manuscript submitted to Journal of Examples requires major revision.
Please submit your revised manuscript by 2026-09-15.

Editor
"""

REVISE_EMAIL_MONTH_NAME = """
Dear Dr. Doe,

Your submission to Journal of Examples requires minor revision. Please
resubmit by September 15, 2026.

Editor
"""

AMBIGUOUS_EMAIL = "Thank you for your submission. We will be in touch."


def test_deterministic_parse_detects_acceptance():
    result = parsing.deterministic_parse(ACCEPT_EMAIL)
    assert result["decision"] == "accepted"
    assert result["journal"] == "Journal of Examples"
    assert result["source"] == "capture-fallback"


def test_deterministic_parse_detects_rejection():
    result = parsing.deterministic_parse(REJECT_EMAIL)
    assert result["decision"] == "rejected"


def test_deterministic_parse_detects_revise_and_deadline_iso():
    result = parsing.deterministic_parse(REVISE_EMAIL)
    assert result["decision"] == "revise_resubmit"
    assert result["revision_deadline"] == "2026-09-15"


def test_deterministic_parse_detects_deadline_from_month_name():
    result = parsing.deterministic_parse(REVISE_EMAIL_MONTH_NAME)
    assert result["decision"] == "revise_resubmit"
    assert result["revision_deadline"] == "2026-09-15"


def test_deterministic_parse_degrades_gracefully_on_ambiguous_text():
    result = parsing.deterministic_parse(AMBIGUOUS_EMAIL)
    assert result["decision"] is None
    assert result["journal"] is None


def test_deterministic_parse_handles_empty_text():
    result = parsing.deterministic_parse("")
    assert result["decision"] is None


def test_ai_parse_makes_no_network_call_without_api_key():
    with patch("urllib.request.urlopen") as mock_urlopen:
        result = parsing.ai_parse(ACCEPT_EMAIL, api_key=None)
        assert result is None
        mock_urlopen.assert_not_called()


def test_ai_parse_returns_parsed_result_on_well_formed_response():
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "content": [{"text": json.dumps({
            "decision": "accepted",
            "journal": "Journal of Examples",
            "revision_deadline": None,
        })}]
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_response):
        result = parsing.ai_parse(ACCEPT_EMAIL, api_key="fake-key")

    assert result["decision"] == "accepted"
    assert result["journal"] == "Journal of Examples"
    assert result["source"] == "capture-ai"


def test_ai_parse_falls_back_to_none_on_malformed_json():
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "content": [{"text": "not valid json {{{"}]
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_response):
        result = parsing.ai_parse(ACCEPT_EMAIL, api_key="fake-key")

    assert result is None


def test_ai_parse_falls_back_to_none_on_network_error():
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
        result = parsing.ai_parse(ACCEPT_EMAIL, api_key="fake-key")
    assert result is None


def test_extract_prefers_ai_result_when_available():
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "content": [{"text": json.dumps({
            "decision": "rejected",
            "journal": "AI-Detected Journal",
            "revision_deadline": None,
        })}]
    }).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_response):
        result = parsing.extract(ACCEPT_EMAIL, api_key="fake-key")

    assert result["journal"] == "AI-Detected Journal"
    assert result["source"] == "capture-ai"


def test_extract_falls_back_to_deterministic_when_no_api_key():
    result = parsing.extract(ACCEPT_EMAIL, api_key=None)
    assert result["source"] == "capture-fallback"
    assert result["decision"] == "accepted"
