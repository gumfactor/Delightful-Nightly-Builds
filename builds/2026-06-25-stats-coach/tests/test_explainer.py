"""Tests for the AI explainer module (mocked Anthropic client)."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_explainer import build_prompt, generate_explanation


ASSUMPTIONS = [
    "Continuous outcome variable",
    "Two independent groups",
    "Approximately normal distributions",
]


def test_build_prompt_contains_test_name():
    prompt = build_prompt(
        test_name="Independent Samples t-test",
        outcome_type="continuous",
        num_groups=2,
        paired=False,
        normality="assumed",
        relationship=False,
        study_context="",
        assumptions=ASSUMPTIONS,
    )
    assert "Independent Samples t-test" in prompt


def test_build_prompt_contains_outcome_type():
    prompt = build_prompt(
        test_name="One-Way ANOVA",
        outcome_type="continuous",
        num_groups=3,
        paired=False,
        normality="assumed",
        relationship=False,
        study_context="",
        assumptions=ASSUMPTIONS,
    )
    assert "continuous" in prompt


def test_build_prompt_contains_group_description():
    prompt = build_prompt(
        test_name="One-Way ANOVA",
        outcome_type="continuous",
        num_groups=3,
        paired=False,
        normality="assumed",
        relationship=False,
        study_context="",
        assumptions=ASSUMPTIONS,
    )
    assert "three or more groups" in prompt


def test_build_prompt_includes_study_context():
    prompt = build_prompt(
        test_name="Paired Samples t-test",
        outcome_type="continuous",
        num_groups=2,
        paired=True,
        normality="assumed",
        relationship=False,
        study_context="Testing cortisol before and after a stressor",
        assumptions=ASSUMPTIONS,
    )
    assert "cortisol" in prompt


def test_build_prompt_omits_empty_context():
    prompt = build_prompt(
        test_name="Paired Samples t-test",
        outcome_type="continuous",
        num_groups=2,
        paired=True,
        normality="assumed",
        relationship=False,
        study_context="",
        assumptions=ASSUMPTIONS,
    )
    assert "Study context provided" not in prompt


def test_generate_explanation_returns_string():
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="This is the explanation.")]
    mock_client.messages.create.return_value = mock_message

    result = generate_explanation(
        test_name="Independent Samples t-test",
        outcome_type="continuous",
        num_groups=2,
        paired=False,
        normality="assumed",
        relationship=False,
        study_context="",
        assumptions=ASSUMPTIONS,
        client=mock_client,
    )
    assert isinstance(result, str)
    assert result == "This is the explanation."


def test_generate_explanation_calls_api_once():
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Explanation text.")]
    mock_client.messages.create.return_value = mock_message

    generate_explanation(
        test_name="Mann-Whitney U Test",
        outcome_type="continuous",
        num_groups=2,
        paired=False,
        normality="violated",
        relationship=False,
        study_context="",
        assumptions=ASSUMPTIONS,
        client=mock_client,
    )
    assert mock_client.messages.create.call_count == 1


def test_generate_explanation_uses_haiku_model():
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="ok")]
    mock_client.messages.create.return_value = mock_message

    generate_explanation(
        test_name="Pearson Correlation",
        outcome_type="continuous",
        num_groups=2,
        paired=False,
        normality="assumed",
        relationship=True,
        study_context="",
        assumptions=ASSUMPTIONS,
        client=mock_client,
    )
    call_kwargs = mock_client.messages.create.call_args
    assert "haiku" in call_kwargs.kwargs.get("model", "")


def test_generate_explanation_fallback_on_error():
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API timeout")

    result = generate_explanation(
        test_name="Chi-Square Test of Independence",
        outcome_type="categorical",
        num_groups=3,
        paired=False,
        normality="assumed",
        relationship=False,
        study_context="",
        assumptions=ASSUMPTIONS,
        client=mock_client,
    )
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Chi-Square" in result or "unavailable" in result
