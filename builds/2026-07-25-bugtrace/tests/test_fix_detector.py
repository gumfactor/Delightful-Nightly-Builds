from src.fix_detector import is_fix_commit


def test_positive_fix_keywords():
    assert is_fix_commit("Fix null pointer crash on empty input")
    assert is_fix_commit("fixed bug in CSV parser")
    assert is_fix_commit("resolve race condition in worker pool")
    assert is_fix_commit("patch security hole in auth check")
    assert is_fix_commit("correct off-by-one error in pagination")
    assert is_fix_commit("Fix typo in README")


def test_merge_commits_excluded_even_with_fix_keyword():
    assert not is_fix_commit('Merge pull request #12 from feature/fix-crash')


def test_revert_commits_excluded_even_with_fix_keyword():
    assert not is_fix_commit('Revert "fix bug in parser"')


def test_unrelated_commits_are_not_fixes():
    assert not is_fix_commit("Add new dashboard widget")
    assert not is_fix_commit("Update documentation")
    assert not is_fix_commit("Refactor request handler for clarity")


def test_empty_message_is_not_a_fix():
    assert not is_fix_commit("")
    assert not is_fix_commit("   ")


def test_only_first_line_considered():
    message = "Add feature X\n\nfix bug in unrelated body text"
    assert not is_fix_commit(message)
