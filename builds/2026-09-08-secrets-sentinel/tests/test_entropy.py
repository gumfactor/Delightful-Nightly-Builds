from src.entropy import (
    classify_token_charset,
    find_high_entropy_tokens,
    is_high_entropy,
    shannon_entropy,
)


def test_shannon_entropy_empty_string_is_zero():
    assert shannon_entropy("") == 0.0


def test_shannon_entropy_repeated_character_is_zero():
    assert shannon_entropy("aaaaaaaaaaaaaaaaaaaa") == 0.0


def test_shannon_entropy_random_looking_string_is_high():
    # 20 chars drawn from a genuinely mixed alphabet — well above the base64 threshold.
    token = "aB3xQ9zL7mK2pR8vN4wT"
    assert shannon_entropy(token) > 3.5


def test_classify_token_charset_hex():
    assert classify_token_charset("deadbeef1234567890abcdef12345678") == "hex"


def test_classify_token_charset_base64():
    assert classify_token_charset("aB3xQ9zL7mK2pR8vN4wT+/==") == "base64"


def test_classify_token_charset_none_for_non_matching():
    assert classify_token_charset("hello world! this has spaces") is None


def test_is_high_entropy_true_for_random_base64_like_token():
    assert is_high_entropy("k3Jd82jfQ0zLmXpR7vNwT9bY") is True


def test_is_high_entropy_false_for_short_token():
    assert is_high_entropy("aB3xQ9") is False


def test_is_high_entropy_false_for_repeated_hash_lookalike():
    assert is_high_entropy("0" * 40) is False


def test_is_high_entropy_false_for_snake_case_identifier():
    assert is_high_entropy("this_is_a_very_long_snake_case_function_name") is False


def test_find_high_entropy_tokens_extracts_candidate_from_line():
    line = 'AWS_SECRET = "k3Jd82jfQ0zLmXpR7vNwT9bYh8sQ2fLk"'
    tokens = find_high_entropy_tokens(line)
    assert "k3Jd82jfQ0zLmXpR7vNwT9bYh8sQ2fLk" in tokens


def test_find_high_entropy_tokens_empty_for_plain_english_line():
    line = "this function computes the average of a list of numbers"
    assert find_high_entropy_tokens(line) == []
