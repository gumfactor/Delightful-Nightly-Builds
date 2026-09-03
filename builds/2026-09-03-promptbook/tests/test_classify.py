from src.classify import classify


def test_bug_fix():
    assert classify("There's a bug in the login flow, please fix it") == "bug-fix"


def test_test_type():
    assert classify("Please write unit tests for the parser module") == "test"


def test_docs():
    assert classify("Add a docstring explaining this function") == "docs"


def test_config():
    assert classify("Set up the environment variables for staging") == "config"


def test_review():
    assert classify("Please review this pull request and give feedback") == "review"


def test_refactor():
    assert classify("Refactor this module to simplify the logic") == "refactor"


def test_research():
    assert classify("Explain why this function returns None") == "research"


def test_feature():
    assert classify("Please implement an endpoint for user signup") == "feature"


def test_other_default():
    assert classify("What's the weather like today") == "other"


def test_bug_fix_takes_priority_over_feature_language():
    # Contains both "add" (feature-ish) and "fix"/"bug" language; bug-fix must win.
    assert classify("Add a fix for the crash bug in the parser") == "bug-fix"


def test_classification_is_case_insensitive():
    assert classify("PLEASE FIX THE BROKEN BUILD") == "bug-fix"


def test_empty_string_defaults_to_other():
    assert classify("") == "other"


def test_feature_with_stacked_modifiers():
    # "a new" stacks two modifier words before the noun — must still classify as feature.
    assert classify("Please add a new endpoint for user signup") == "feature"
