from src.questions import generate_discussion_questions

_EMPTY_FACTS = {
    "sample_size": None,
    "population": None,
    "methodology": None,
    "effect_size_text": None,
    "p_value_text": None,
    "has_control_comparison": True,
}


def test_empty_facts_still_produce_minimum_questions():
    questions = generate_discussion_questions(_EMPTY_FACTS)
    assert len(questions) >= 3


def test_small_sample_triggers_power_question():
    facts = dict(_EMPTY_FACTS, sample_size=18)
    questions = generate_discussion_questions(facts)
    assert any("N=18" in q for q in questions)


def test_large_sample_does_not_trigger_power_question():
    facts = dict(_EMPTY_FACTS, sample_size=5000)
    questions = generate_discussion_questions(facts)
    assert not any("statistical power" in q for q in questions)


def test_correlational_triggers_causality_question():
    facts = dict(_EMPTY_FACTS, methodology="correlational")
    questions = generate_discussion_questions(facts)
    assert any("causal explanations" in q for q in questions)


def test_fmri_triggers_neuroimaging_question():
    facts = dict(_EMPTY_FACTS, methodology="fMRI")
    questions = generate_discussion_questions(facts)
    assert any("fMRI" in q for q in questions)


def test_eeg_also_triggers_neuroimaging_question():
    facts = dict(_EMPTY_FACTS, methodology="EEG")
    questions = generate_discussion_questions(facts)
    assert any("EEG" in q for q in questions)


def test_survey_methodology_does_not_trigger_neuroimaging_question():
    facts = dict(_EMPTY_FACTS, methodology="survey")
    questions = generate_discussion_questions(facts)
    assert not any("comparisons this type of analysis" in q for q in questions)


def test_no_control_language_triggers_confound_question():
    facts = dict(_EMPTY_FACTS, has_control_comparison=False)
    questions = generate_discussion_questions(facts)
    assert any("confound" in q.lower() or "alternative explanations" in q for q in questions)


def test_has_control_language_does_not_trigger_confound_question():
    facts = dict(_EMPTY_FACTS, has_control_comparison=True)
    questions = generate_discussion_questions(facts)
    assert not any("No explicit control" in q for q in questions)


def test_effect_size_triggers_practical_significance_question():
    facts = dict(_EMPTY_FACTS, effect_size_text="r = 0.61")
    questions = generate_discussion_questions(facts)
    assert any("r = 0.61" in q for q in questions)


def test_meta_analysis_triggers_publication_bias_question():
    facts = dict(_EMPTY_FACTS, methodology="meta-analysis")
    questions = generate_discussion_questions(facts)
    assert any("publication bias" in q for q in questions)


def test_named_population_triggers_generalization_question():
    facts = dict(_EMPTY_FACTS, population="undergraduate sample")
    questions = generate_discussion_questions(facts)
    assert any("undergraduate sample" in q for q in questions)


def test_all_rules_triggered_caps_at_expected_maximum():
    facts = {
        "sample_size": 12,
        "population": "clinical sample",
        "methodology": "fMRI",
        "effect_size_text": "d = 0.9",
        "p_value_text": "p < .01",
        "has_control_comparison": False,
    }
    questions = generate_discussion_questions(facts)
    # 5 rule-triggered questions capped, plus 3 always-included fallbacks.
    assert len(questions) == 8


def test_questions_are_deterministic_across_calls():
    facts = dict(_EMPTY_FACTS, sample_size=15, methodology="correlational")
    first = generate_discussion_questions(facts)
    second = generate_discussion_questions(facts)
    assert first == second


def test_fallback_questions_always_present():
    facts = dict(_EMPTY_FACTS, sample_size=15)
    questions = generate_discussion_questions(facts)
    assert "What is the single most important claim this study makes, and what evidence in the abstract directly supports it?" in questions
