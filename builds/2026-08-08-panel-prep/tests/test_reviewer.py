import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import checklist, reviewer

COMPLETE_SECTIONS = {
    "aims": "Aim 1: X. Aim 2: Y. Our central hypothesis is that Z. This work will provide a new framework.",
    "significance": "A critical barrier is that this remains unknown. Recent advances make this timely.",
    "innovation": "This proposal is novel and is the first to combine these methods.",
    "approach": (
        "A power analysis indicates a sample size of 80. Timeline: Year 1. "
        "Potential pitfalls exist; an alternative approach is available. "
        "Preliminary data support feasibility. Data will be analyzed using regression."
    ),
    "rigor": "Sex as a biological variable. Randomized and blinded. Authenticated reagents. Reproducibility assessed.",
}

SPARSE_SECTIONS = {"aims": "We will study a phenomenon."}


def _mock_response(body: dict) -> MagicMock:
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value.read.return_value = json.dumps(body).encode("utf-8")
    return mock_cm


def test_deterministic_score_full_checklist_is_best_score():
    checklist_result = checklist.run(COMPLETE_SECTIONS)
    for persona in reviewer.PERSONAS:
        assert reviewer.deterministic_score(checklist_result, persona) == 1


def test_deterministic_score_empty_checklist_is_worst_score():
    checklist_result = checklist.run({})
    for persona in reviewer.PERSONAS:
        assert reviewer.deterministic_score(checklist_result, persona) == 9


def test_deterministic_score_is_monotonic_with_completeness():
    complete = checklist.run(COMPLETE_SECTIONS)
    sparse = checklist.run(SPARSE_SECTIONS)
    persona = reviewer.PERSONAS[0]
    assert reviewer.deterministic_score(complete, persona) <= reviewer.deterministic_score(sparse, persona)


def test_deterministic_rationale_references_failed_checks_when_incomplete():
    checklist_result = checklist.run(SPARSE_SECTIONS)
    persona = next(p for p in reviewer.PERSONAS if p["key"] == "rigor_hawk")
    rationale = reviewer.deterministic_rationale(checklist_result, persona)
    assert len(rationale) > 0
    assert any("Approach" in bullet or "Rigor" in bullet for bullet in rationale)


def test_deterministic_rationale_is_positive_when_complete():
    checklist_result = checklist.run(COMPLETE_SECTIONS)
    persona = reviewer.PERSONAS[0]
    rationale = reviewer.deterministic_rationale(checklist_result, persona)
    assert len(rationale) == 1
    assert "present" in rationale[0].lower()


def test_no_api_key_makes_zero_network_calls():
    checklist_result = checklist.run(COMPLETE_SECTIONS)
    persona = reviewer.PERSONAS[0]
    with patch("urllib.request.urlopen") as mock_urlopen:
        result = reviewer.ai_persona_critique(persona, COMPLETE_SECTIONS, checklist_result, api_key=None)
    assert result is None
    mock_urlopen.assert_not_called()


def test_well_formed_ai_response_is_used():
    checklist_result = checklist.run(COMPLETE_SECTIONS)
    persona = reviewer.PERSONAS[0]
    api_body = {"content": [{"text": json.dumps({"score": 3, "rationale": ["Concern one.", "Concern two."]})}]}
    with patch("urllib.request.urlopen", return_value=_mock_response(api_body)):
        result = reviewer.ai_persona_critique(persona, COMPLETE_SECTIONS, checklist_result, api_key="fake-key")
    assert result == {"score": 3, "rationale": ["Concern one.", "Concern two."]}


def test_malformed_ai_json_falls_back_to_none():
    checklist_result = checklist.run(COMPLETE_SECTIONS)
    persona = reviewer.PERSONAS[0]
    api_body = {"content": [{"text": "not valid json"}]}
    with patch("urllib.request.urlopen", return_value=_mock_response(api_body)):
        result = reviewer.ai_persona_critique(persona, COMPLETE_SECTIONS, checklist_result, api_key="fake-key")
    assert result is None


def test_ai_response_missing_required_fields_falls_back_to_none():
    checklist_result = checklist.run(COMPLETE_SECTIONS)
    persona = reviewer.PERSONAS[0]
    api_body = {"content": [{"text": json.dumps({"score": 3})}]}
    with patch("urllib.request.urlopen", return_value=_mock_response(api_body)):
        result = reviewer.ai_persona_critique(persona, COMPLETE_SECTIONS, checklist_result, api_key="fake-key")
    assert result is None


def test_ai_response_score_out_of_range_falls_back_to_none():
    checklist_result = checklist.run(COMPLETE_SECTIONS)
    persona = reviewer.PERSONAS[0]
    api_body = {"content": [{"text": json.dumps({"score": 15, "rationale": ["x"]})}]}
    with patch("urllib.request.urlopen", return_value=_mock_response(api_body)):
        result = reviewer.ai_persona_critique(persona, COMPLETE_SECTIONS, checklist_result, api_key="fake-key")
    assert result is None


def test_network_error_falls_back_to_none():
    checklist_result = checklist.run(COMPLETE_SECTIONS)
    persona = reviewer.PERSONAS[0]
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("no network")):
        result = reviewer.ai_persona_critique(persona, COMPLETE_SECTIONS, checklist_result, api_key="fake-key")
    assert result is None


def test_build_review_falls_back_fully_deterministic_without_key():
    checklist_result = checklist.run(COMPLETE_SECTIONS)
    review = reviewer.build_review(COMPLETE_SECTIONS, checklist_result, api_key=None)
    assert review["ai_used"] is False
    assert all(p["source"] == "deterministic" for p in review["personas"])
    assert review["overall_impact"] == 1.0


def test_build_review_uses_ai_when_available_and_well_formed():
    checklist_result = checklist.run(COMPLETE_SECTIONS)
    api_body = {"content": [{"text": json.dumps({"score": 2, "rationale": ["Strong draft overall."]})}]}
    with patch("urllib.request.urlopen", return_value=_mock_response(api_body)):
        review = reviewer.build_review(COMPLETE_SECTIONS, checklist_result, api_key="fake-key")
    assert review["ai_used"] is True
    assert all(p["source"] == "ai" for p in review["personas"])
    assert review["overall_impact"] == 2.0


def test_build_resume_notes_divergence_when_scores_vary():
    personas_out = [
        {"key": "a", "name": "A", "score": 1, "rationale": [], "source": "deterministic"},
        {"key": "b", "name": "B", "score": 8, "rationale": [], "source": "deterministic"},
    ]
    checklist_result = checklist.run(COMPLETE_SECTIONS)
    resume = reviewer.build_resume(personas_out, checklist_result)
    assert "diverged" in resume
