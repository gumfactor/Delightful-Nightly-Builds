import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import generator


def test_load_taxonomy_has_all_dimensions():
    tax = generator.load_taxonomy()
    for key in ("populations", "constructs", "outcomes", "methods", "frames"):
        assert key in tax
        assert len(tax[key]) >= 5


def test_all_valid_combinations_only_yields_compatible_combos():
    tax = generator.load_taxonomy()
    combos = list(generator.all_valid_combinations(tax))
    assert len(combos) > 0
    for population, construct, outcome, method, frame in combos:
        assert generator.is_compatible(population, construct, outcome, method, frame)


def test_is_compatible_rejects_method_with_excluded_construct():
    tax = generator.load_taxonomy()
    by_id = {item["id"]: item for group in tax.values() for item in group}
    # fMRI requires a 'neural' tag; pairing it with a construct/outcome pair
    # that has no 'neural' tag anywhere must be rejected.
    population = by_id["p_healthy_controls"]
    construct = by_id["c_cortisol_reactivity"]  # tags: stress, physiological (no 'neural')
    outcome = by_id["o_self_reported_burnout"]  # tags: self-report (no 'neural')
    method = by_id["m_fmri"]  # requires 'neural'
    frame = by_id["f_allostatic_load"]
    assert generator.is_compatible(population, construct, outcome, method, frame) is False


def test_is_compatible_accepts_a_known_good_combo():
    tax = generator.load_taxonomy()
    by_id = {item["id"]: item for group in tax.values() for item in group}
    population = by_id["p_frontline_clinicians"]  # tags include empathy, stress
    construct = by_id["c_affective_empathy"]  # tags: empathy, self-report, neural
    outcome = by_id["o_deception_detection"]  # tags: behavioral
    method = by_id["m_behavioral_task"]  # requires behavioral
    frame = by_id["f_dual_process_empathy"]  # tags: empathy
    assert generator.is_compatible(population, construct, outcome, method, frame) is True


def test_testability_tag_flags_forensic_neuroimaging_as_speculative():
    tax = generator.load_taxonomy()
    by_id = {item["id"]: item for group in tax.values() for item in group}
    population = by_id["p_forensic_offenders"]
    method = by_id["m_fmri"]
    assert generator.testability_tag(population, method) == "speculative"


def test_testability_tag_flags_survey_as_feasible_now():
    tax = generator.load_taxonomy()
    by_id = {item["id"]: item for group in tax.values() for item in group}
    population = by_id["p_healthy_controls"]
    method = by_id["m_survey_longitudinal"]
    assert generator.testability_tag(population, method) == "feasible-now"


def test_novelty_score_is_full_for_empty_library():
    assert generator.novelty_score("Does X predict Y in Z?", []) == 1.0


def test_novelty_score_is_lower_for_a_near_duplicate():
    original = "Does empathic accuracy predict prosocial behavior in caregivers?"
    near_dup = "Does empathic accuracy predict prosocial behavior in clinicians?"
    unrelated = "Does cortisol reactivity predict burnout in graduate students?"

    dup_score = generator.novelty_score(near_dup, [original])
    unrelated_score = generator.novelty_score(unrelated, [original])

    assert dup_score < unrelated_score
    assert dup_score < 1.0


def test_generate_batch_respects_count_and_dedupes():
    existing = []
    batch = generator.generate_batch(10, existing, rng_seed=1)
    assert len(batch) == 10
    combo_keys = {(q["population"], q["construct"], q["outcome"], q["method"], q["frame"]) for q in batch}
    assert len(combo_keys) == len(batch)


def test_generate_batch_is_deterministic_with_seed():
    batch_a = generator.generate_batch(5, [], rng_seed=99)
    batch_b = generator.generate_batch(5, [], rng_seed=99)
    assert [q["skeleton"] for q in batch_a] == [q["skeleton"] for q in batch_b]


def test_generate_batch_caps_at_available_valid_combinations():
    # A tiny synthetic taxonomy with exactly one compatible combination, so this
    # test exercises the "requested more than exists" cap without the O(n^2)
    # novelty-scoring cost of exhausting the full real taxonomy (~7000 combos).
    tiny_taxonomy = {
        "populations": [{"id": "p1", "label": "healthy adults", "tags": ["stress"]}],
        "constructs": [{"id": "c1", "label": "cortisol reactivity", "tags": ["stress", "physiological"]}],
        "outcomes": [{"id": "o1", "label": "self-reported burnout", "tags": ["self-report"]}],
        "methods": [{"id": "m1", "label": "a survey", "requires_tags": ["self-report"], "excludes_tags": []}],
        "frames": [{"id": "f1", "label": "allostatic load theory", "tags": ["stress"]}],
    }
    total_valid = len(list(generator.all_valid_combinations(tiny_taxonomy)))
    assert total_valid == 1
    batch = generator.generate_batch(total_valid + 10, [], tiny_taxonomy, rng_seed=3)
    assert len(batch) == total_valid
