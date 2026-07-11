import datetime
import json
from unittest.mock import patch, MagicMock

from src import ai_client, categorize
from src.parser import Transaction


def _txn(description, amount=-10.0):
    return Transaction(date=datetime.date(2026, 1, 1), description=description, amount=amount)


def test_rule_based_matches_grocery_keywords():
    assert categorize.categorize_rule_based("LOBLAWS #4021") == "Groceries"
    assert categorize.categorize_rule_based("COSTCO WHOLESALE") == "Groceries"


def test_rule_based_matches_subscription_keywords():
    assert categorize.categorize_rule_based("NETFLIX.COM") == "Subscriptions"
    assert categorize.categorize_rule_based("SPOTIFY PREMIUM") == "Subscriptions"


def test_rule_based_matches_income_keywords():
    assert categorize.categorize_rule_based("ACME CORP PAYROLL DEPOSIT") == "Income"


def test_unmatched_defaults_to_other():
    assert categorize.categorize_rule_based("XYZQ RANDOM MERCHANT 999") == "Other"


def test_redacts_long_digit_sequences_before_ai_call():
    redacted = ai_client.redact_reference_numbers("PAYMENT REF 1234567890 THANKS")
    assert "1234567890" not in redacted
    assert "[ref]" in redacted
    # Short numbers (store numbers etc.) are left alone.
    assert ai_client.redact_reference_numbers("STORE #42") == "STORE #42"


def test_categorize_transactions_leaves_existing_category_untouched():
    txn = _txn("Some Merchant")
    txn.category = "Custom"
    txn.category_source = "existing"
    stats = categorize.categorize_transactions([txn], use_ai=False)
    assert txn.category == "Custom"
    assert stats["existing"] == 1


def test_no_api_key_skips_ai_and_uses_fallback(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    txn = _txn("UNRECOGNIZABLE MERCHANT XYZ")
    stats = categorize.categorize_transactions([txn], use_ai=True)
    assert txn.category == "Other"
    assert txn.category_source == "rule"
    assert stats["other"] == 1
    assert stats["ai"] == 0


def test_ai_enrichment_merges_results(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    txn = _txn("MYSTERY MERCHANT CO")

    fake_response_body = json.dumps({
        "content": [{"text": json.dumps({"MYSTERY MERCHANT CO": "Shopping"})}]
    }).encode("utf-8")

    mock_response = MagicMock()
    mock_response.read.return_value = fake_response_body
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("src.ai_client.urllib.request.urlopen", return_value=mock_response):
        stats = categorize.categorize_transactions([txn], use_ai=True)

    assert txn.category == "Shopping"
    assert txn.category_source == "ai"
    assert stats["ai"] == 1


def test_ai_call_failure_falls_back_to_rule_based(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    txn = _txn("MYSTERY MERCHANT CO")

    with patch("src.ai_client.urllib.request.urlopen", side_effect=OSError("network down")):
        stats = categorize.categorize_transactions([txn], use_ai=True)

    assert txn.category == "Other"
    assert txn.category_source == "rule"
    assert stats["other"] == 1


def test_use_ai_false_never_calls_api(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    txn = _txn("MYSTERY MERCHANT CO")
    with patch("src.ai_client.urllib.request.urlopen") as mock_urlopen:
        categorize.categorize_transactions([txn], use_ai=False)
    mock_urlopen.assert_not_called()
    assert txn.category == "Other"
