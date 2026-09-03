"""Deterministic 0-10 effectiveness score from an episode's signals.

Formula (each branch hand-verified against a reference case in tests/test_score.py):
  base 0
  +4  a git commit happened in the episode
  +3  a test-runner command ran AND a pass signal was detected
  +1  a test-runner command ran with no clear pass/fail signal
  +2  at least one file was edited and there is no unresolved error
  -3  an error occurred with no successful edit/test-pass/commit afterward (unresolved)
  clamped to [0, 10]

Max achievable (commit + passing tests + a clean edit) is 9, leaving room above it so the
[0, 10] clamp is a real safety bound rather than dead code, and "7+" reads as a genuinely
high bar (only reachable by combining at least two strong signals).
"""
from __future__ import annotations

from src.episode import Episode


def score_episode(episode: Episode) -> int:
    total = 0

    if episode.git_commit:
        total += 4

    if episode.test_run:
        if episode.test_passed is True:
            total += 3
        elif episode.test_passed is None:
            total += 1
        # test_passed is False: no bonus, but not itself a penalty beyond the
        # unresolved-error branch below (a known-failing test isn't an error).

    if episode.files_edited and not episode.unresolved_error:
        total += 2

    if episode.unresolved_error:
        total -= 3

    return max(0, min(10, total))
