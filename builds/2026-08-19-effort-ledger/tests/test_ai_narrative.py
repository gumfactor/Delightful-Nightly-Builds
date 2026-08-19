import json
import urllib.error
from datetime import date
from unittest.mock import MagicMock, patch

from src.ai_narrative import build_aggregate_summary, deterministic_template, generate_ai_briefing
from src.models import Flag, GrantBudgetSummary, OvercommitmentWindow, Severity


def test_build_aggregate_summary_contains_no_names_dollars_or_grant_ids():
    flags = [
        Flag(Severity.ERROR, "indirect_mismatch", "Secret Grant Name mismatch of $12,345.67", grant_id="R01-SECRET"),
        Flag(Severity.WARNING, "missing_fringe", "msg", grant_id="R01-SECRET"),
        Flag(Severity.ERROR, "overcommitment", "Dr. Jane Doe overcommitted", person_name="Dr. Jane Doe"),
    ]
    summaries = [
        GrantBudgetSummary("R01-SECRET", "Secret Grant Name", "2026", 10000, 8000, 4000, 4000, 14000)
    ]
    windows = [OvercommitmentWindow("Dr. Jane Doe", date(2026, 1, 1), date(2026, 6, 1), 110, ("R01-SECRET",))]

    aggregate = build_aggregate_summary(flags, summaries, windows)
    serialized = json.dumps(aggregate)

    assert "Jane Doe" not in serialized
    assert "R01-SECRET" not in serialized
    assert "Secret Grant Name" not in serialized
    assert "12,345.67" not in serialized
    assert aggregate["total_grants"] == 1
    assert aggregate["total_flags"] == 3
    assert aggregate["errors"] == 2
    assert aggregate["warnings"] == 1
    assert aggregate["people_overcommitted"] == 1


def test_deterministic_template_zero_flags():
    aggregate = {"total_grants": 2, "total_flags": 0, "errors": 0, "warnings": 0, "info": 0,
                 "people_overcommitted": 0, "flag_types": {}}
    text = deterministic_template(aggregate)
    assert "zero flags" in text
    assert len(text) > 0


def test_deterministic_template_with_flags_mentions_counts():
    aggregate = {"total_grants": 3, "total_flags": 5, "errors": 2, "warnings": 2, "info": 1,
                 "people_overcommitted": 1, "flag_types": {"overcommitment": 1}}
    text = deterministic_template(aggregate)
    assert "5 flag" in text
    assert "1 person" in text or "overlapping effort" in text


def test_generate_ai_briefing_no_api_key_uses_deterministic_fallback_zero_network_calls():
    aggregate = {"total_grants": 1, "total_flags": 0, "errors": 0, "warnings": 0, "info": 0,
                 "people_overcommitted": 0, "flag_types": {}}
    with patch("urllib.request.urlopen") as mock_urlopen:
        result = generate_ai_briefing(aggregate, None)
    mock_urlopen.assert_not_called()
    assert result == deterministic_template(aggregate)


def test_generate_ai_briefing_with_key_uses_mocked_response():
    aggregate = {"total_grants": 1, "total_flags": 1, "errors": 1, "warnings": 0, "info": 0,
                 "people_overcommitted": 0, "flag_types": {"indirect_mismatch": 1}}

    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(
        {"content": [{"type": "text", "text": "One error found in the indirect cost calculation."}]}
    ).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        result = generate_ai_briefing(aggregate, "fake-api-key")

    mock_urlopen.assert_called_once()
    assert result == "One error found in the indirect cost calculation."


def test_generate_ai_briefing_falls_back_on_network_error():
    aggregate = {"total_grants": 1, "total_flags": 0, "errors": 0, "warnings": 0, "info": 0,
                 "people_overcommitted": 0, "flag_types": {}}
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("no network")):
        result = generate_ai_briefing(aggregate, "fake-api-key")
    assert result == deterministic_template(aggregate)


def test_generate_ai_briefing_falls_back_on_malformed_response():
    aggregate = {"total_grants": 1, "total_flags": 0, "errors": 0, "warnings": 0, "info": 0,
                 "people_overcommitted": 0, "flag_types": {}}
    mock_response = MagicMock()
    mock_response.read.return_value = b"not valid json"
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False
    with patch("urllib.request.urlopen", return_value=mock_response):
        result = generate_ai_briefing(aggregate, "fake-api-key")
    assert result == deterministic_template(aggregate)
