from src import heuristics, scoring


def _analysis_for(text: str) -> dict:
    return heuristics.analyze_text(text)


def test_clean_varied_prose_scores_at_or_near_100():
    text = (
        "Rain hammered the tin roof all night. By morning the creek had crept up over "
        "the gravel path, and the dog refused to go outside. We waited. Eventually the "
        "sun broke through, and the whole yard steamed."
    )
    analysis = _analysis_for(text)
    result = scoring.compute_score(analysis)
    assert result["score"] == 100.0
    assert result["flag_count"] == 0


def test_heavily_flagged_text_scores_lower_than_clean_text():
    flagged = (
        "It's important to note that, moreover, we must delve into the tapestry of "
        "seamless, robust synergies. Furthermore, this testament to leveraging a "
        "holistic paradigm shift cannot be overstated. In conclusion, it's worth "
        "noting the myriad of intricacies."
    )
    clean = "Rain hammered the tin roof all night, and the dog refused to go outside."
    flagged_score = scoring.compute_score(_analysis_for(flagged))["score"]
    clean_score = scoring.compute_score(_analysis_for(clean))["score"]
    assert flagged_score < clean_score


def test_removing_ai_tell_phrases_strictly_increases_score():
    before = "We need to delve into this. We should also leverage seamless synergy here."
    after = "We need to examine this closely. We should also combine these systems well."
    before_score = scoring.compute_score(_analysis_for(before))["score"]
    after_score = scoring.compute_score(_analysis_for(after))["score"]
    assert after_score > before_score


def test_score_is_deterministic_across_repeated_calls():
    analysis = _analysis_for("This is a plain sentence about the weather today.")
    first = scoring.compute_score(analysis)
    second = scoring.compute_score(analysis)
    assert first == second


def test_empty_text_handled_without_crash():
    analysis = _analysis_for("")
    result = scoring.compute_score(analysis)
    assert result["score"] == 100.0
    assert result["flag_count"] == 0


def test_score_never_goes_below_zero_even_with_extreme_penalties():
    fake_analysis = {
        "word_count": 100,
        "ai_tell_hits": [{"phrase": "x", "line": 1, "excerpt": "x"}] * 100,
        "em_dash_count": 1000,
        "semicolon_count": 1000,
        "hedge_hits": ["might"] * 1000,
        "passive_matches": ["was tested"] * 1000,
        "rule_of_three_matches": ["a, b, and c"] * 100,
        "sentence_count": 10,
        "burstiness": {"cv": 0.0, "mean": 5.0, "stdev": 0.0},
        "type_token_ratio": 0.01,
        "repeated_openers": [{"word": "the", "count": 100}],
    }
    result = scoring.compute_score(fake_analysis)
    assert result["score"] == 0.0


def test_score_never_exceeds_100():
    fake_analysis = {
        "word_count": 0,
        "ai_tell_hits": [],
        "em_dash_count": 0,
        "semicolon_count": 0,
        "hedge_hits": [],
        "passive_matches": [],
        "rule_of_three_matches": [],
        "sentence_count": 0,
        "burstiness": {"cv": 0.0, "mean": 0.0, "stdev": 0.0},
        "type_token_ratio": 1.0,
        "repeated_openers": [],
    }
    result = scoring.compute_score(fake_analysis)
    assert result["score"] == 100.0


def test_breakdown_contains_expected_categories():
    analysis = _analysis_for("A short, plain sentence.")
    result = scoring.compute_score(analysis)
    expected = {
        "ai_tell_phrases",
        "em_dash_density",
        "semicolon_density",
        "hedge_density",
        "passive_voice",
        "rule_of_three",
        "low_burstiness",
        "low_vocabulary_diversity",
        "repeated_paragraph_openers",
    }
    assert expected.issubset(result["breakdown"].keys())
