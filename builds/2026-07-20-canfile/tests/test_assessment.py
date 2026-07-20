from unittest.mock import MagicMock, patch

import assessment


def test_canadian_no_parent_high_confidence():
    facts = {"country_labels": ["Canada"], "headquarters_labels": ["Oakville"]}
    result = assessment.deterministic_assessment("Tim Hortons", facts)
    assert result["verdict"] == assessment.VERDICT_CANADIAN
    assert result["confidence"] == assessment.CONFIDENCE_HIGH
    assert "Tim Hortons" in result["text"]


def test_foreign_no_parent_high_confidence():
    facts = {"country_labels": ["United States of America"], "headquarters_labels": ["Chicago"]}
    result = assessment.deterministic_assessment("Acme USA", facts)
    assert result["verdict"] == assessment.VERDICT_FOREIGN
    assert result["confidence"] == assessment.CONFIDENCE_HIGH


def test_foreign_parent_overrides_own_country():
    facts = {
        "country_labels": ["Canada"],
        "parent_organization_labels": ["MegaCorp Holdings"],
        "parent_country_labels": ["United States of America"],
    }
    result = assessment.deterministic_assessment("Local Subsidiary Inc", facts)
    assert result["verdict"] == assessment.VERDICT_FOREIGN
    assert result["confidence"] == assessment.CONFIDENCE_HIGH
    assert "MegaCorp Holdings" in result["text"]


def test_canadian_parent_confirms_canadian_ownership():
    facts = {
        "country_labels": [],
        "owned_by_labels": ["Canadian Holdco"],
        "parent_country_labels": ["Canada"],
    }
    result = assessment.deterministic_assessment("Some Brand", facts)
    assert result["verdict"] == assessment.VERDICT_CANADIAN
    assert result["confidence"] == assessment.CONFIDENCE_HIGH


def test_parent_present_but_country_unknown_is_uncertain():
    facts = {"country_labels": [], "parent_organization_labels": ["Mystery Holdco"], "parent_country_labels": []}
    result = assessment.deterministic_assessment("Mystery Brand", facts)
    assert result["verdict"] == assessment.VERDICT_UNCERTAIN
    assert result["confidence"] == assessment.CONFIDENCE_MEDIUM


def test_no_data_at_all_is_insufficient():
    facts = {}
    result = assessment.deterministic_assessment("Unknown Co", facts)
    assert result["verdict"] == assessment.VERDICT_INSUFFICIENT
    assert result["confidence"] == assessment.CONFIDENCE_LOW


def test_enrich_with_claude_no_api_key_returns_deterministic_text():
    deterministic = {"verdict": "canadian", "confidence": "high", "text": "deterministic text here"}
    with patch.dict("os.environ", {}, clear=True):
        result = assessment.enrich_with_claude("Tim Hortons", {}, deterministic, api_key=None)
    assert result == "deterministic text here"


def test_enrich_with_claude_success_returns_claude_text():
    deterministic = {"verdict": "canadian", "confidence": "high", "text": "fallback"}
    fake_block = MagicMock()
    fake_block.type = "text"
    fake_block.text = "Claude-written assessment mentioning Canada."
    fake_response = MagicMock()
    fake_response.content = [fake_block]

    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_response

    fake_anthropic_module = MagicMock()
    fake_anthropic_module.Anthropic.return_value = fake_client

    with patch.dict("sys.modules", {"anthropic": fake_anthropic_module}):
        result = assessment.enrich_with_claude("Tim Hortons", {}, deterministic, api_key="fake-key")

    assert result == "Claude-written assessment mentioning Canada."


def test_enrich_with_claude_falls_back_on_exception():
    deterministic = {"verdict": "canadian", "confidence": "high", "text": "fallback text"}
    fake_anthropic_module = MagicMock()
    fake_anthropic_module.Anthropic.side_effect = RuntimeError("API down")

    with patch.dict("sys.modules", {"anthropic": fake_anthropic_module}):
        result = assessment.enrich_with_claude("Tim Hortons", {}, deterministic, api_key="fake-key")

    assert result == "fallback text"
