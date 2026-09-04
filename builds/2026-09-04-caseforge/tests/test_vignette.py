from src.vignette import (
    assemble_deterministic_vignette,
    build_polish_prompt,
    polish_with_ai,
    required_fact_strings,
)

_RICH_FACTS = {
    "sample_size": 64,
    "population": "undergraduate sample",
    "methodology": "fMRI",
    "effect_size_text": "r = 0.42",
    "p_value_text": "p < .01",
    "has_control_comparison": True,
}

_SPARSE_FACTS = {
    "sample_size": None,
    "population": None,
    "methodology": None,
    "effect_size_text": None,
    "p_value_text": None,
    "has_control_comparison": False,
}


def test_deterministic_vignette_embeds_all_rich_facts():
    text = assemble_deterministic_vignette("Empathy and the Brain", "Journal of Affective Science", 2024, _RICH_FACTS)
    assert "Empathy and the Brain" in text
    assert "Journal of Affective Science" in text
    assert "2024" in text
    assert "fMRI" in text
    assert "undergraduate sample" in text
    assert "N=64" in text
    assert "r = 0.42" in text
    assert "p < .01" in text


def test_deterministic_vignette_handles_sparse_facts_without_crashing():
    text = assemble_deterministic_vignette("A Theoretical Note", None, None, _SPARSE_FACTS)
    assert "A Theoretical Note" in text
    assert len(text) > 0
    assert "No specific effect size or p-value" in text


def test_required_fact_strings_includes_sample_size_and_stats():
    required = required_fact_strings(_RICH_FACTS)
    assert "64" in required
    assert "r = 0.42" in required
    assert "p < .01" in required


def test_required_fact_strings_empty_for_sparse_facts():
    assert required_fact_strings(_SPARSE_FACTS) == []


def test_build_polish_prompt_includes_title_and_source_text():
    prompt = build_polish_prompt("Some deterministic text.", "A Study Title", "undergrad")
    assert "A Study Title" in prompt
    assert "Some deterministic text." in prompt
    assert "undergrad" in prompt


def test_polish_with_ai_accepts_response_preserving_all_facts():
    deterministic_text = assemble_deterministic_vignette("Title", "Journal", 2023, _RICH_FACTS)

    def fake_ai_call(prompt):
        return "Researchers studied 64 undergraduates and found r = 0.42 with p < .01 in an fMRI study."

    text, source = polish_with_ai(deterministic_text, "Title", _RICH_FACTS, "undergrad", fake_ai_call)
    assert source == "ai"
    assert "64" in text


def test_polish_with_ai_rejects_response_dropping_a_fact():
    deterministic_text = assemble_deterministic_vignette("Title", "Journal", 2023, _RICH_FACTS)

    def fake_ai_call_missing_pvalue(prompt):
        # Drops the p-value entirely — must be rejected.
        return "Researchers studied 64 undergraduates and found r = 0.42 in an fMRI study."

    text, source = polish_with_ai(
        deterministic_text, "Title", _RICH_FACTS, "undergrad", fake_ai_call_missing_pvalue
    )
    assert source == "deterministic"
    assert text == deterministic_text


def test_polish_with_ai_falls_back_when_ai_call_returns_none():
    deterministic_text = assemble_deterministic_vignette("Title", "Journal", 2023, _SPARSE_FACTS)

    def fake_ai_call_no_key(prompt):
        return None

    text, source = polish_with_ai(deterministic_text, "Title", _SPARSE_FACTS, "public", fake_ai_call_no_key)
    assert source == "deterministic"
    assert text == deterministic_text


def test_polish_with_ai_falls_back_when_ai_call_raises():
    deterministic_text = assemble_deterministic_vignette("Title", "Journal", 2023, _SPARSE_FACTS)

    def fake_ai_call_raises(prompt):
        raise RuntimeError("network exploded")

    text, source = polish_with_ai(deterministic_text, "Title", _SPARSE_FACTS, "public", fake_ai_call_raises)
    assert source == "deterministic"
    assert text == deterministic_text


def test_polish_with_ai_accepts_sparse_facts_with_no_requirements():
    deterministic_text = assemble_deterministic_vignette("Title", None, None, _SPARSE_FACTS)

    def fake_ai_call(prompt):
        return "A completely rewritten paragraph with no numbers at all."

    text, source = polish_with_ai(deterministic_text, "Title", _SPARSE_FACTS, "public", fake_ai_call)
    assert source == "ai"
    assert text == "A completely rewritten paragraph with no numbers at all."
