from src.text_case import to_sentence_case, to_title_case


def test_sentence_case_capitalizes_only_first_word():
    assert to_sentence_case("the effects of sleep on memory") == "The effects of sleep on memory"


def test_sentence_case_capitalizes_after_colon():
    result = to_sentence_case("the effects of sleep: a randomized trial")
    assert result == "The effects of sleep: A randomized trial"


def test_sentence_case_capitalizes_after_question_mark():
    result = to_sentence_case("what is memory? a review")
    assert result == "What is memory? A review"


def test_sentence_case_preserves_acronyms():
    result = to_sentence_case("HIV-infected patients and their treatment")
    assert result == "HIV-infected patients and their treatment"


def test_sentence_case_preserves_internal_capitals():
    result = to_sentence_case("a case report on mRNA vaccines")
    assert result == "A case report on mRNA vaccines"


def test_sentence_case_real_world_title_is_idempotent():
    title = "Solid-organ transplantation in HIV-infected patients"
    assert to_sentence_case(title) == title


def test_sentence_case_empty_string():
    assert to_sentence_case("") == ""


def test_sentence_case_single_word():
    assert to_sentence_case("MEMORY") == "MEMORY"  # already all-caps -> protected acronym


def test_title_case_lowercases_minor_words():
    result = to_title_case("the effects of sleep on memory")
    assert result == "The Effects of Sleep on Memory"


def test_title_case_always_capitalizes_first_and_last_word():
    result = to_title_case("a study of the mind")
    assert result == "A Study of the Mind"


def test_title_case_capitalizes_word_after_colon():
    result = to_title_case("thinking fast: a review of judgment")
    assert result == "Thinking Fast: A Review of Judgment"


def test_title_case_book_title_worked_example():
    result = to_title_case("thinking, fast and slow")
    assert result == "Thinking, Fast and Slow"


def test_title_case_preserves_acronyms():
    result = to_title_case("a study of DNA and RNA structure")
    assert result == "A Study of DNA and RNA Structure"


def test_title_case_empty_string():
    assert to_title_case("") == ""
