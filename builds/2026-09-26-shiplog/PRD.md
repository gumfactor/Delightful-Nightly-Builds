# PRD — Shiplog

> **Build date:** 2026-09-26
> **Category:** H — Developer Tool
> **Complexity:** Ambitious
> **Day of week:** Saturday

---

## Goal

Generate a categorized, deduplicated, human-readable changelog (with a suggested semver bump) from a local git repository's commit history, with an optional AI-polished prose summary and a self-contained HTML velocity report.

## User Story

As a solo founder and lab director who maintains several actively-developed repositories (The Canada List, Kwyeter, this nightly-build repo) between occasional review passes, I want to point a tool at a repo and a commit range and get back a structured, readable changelog instead of a raw `git log`, so that I can write release notes, catch what actually shipped, and decide what needs a version bump without re-reading every commit message by hand.

## Scope

### In Scope
- A Python CLI (`shiplog generate <path> [--since <ref-or-date>] [--until <ref>] [--format md|html|both] [--out <dir>] [--ai-polish] [--github-token-env <VAR>]`) that reads a local git repo's commit history via read-only `git log` subprocess calls (never mutates the target repo).
- A conventional-commit parser: `type(scope)!: subject` / `type(scope): subject` / `type!: subject`, extracting `type`, optional `scope`, `breaking` flag (`!` or a `BREAKING CHANGE:` footer), and `subject`.
- A deterministic keyword-based fallback classifier for any commit that isn't conventional-commit-formatted (maps common verbs/nouns to `feat`/`fix`/`docs`/`chore`/`refactor`/`perf`/`test`/`ci`/`build`/`other`).
- Revert/re-revert cancellation: a commit whose subject matches `^Revert "..."` is matched against the commit it reverts (by quoted subject text); if both the original and its revert are within the selected range, both are dropped from the changelog as net-zero noise (and reported as cancelled in a summary line).
- Merge-commit PR-number extraction (`Merge pull request #123 from ...`) with **optional** enrichment: if `GITHUB_TOKEN` is set in the environment and `--repo owner/name` is supplied, fetch each referenced PR's title/labels from the GitHub REST API and prefer the PR title over the merge commit subject when classifying. Works with zero network calls when no token/repo is supplied (falls back to commit-message-only classification).
- Semver-bump suggestion: any `breaking` commit → `major`; else any `feat` → `minor`; else any `fix`/`perf` → `patch`; else `none`.
- Grouped output sections: Breaking Changes, Features, Fixes, Other (chore/refactor/perf/test/ci/build merged under "Maintenance"), Uncategorized (only if the keyword classifier truly can't place a commit) — with a count of cancelled revert pairs shown separately.
- Markdown output: a `CHANGELOG_<range>.md` fragment the user can paste into a project's `CHANGELOG.md`.
- HTML output: a self-contained dark-mode report (`report_<range>.html`) with the same grouped sections, a Chart.js bar chart of commit-type counts, and the suggested version bump shown as a banner. No external calls at view time — all data is inlined as JSON in a `<script>` tag with `</` escaped.
- Optional `--ai-polish`: when `ANTHROPIC_API_KEY` is set, sends only the already-classified structure (type, scope, subject, breaking flag — never diffs, file paths, or file contents) to Claude Haiku to write a short cohesive prose paragraph per non-empty section. Deterministic fallback (plain bulleted list of subjects, already-classified) is used whenever the key is absent or the API call fails for any reason.
- A companion Claude Code Skill (`skill/SKILL.md`) so the tool can be invoked as `/shiplog <path> [range]` inside a coding session, per PROFILE.md's stated preference for pull-tools over scripts the user must remember to run.
- `requirements.txt`, type hints throughout, `if __name__ == "__main__":` guard.

### Out of Scope
- Writing back to the target repo (no tagging, no committing a generated `CHANGELOG.md` automatically — the user reviews and pastes it in).
- Support for non-git version control systems.
- A hosted/scheduled version that runs automatically on push (this build is invoked on demand; a Routine/Hook wrapper is a natural `FutureFeatures.md` extension, not tonight's scope).
- Multi-repo aggregation in one run (one repo per invocation; the Skill can be called once per repo).

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None (stdlib `subprocess`, `argparse`, `re`, `json`, `dataclasses`, `urllib.request` for the optional GitHub/Anthropic HTTP calls)
- **Dependencies:** stdlib only for the core engine and CLI; Chart.js 4.4.4 via CDN for the HTML report's chart (no local JS dependency to install)
- **Runtime requirement:** `python3 src/shiplog.py generate <repo-path> [options]` — no install step beyond stdlib

## Data Structure

Each parsed commit becomes a `Commit` dataclass:

```python
@dataclass
class Commit:
    sha: str
    subject: str
    body: str
    author_date: str        # ISO 8601, from git
    type: str                # feat|fix|docs|chore|refactor|perf|test|ci|build|revert|other
    scope: str | None
    breaking: bool
    pr_number: int | None
    source: str               # "conventional" | "keyword" | "github-pr"
```

A `ChangelogResult` dataclass holds: `sections: dict[str, list[Commit]]`, `cancelled_pairs: list[tuple[Commit, Commit]]`, `suggested_bump: str`, `range_label: str`, `total_commits: int`.

No persistent storage — each run is stateless over the git history in the given range; Markdown/HTML files are written to `--out` (default: the target repo's working directory is never touched — output defaults to the current directory the tool was invoked from, or `--out` if given, never inside the target repo unless explicitly requested).

## Folder Structure

```
builds/2026-09-26-shiplog/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── shiplog.py           (CLI entry point)
│   ├── git_log.py           (read-only git log subprocess wrapper)
│   ├── classify.py          (conventional-commit parser + keyword fallback + revert cancellation)
│   ├── github_enrich.py     (optional PR-title enrichment via GITHUB_TOKEN)
│   ├── semver.py            (bump suggestion)
│   ├── ai_polish.py         (optional Claude Haiku prose polish + deterministic fallback)
│   └── render.py            (Markdown + HTML rendering)
├── skill/
│   └── SKILL.md
└── tests/
    ├── test_classify.py
    ├── test_semver.py
    ├── test_github_enrich.py
    ├── test_ai_polish.py
    ├── test_render.py
    └── test_shiplog_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Conventional-commit parsing: type/scope/breaking-flag/subject extraction for all documented formats, including `!` and `BREAKING CHANGE:` footer variants.
  - Keyword fallback classifier: representative commits for each category, plus a genuinely unclassifiable message routed to "other".
  - Revert/re-revert cancellation: matching pair removed and counted; an unmatched revert (original commit outside range) is kept, not incorrectly cancelled.
  - Merge-commit PR-number extraction regex, including messages that aren't merge commits (no false match).
  - GitHub PR enrichment: mocked HTTP call returning a PR title/labels, used only when `GITHUB_TOKEN` + `--repo` are both supplied; falls back cleanly to commit-message classification when the mocked call raises/returns non-200; zero real network calls in tests.
  - Semver bump suggestion for every priority case (breaking > feat > fix/perf > none) and the "no commits" edge case.
  - AI polish: mocked Anthropic call producing prose used verbatim; a mocked failure/timeout falls back to the deterministic bullet list; no call is made at all when the API key is absent (asserted via a call-count spy).
  - Markdown rendering: correct section headers, cancelled-pair note, omission of empty sections.
  - HTML rendering: valid self-contained document, JSON payload correctly escapes `</script>`, no `innerHTML` of user-controlled text.
  - End-to-end CLI test against a small real git repo built in a pytest tmp_path fixture (real `git init`/`git commit` calls, not mocks — this is local, not an external API) covering the full generate flow and file output.
  - Error handling: non-git directory, empty repo (0 commits in range), invalid `--since`/`--until` ref.

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests.
2. Running `generate` against a real local git repo with a mix of conventional and non-conventional commits, including one revert/re-revert pair, produces a Markdown changelog with the pair correctly cancelled and omitted.
3. The suggested semver bump is correct for at least three constructed scenarios (breaking-only, feat-only, fix-only) with a dedicated test per scenario.
4. With no `ANTHROPIC_API_KEY` set, `--ai-polish` produces the deterministic fallback output and makes zero network calls (verified by a call-count spy in tests).
5. The generated HTML report is a single self-contained file (no external file dependencies besides the pinned Chart.js CDN `<script src>`), opens correctly, and contains zero `innerHTML` assignments in the shipped source (grep-verified).

---

## Scope Changes

(none yet — filled in during the build if scope changes)
