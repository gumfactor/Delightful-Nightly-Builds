from src.extraction import (
    extract_all,
    extract_effect_size,
    extract_methodology,
    extract_p_value,
    extract_population,
    extract_sample_size,
    has_control_comparison_language,
)


def test_extract_sample_size_capital_n():
    assert extract_sample_size("A sample of adults (N=142) completed the survey.") == 142


def test_extract_sample_size_lowercase_n():
    assert extract_sample_size("Data were collected from a group (n=58) of undergraduates.") == 58


def test_extract_sample_size_participants_phrasing():
    assert extract_sample_size("87 participants completed the study over two sessions.") == 87


def test_extract_sample_size_absent():
    assert extract_sample_size("This paper reviews prior theoretical work on empathy.") is None


def test_extract_sample_size_implausible_value_rejected():
    # A "sample size" of 0 should never be returned as a real number.
    assert extract_sample_size("N=0 participants were recruited due to funding loss.") is None


def test_extract_p_value_less_than():
    assert extract_p_value("The effect was significant, p < .001.") == "p < .001"


def test_extract_p_value_equals():
    result = extract_p_value("results showed p = 0.03 for the main contrast")
    assert result == "p = 0.03"


def test_extract_p_value_absent():
    assert extract_p_value("No inferential statistics were reported in this abstract.") is None


def test_extract_effect_size_correlation():
    assert extract_effect_size("stress and coping were correlated, r = 0.42") == "r = 0.42"


def test_extract_effect_size_cohens_d():
    assert extract_effect_size("a large effect was found, d = 0.81, between groups") == "d = 0.81"


def test_extract_effect_size_odds_ratio():
    assert extract_effect_size("risk was elevated (OR = 2.3) in the exposed group") == "OR = 2.3"


def test_extract_effect_size_absent():
    assert extract_effect_size("This study describes a novel theoretical framework.") is None


def test_extract_methodology_fmri():
    assert extract_methodology("Using fMRI, we examined amygdala reactivity during the task.") == "fMRI"


def test_extract_methodology_meta_analysis_priority_over_correlational():
    text = "This meta-analysis examined the correlation between empathy and prosocial behavior."
    assert extract_methodology(text) == "meta-analysis"


def test_extract_methodology_rct():
    text = "In this randomized controlled trial, participants were assigned to treatment or control."
    assert extract_methodology(text) == "randomized controlled trial"


def test_extract_methodology_survey():
    assert extract_methodology("Participants completed an online questionnaire about coping styles.") == "survey"


def test_extract_methodology_absent():
    assert extract_methodology("A commentary on the state of the field.") is None


def test_extract_population_incarcerated():
    assert extract_population("A sample of incarcerated adults completed the psychopathy measure.") == "incarcerated/forensic sample"


def test_extract_population_undergraduate():
    assert extract_population("Undergraduate students from a large university participated.") == "undergraduate sample"


def test_extract_population_absent():
    assert extract_population("The theoretical model is described in detail.") is None


def test_has_control_comparison_language_true():
    assert has_control_comparison_language("Outcomes were compared to a control group receiving placebo.") is True


def test_has_control_comparison_language_false():
    assert has_control_comparison_language("A single group of participants was observed longitudinally.") is False


def test_extract_all_returns_full_key_set():
    facts = extract_all("A sample of 40 undergraduates (N=40) showed r = 0.35, p < .05, using a survey.")
    assert set(facts.keys()) == {
        "sample_size",
        "population",
        "methodology",
        "effect_size_text",
        "p_value_text",
        "has_control_comparison",
    }
    assert facts["sample_size"] == 40
    assert facts["effect_size_text"] == "r = 0.35"
    assert facts["p_value_text"] == "p < .05"


def test_extract_all_handles_empty_string():
    facts = extract_all("")
    assert facts["sample_size"] is None
    assert facts["has_control_comparison"] is False
