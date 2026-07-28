from src import heuristics


def test_find_ai_tell_phrases_detects_known_phrase_with_line_and_excerpt():
    text = "Line one is clean.\nLet's delve into the details here."
    hits = heuristics.find_ai_tell_phrases(text)
    assert len(hits) == 1
    assert hits[0]["phrase"] == "delve into"
    assert hits[0]["line"] == 2
    assert "delve into" in hits[0]["excerpt"].lower()


def test_find_ai_tell_phrases_negative_fixture_has_no_hits():
    text = "The cat sat on the warm windowsill and watched the rain fall outside."
    assert heuristics.find_ai_tell_phrases(text) == []


def test_find_ai_tell_phrases_counts_multiple_occurrences():
    text = "This is robust. That is also robust. Everything here is robust."
    hits = heuristics.find_ai_tell_phrases(text)
    assert len(hits) == 3


def test_count_em_dashes_positive_and_negative():
    assert heuristics.count_em_dashes("A thought—interrupted—finished.") == 2
    assert heuristics.count_em_dashes("A thought, interrupted, finished.") == 0


def test_count_semicolons_positive_and_negative():
    assert heuristics.count_semicolons("One; two; three.") == 2
    assert heuristics.count_semicolons("One, two, three.") == 0


def test_find_hedge_words_detects_and_ignores_clean_text():
    assert sorted(heuristics.find_hedge_words("This might possibly work, perhaps.")) == sorted(
        ["might", "possibly", "perhaps"]
    )
    assert heuristics.find_hedge_words("This will work.") == []


def test_find_passive_voice_detects_auxiliary_plus_past_participle():
    matches = heuristics.find_passive_voice("The results were tested and the data was analyzed.")
    assert len(matches) == 2


def test_find_passive_voice_negative_fixture():
    matches = heuristics.find_passive_voice("The team tested the results and analyzed the data.")
    assert matches == []


def test_find_rule_of_three_detects_triad_pattern():
    matches = heuristics.find_rule_of_three(
        "The system is fast, reliable, and secure for every workload."
    )
    assert len(matches) == 1


def test_find_rule_of_three_negative_fixture():
    matches = heuristics.find_rule_of_three("The system is fast for every workload.")
    assert matches == []


def test_sentence_lengths_splits_on_terminal_punctuation():
    lengths = heuristics.sentence_lengths("This is short. Here are six total words now.")
    assert lengths == [3, 6]


def test_sentence_lengths_empty_text_returns_empty_list():
    assert heuristics.sentence_lengths("   ") == []


def test_burstiness_high_variance_prose():
    lengths = heuristics.sentence_lengths(
        "Go. The rain fell steadily through the entire cold and grey afternoon, soaking everything. Wait."
    )
    result = heuristics.burstiness(lengths)
    assert result["cv"] > 0.3


def test_burstiness_uniform_sentence_lengths_has_low_cv():
    lengths = [6, 6, 6, 6, 6, 6]
    result = heuristics.burstiness(lengths)
    assert result["cv"] == 0.0


def test_burstiness_handles_fewer_than_two_sentences():
    assert heuristics.burstiness([]) == {"mean": 0.0, "stdev": 0.0, "cv": 0.0}
    assert heuristics.burstiness([5]) == {"mean": 5.0, "stdev": 0.0, "cv": 0.0}


def test_type_token_ratio_repetitive_text_is_low():
    ratio = heuristics.type_token_ratio("test test test test test")
    assert ratio == 1 / 5


def test_type_token_ratio_varied_text_is_higher():
    ratio = heuristics.type_token_ratio("the quick brown fox jumps over a lazy dog")
    assert ratio == 1.0


def test_type_token_ratio_empty_text_returns_one():
    assert heuristics.type_token_ratio("") == 1.0


def test_find_repeated_paragraph_openers_flags_three_or_more():
    text = "The lab studies stress.\n\nThe lab studies empathy.\n\nThe lab studies psychopathy.\n\nMeanwhile funding continues."
    openers = heuristics.find_repeated_paragraph_openers(text)
    assert openers == [{"word": "the", "count": 3}]


def test_find_repeated_paragraph_openers_negative_fixture():
    text = "The lab studies stress.\n\nFunding remains steady.\n\nStudents are engaged."
    assert heuristics.find_repeated_paragraph_openers(text) == []


def test_analyze_text_returns_all_expected_keys():
    result = heuristics.analyze_text("This is a simple, clear, and direct paragraph about research.")
    expected_keys = {
        "word_count",
        "sentence_count",
        "sentence_lengths",
        "ai_tell_hits",
        "em_dash_count",
        "semicolon_count",
        "hedge_hits",
        "passive_matches",
        "rule_of_three_matches",
        "burstiness",
        "type_token_ratio",
        "repeated_openers",
        "paragraphs",
    }
    assert expected_keys.issubset(result.keys())


def test_analyze_text_handles_empty_input_without_crashing():
    result = heuristics.analyze_text("")
    assert result["word_count"] == 0
    assert result["ai_tell_hits"] == []
    assert result["sentence_count"] == 0
