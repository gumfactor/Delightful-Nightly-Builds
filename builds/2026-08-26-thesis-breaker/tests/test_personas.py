from src.rules import RuleResult
from src.personas import score_persona, score_all_personas, overall_score


def r(key, fired, label=None):
    return RuleResult(key, label or key, fired, f"detail for {key}")


def test_value_skeptic_scores_from_weighted_categories():
    results = [
        r("valuation_stretch", True),
        r("growth_deceleration", False),
        r("margin_debt_risk", True),
        r("insider_selling", True),
        r("narrative_fragility", False),
    ]
    score = score_persona("value_skeptic", results)
    # weights: valuation_stretch=3 (fired), narrative_fragility=2 (not fired), growth_deceleration=1 (not fired)
    # margin_debt_risk and insider_selling have weight 0 for this persona
    assert score.score == round(100 * 3 / 6)


def test_persona_ignores_zero_weighted_categories():
    results = [r("insider_selling", True)]  # value_skeptic weights this 0
    score = score_persona("value_skeptic", results)
    assert score.score is None  # nothing weighted was evaluable


def test_persona_score_none_when_all_weighted_categories_unavailable():
    results = [
        r("valuation_stretch", None),
        r("growth_deceleration", None),
        r("narrative_fragility", None),
    ]
    score = score_persona("value_skeptic", results)
    assert score.score is None
    assert len(score.unavailable) == 3


def test_persona_categorizes_fired_and_not_fired_lists():
    results = [
        r("insider_selling", True),
        r("narrative_fragility", False),
        r("margin_debt_risk", True),
    ]
    score = score_persona("governance_hawk", results)
    assert [f.key for f in score.fired] == ["insider_selling", "margin_debt_risk"]
    assert [f.key for f in score.not_fired] == ["narrative_fragility"]


def test_score_all_personas_returns_three():
    results = [r("valuation_stretch", True), r("growth_deceleration", True)]
    scores = score_all_personas(results)
    assert len(scores) == 3
    assert {s.key for s in scores} == {"value_skeptic", "macro_bear", "governance_hawk"}


def test_overall_score_averages_valid_persona_scores():
    from src.personas import PersonaScore
    scores = [
        PersonaScore("a", "A", 60, [], [], []),
        PersonaScore("b", "B", 40, [], [], []),
        PersonaScore("c", "C", None, [], [], []),
    ]
    assert overall_score(scores) == 50


def test_overall_score_none_when_all_personas_unscored():
    from src.personas import PersonaScore
    scores = [PersonaScore("a", "A", None, [], [], [])]
    assert overall_score(scores) is None
