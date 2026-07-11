import os
from unittest.mock import patch

from ai_summary import ANTHROPIC_API_URL, _post_json, generate_methods_paragraph, _deterministic_paragraph
from qc import QCConfig, SubjectSummary, ConditionSummary


def make_subjects():
    clean = SubjectSummary(
        subject="S1", n_trials=10, n_correct=9, accuracy=0.9, mean_rt=450.0,
        median_rt=440.0, sd_rt=50.0, flags=[],
    )
    excluded = SubjectSummary(
        subject="S2", n_trials=10, n_correct=5, accuracy=0.5, mean_rt=400.0,
        median_rt=400.0, sd_rt=30.0, flags=["chance_level (p=0.623 vs chance=0.50)"],
    )
    conditions = [ConditionSummary(condition="A", n_trials=20, n_subjects=2, accuracy=0.7, mean_rt=425.0, sd_rt=40.0)]
    return [clean, excluded], conditions, [excluded]


def test_deterministic_paragraph_includes_subject_counts():
    subjects, conditions, excluded = make_subjects()
    text = _deterministic_paragraph(subjects, conditions, excluded, QCConfig())
    assert "2" in text  # total subjects
    assert "1" in text  # excluded count
    assert "chance level" in text.lower() or "chance" in text.lower()


def test_deterministic_paragraph_handles_zero_subjects():
    text = _deterministic_paragraph([], [], [], QCConfig())
    assert "no subjects" in text.lower() or "no data" in text.lower()


def test_deterministic_paragraph_handles_zero_exclusions():
    subjects, conditions, _ = make_subjects()
    text = _deterministic_paragraph(subjects, conditions, [], QCConfig())
    assert "0" in text


def test_generate_methods_paragraph_uses_template_when_no_api_key():
    subjects, conditions, excluded = make_subjects()
    with patch.dict(os.environ, {}, clear=True):
        text, source = generate_methods_paragraph(subjects, conditions, excluded, QCConfig())
    assert source == "template"
    assert len(text) > 0


def test_generate_methods_paragraph_uses_ai_response_when_key_present_and_call_succeeds():
    subjects, conditions, excluded = make_subjects()
    fake_response = (200, {
        "content": [{"type": "text", "text": "Two participants completed the task; one was excluded."}]
    })
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-test-key"}, clear=True):
        with patch("ai_summary._post_json", return_value=fake_response) as mock_post:
            text, source = generate_methods_paragraph(subjects, conditions, excluded, QCConfig())
    assert source == "ai"
    assert "excluded" in text.lower()
    assert mock_post.called
    call_args = mock_post.call_args
    assert call_args.kwargs["headers"]["x-api-key"] == "fake-test-key"


def test_generate_methods_paragraph_falls_back_to_template_on_non_200_response():
    subjects, conditions, excluded = make_subjects()
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-test-key"}, clear=True):
        with patch("ai_summary._post_json", return_value=(401, None)):
            text, source = generate_methods_paragraph(subjects, conditions, excluded, QCConfig())
    assert source == "template"
    assert len(text) > 0


def test_generate_methods_paragraph_falls_back_to_template_on_network_error():
    subjects, conditions, excluded = make_subjects()
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-test-key"}, clear=True):
        with patch("ai_summary._post_json", return_value=(None, None)):
            text, source = generate_methods_paragraph(subjects, conditions, excluded, QCConfig())
    assert source == "template"
    assert len(text) > 0


def test_post_json_real_request_against_anthropic_api_with_invalid_key():
    # Genuine end-to-end network call (no mocking) to the real Anthropic Messages
    # endpoint, using a deliberately invalid key. This is not testing successful AI
    # generation (no valid key is available in this build/test environment) -- it
    # verifies the raw HTTP plumbing (request construction, HTTPError handling,
    # JSON body parsing) actually works against the real service rather than only
    # against a mock. A real 401 with a parsed error body is the expected outcome.
    status, data = _post_json(
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": "sk-ant-invalid-test-key",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        payload={"model": "claude-haiku-4-5-20251001", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]},
        timeout=20,
    )
    assert status == 401
    assert data is not None
    assert data.get("type") == "error"
