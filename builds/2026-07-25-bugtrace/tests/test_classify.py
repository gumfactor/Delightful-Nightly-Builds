from src.classify import TAXONOMY, keyword_classify


def test_test_only_fix_detected_via_changed_files():
    category, _ = keyword_classify(
        "fix flaky assertion", "diff content", changed_files=["tests/test_foo.py"]
    )
    assert category == "test_only_fix"


def test_config_env_credentials():
    category, _ = keyword_classify(
        "fix: read API key from environment variable instead of hardcoding", "", []
    )
    assert category == "config_env_credentials"


def test_dependency_version():
    category, _ = keyword_classify("fix: bump requests dependency to patch CVE", "", [])
    assert category == "dependency_version"


def test_async_race_condition():
    category, _ = keyword_classify("fix race condition in async worker queue", "", [])
    assert category == "async_race_condition"


def test_off_by_one_index():
    category, _ = keyword_classify(
        "fix off-by-one error causing IndexError on last page", "", []
    )
    assert category == "off_by_one_index"


def test_null_none_handling():
    category, _ = keyword_classify(
        "fix NoneType attribute error on missing user record", "", []
    )
    assert category == "null_none_handling"


def test_type_mismatch():
    category, _ = keyword_classify("fix TypeError when comparing string to int", "", [])
    assert category == "type_mismatch"


def test_logic_operator_error():
    category, _ = keyword_classify(
        "fix inverted boolean check that skipped valid entries", "", []
    )
    assert category == "logic_operator_error"


def test_error_handling_missing():
    category, _ = keyword_classify(
        "add missing try/except around network call to prevent uncaught crash", "", []
    )
    assert category == "error_handling_missing"


def test_api_integration_misuse():
    category, _ = keyword_classify(
        "fix API endpoint returning 500 error on empty payload", "", []
    )
    assert category == "api_integration_misuse"


def test_typo_naming():
    category, _ = keyword_classify(
        "fix typo in variable name causing wrong lookup", "", []
    )
    assert category == "typo_naming"


def test_other_fallback():
    category, _ = keyword_classify("fix minor UI alignment issue", "", [])
    assert category == "other"


def test_always_returns_taxonomy_member():
    for message in ["fix bug", "fix crash", "", "patch it"]:
        category, explanation = keyword_classify(message, "", [])
        assert category in TAXONOMY
        assert isinstance(explanation, str) and explanation
