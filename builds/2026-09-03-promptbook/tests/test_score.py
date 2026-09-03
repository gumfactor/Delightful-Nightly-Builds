from src.episode import Episode
from src.score import score_episode


def test_empty_episode_scores_zero():
    assert score_episode(Episode()) == 0


def test_commit_only_scores_four():
    e = Episode(git_commit=True)
    assert score_episode(e) == 4


def test_test_pass_scores_three():
    e = Episode(test_run=True, test_passed=True)
    assert score_episode(e) == 3


def test_test_ambiguous_scores_one():
    e = Episode(test_run=True, test_passed=None)
    assert score_episode(e) == 1


def test_test_fail_scores_zero_bonus():
    e = Episode(test_run=True, test_passed=False)
    assert score_episode(e) == 0


def test_edit_with_no_error_scores_two():
    e = Episode(files_edited={"/x/f.py"}, unresolved_error=False)
    assert score_episode(e) == 2


def test_unresolved_error_scores_negative_three_clamped_to_zero():
    e = Episode(had_error=True, unresolved_error=True)
    assert score_episode(e) == 0


def test_full_success_combo_reaches_nine():
    # commit(+4) + test pass(+3) + edit no error(+2) = 9
    e = Episode(
        git_commit=True,
        test_run=True,
        test_passed=True,
        files_edited={"/x/a.py", "/x/b.py"},
        unresolved_error=False,
    )
    assert score_episode(e) == 9


def test_commit_plus_test_pass_reaches_seven():
    e = Episode(git_commit=True, test_run=True, test_passed=True)
    assert score_episode(e) == 7


def test_edit_during_unresolved_error_does_not_get_edit_bonus():
    e = Episode(files_edited={"/x/f.py"}, had_error=True, unresolved_error=True)
    # +0 for edit (unresolved_error is True) then -3 for the unresolved error, clamped to 0
    assert score_episode(e) == 0


def test_score_never_goes_below_zero():
    e = Episode(had_error=True, unresolved_error=True, test_run=True, test_passed=False)
    assert score_episode(e) == 0


def test_score_never_exceeds_ten():
    e = Episode(
        git_commit=True,
        test_run=True,
        test_passed=True,
        files_edited={"/x/a.py"},
        unresolved_error=False,
    )
    score = score_episode(e)
    assert 0 <= score <= 10
