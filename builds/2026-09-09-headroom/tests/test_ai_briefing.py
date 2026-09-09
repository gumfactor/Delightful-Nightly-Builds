import json
from datetime import date
from unittest.mock import MagicMock, patch

from src.ai_briefing import build_summary_payload, deterministic_summary, generate_briefing


def _payload(**overrides):
    payload = build_summary_payload(
        tfsa_available_room=100_000.0,
        tfsa_is_overcontributed=False,
        tfsa_overcontribution_amount=0.0,
        rrsp_available_room=89_660.0,
        rrsp_is_overcontributed=False,
        rrsp_overcontribution_amount=0.0,
        rrsp_deadline=date(2027, 3, 1),
        rrsp_deadline_tax_year=2026,
        tfsa_next_room_date=date(2027, 1, 1),
    )
    payload.update(overrides)
    return payload


def test_no_api_key_never_calls_network():
    with patch("urllib.request.urlopen") as mock_urlopen:
        result = generate_briefing(_payload(), api_key=None)
    mock_urlopen.assert_not_called()
    assert result == deterministic_summary(_payload())


def test_deterministic_summary_mentions_available_room():
    text = deterministic_summary(_payload())
    assert "$100,000.00" in text
    assert "$89,660.00" in text
    assert "2027-03-01" in text


def test_deterministic_summary_flags_overcontribution():
    text = deterministic_summary(_payload(tfsa_is_overcontributed=True, tfsa_overcontribution_amount=500.0))
    assert "over-contributed" in text
    assert "$500.00" in text


def test_generate_briefing_with_api_key_uses_mocked_response():
    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps(
        {"content": [{"text": "You're in good shape — no action needed before March 2027."}]}
    ).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=fake_response) as mock_urlopen:
        result = generate_briefing(_payload(), api_key="fake-key-for-test")

    assert result == "You're in good shape — no action needed before March 2027."
    mock_urlopen.assert_called_once()


def test_generate_briefing_never_leaks_the_fake_key_as_a_body_field():
    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps({"content": [{"text": "ok"}]}).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=fake_response) as mock_urlopen:
        generate_briefing(_payload(), api_key="fake-key-for-test")

    sent_request = mock_urlopen.call_args[0][0]
    assert sent_request.headers.get("X-api-key") == "fake-key-for-test"
    body = json.loads(sent_request.data)
    assert "fake-key-for-test" not in json.dumps(body)


def test_generate_briefing_falls_back_on_network_error():
    with patch("urllib.request.urlopen", side_effect=OSError("network unreachable")):
        result = generate_briefing(_payload(), api_key="fake-key-for-test")
    assert result == deterministic_summary(_payload())


def test_generate_briefing_falls_back_on_malformed_response():
    fake_response = MagicMock()
    fake_response.read.return_value = b"not json"
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=fake_response):
        result = generate_briefing(_payload(), api_key="fake-key-for-test")
    assert result == deterministic_summary(_payload())


def test_prompt_sent_contains_only_aggregate_numbers_not_raw_transactions():
    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps({"content": [{"text": "ok"}]}).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=fake_response) as mock_urlopen:
        generate_briefing(_payload(), api_key="fake-key-for-test")

    sent_request = mock_urlopen.call_args[0][0]
    body = json.loads(sent_request.data)
    prompt_text = body["messages"][0]["content"]
    # Only the aggregate payload fields should appear, never a per-transaction shape.
    assert "tfsa_available_room" in prompt_text
    assert "transaction" not in prompt_text.lower().replace("_transactions_", "")
