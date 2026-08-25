"""Reusability scorer tests.

Each test builds its input from a plain "filler" word list so the exact
word count is known by construction, then hand-computes the expected
score from the documented rules in src/scorer.py:

    score = 5
            + length_adjustment      (+2 if 40<=n<=250, -2 if n<15, -1 if n>400, else 0)
            + specificity_adjustment (-4 if >=3 signal categories, -3 if 2, -1 if 1, else 0)
            + generic_bonus          (+1 if a generic/transferable keyword is present)
    clamped to [0, 10]; tier = High >=7, Medium 4-6, Low <4.
"""

from src.scorer import score_reusability


def test_generic_transferable_chunk_scores_high():
    # 45 filler words (in the 40-250 band, +2) plus "framework" (generic
    # bonus, +1), zero specificity signals: 5 + 2 + 0 + 1 = 8 -> High.
    text = "framework " + "word " * 44
    score, tier = score_reusability(text.strip())
    assert score == 8
    assert tier == "High"


def test_specificity_anchored_chunk_scores_low():
    # 46 words in the 40-250 band (+2) but with all three specificity
    # signal categories present (dollar, year, name-like phrase): -4.
    # No generic keyword: 5 + 2 - 4 + 0 = 3 -> Low.
    words = ["filler"] * 42 + ["$50,000", "2027", "Example", "Institute"]
    text = " ".join(words)
    score, tier = score_reusability(text)
    assert score == 3
    assert tier == "Low"


def test_score_seven_is_high_boundary():
    # 45 filler words, no signals, no generic keyword: 5 + 2 + 0 + 0 = 7.
    text = "word " * 45
    score, tier = score_reusability(text.strip())
    assert score == 7
    assert tier == "High"


def test_score_six_is_medium_boundary():
    # 45 words including one year (one signal category, -1), no dollar,
    # no name-like phrase, no generic keyword: 5 + 2 - 1 + 0 = 6.
    words = ["filler"] * 44 + ["2027"]
    text = " ".join(words)
    score, tier = score_reusability(text)
    assert score == 6
    assert tier == "Medium"


def test_score_four_is_medium_lower_boundary():
    # 9 words (<15, -2) with a generic keyword (+1), no specificity
    # signals: 5 - 2 + 0 + 1 = 4.
    text = "framework " + "word " * 8
    score, tier = score_reusability(text.strip())
    assert score == 4
    assert tier == "Medium"


def test_very_short_chunk_penalized():
    # 5 words (<15, -2), no signals, no generic bonus: 5 - 2 = 3 -> Low.
    text = "one two three four five"
    score, tier = score_reusability(text)
    assert score == 3
    assert tier == "Low"


def test_very_long_chunk_slightly_penalized():
    # 450 filler words (>400, -1), no signals, no generic bonus: 5-1=4.
    text = "word " * 450
    score, tier = score_reusability(text.strip())
    assert score == 4
    assert tier == "Medium"


def test_score_clamped_at_zero():
    # 7 words (<15, -2) with all three specificity signals present (-4):
    # 5 - 2 - 4 + 0 = -1, clamped to 0 -> Low.
    words = ["$5", "2027", "Example", "Institute", "x", "y", "z"]
    text = " ".join(words)
    score, tier = score_reusability(text)
    assert score == 0
    assert tier == "Low"


def test_empty_chunk_returns_zero_low():
    score, tier = score_reusability("")
    assert score == 0
    assert tier == "Low"
    score, tier = score_reusability("   ")
    assert score == 0
    assert tier == "Low"


def test_two_specificity_categories_apply_medium_penalty():
    # 45 words with a dollar amount and a year but no name-like phrase
    # (2 categories, -3), no generic keyword: 5 + 2 - 3 + 0 = 4.
    words = ["filler"] * 43 + ["$50,000", "2027"]
    text = " ".join(words)
    score, tier = score_reusability(text)
    assert score == 4
    assert tier == "Medium"
