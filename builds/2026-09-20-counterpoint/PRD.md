# PRD — Counterpoint

> **Build date:** 2026-09-20
> **Category:** B — Productivity Utility
> **Complexity:** Ambitious Project
> **Day of week:** Sunday

---

## Goal

Turn a manuscript's raw peer-review comments plus the author's own point-by-point response notes into a complete, correctly-numbered "Response to Reviewers" letter — while deterministically guaranteeing every reviewer comment actually has a response before the letter is generated.

## User Story

As a researcher who regularly submits manuscripts for peer review and has to draft a "Response to Reviewers" letter for every revise-and-resubmit, I want to paste in the reviewers' raw comments and my own response notes and get back a properly structured, professionally worded letter with a completeness check, so that I never accidentally submit a response letter that silently skips a reviewer's point — the single most common way an R&R gets bounced back.

## Scope

### In Scope
- Deterministic parser for reviewer comment files: handles multiple reviewers (`Reviewer 1`, `REVIEWER #2`, Markdown headings), multiple numbered-comment styles (`1.` and `1)`), and multi-line comments (text continues until the next numbered item, next reviewer header, or end of file).
- Deterministic parser for a lightweight response file format (`[R1C1]` block markers followed by free-text response, one block per addressed comment).
- Completeness engine: cross-references every parsed comment ID against the response file, flags every comment with **no** response (never silently dropped), flags orphaned response keys that don't match any real comment (likely a renumbering mistake), and computes an addressed/total percentage.
- `check` command: prints a completeness report and exits non-zero if anything is missing — usable as a pre-submission gate, the same pattern as this repo's `dep-check --exit-on-outdated`.
- `build` command: renders the full letter in three formats — Markdown, a self-contained dark-mode HTML report with a completeness dashboard, and plain text for pasting directly into a journal's submission portal. Refuses to build (exit 1) when comments are missing responses unless `--force` is passed, in which case missing comments are rendered with a visible "NO RESPONSE PROVIDED" placeholder rather than being silently omitted.
- Optional AI polishing layer (`--ai`, requires a runtime `ANTHROPIC_API_KEY`): rewrites the author's raw response notes into courteous, publication-register prose for the letter. The AI is explicitly instructed to rephrase only — never to invent new claims, data, or justifications not present in the author's own notes. When `--ai` is not passed or no key is present, a deterministic formatter (whitespace cleanup, capitalization, terminal punctuation) is used instead and **zero** network calls are made — verified in tests via call-count assertions on an injected client factory.
- Full test suite covering parsing edge cases, completeness logic, the AI/fallback boundary, HTML escaping, and CLI exit codes.

### Out of Scope
- No manuscript diffing / line-number cross-referencing into the actual manuscript file (the author names the section themselves in their response text).
- No journal-specific formatting templates (APA/Nature/etc. citation or file-naming conventions) — output is a generic, universally-accepted point-by-point letter format.
- No live network calls in tests, ever — all Anthropic API usage is mocked.
- No GUI/browser interface — this is a CLI + generated static report, matching the pattern of prior Category B builds (CiteForge, GradeLine) rather than requiring a live web app for a document-generation task.

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None (stdlib `argparse`, `dataclasses`, `html`, `re`)
- **Dependencies:** `anthropic` (only required at runtime if `--ai` is used; the CLI runs fully without it installed as long as `--ai` is never passed)
- **Runtime requirement:** `python3 src/main.py check|build ...` — no install step required beyond `pip install -r requirements.txt` if `--ai` will be used

## Data Structure

**Input 1 — reviewer comments file (plain text/Markdown):**
```
## Reviewer 1

1. The authors should clarify the definition of X in the introduction.
2. Sample size justification is missing — please add a power analysis.

## Reviewer 2

1. Figure 3's axis labels are unreadable at print resolution.
```

**Input 2 — response file (custom lightweight block format, one file):**
```
[R1C1]
We have revised Section 2.1 to explicitly define X (see lines 45-52 of the
tracked-changes manuscript).

[R1C2]
We conducted a post-hoc power analysis (new Supplementary Table S1) confirming
adequate power (1-β = 0.82) at our observed effect size.

[R2C1]
Figure 3 has been redrawn with 14pt axis labels and bold tick marks.
```

**Internal model:**
- `Comment(id: str, reviewer_num: int, comment_num: int, text: str)` — `id` is always `R{n}C{m}`.
- `responses: dict[str, str]` — normalized uppercase key → raw response text.
- `CompletenessReport(total, addressed, missing: list[str], orphaned: list[str])` with a computed `percentage` property.

**Output:** `letter.md`, `letter.html`, `letter.txt` written to the `--out-dir` directory (default `output/`), plus the completeness report printed to stdout.

## Folder Structure

```
builds/2026-09-20-counterpoint/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── sample_data/
│   ├── reviewer_comments.md
│   └── responses.txt
├── src/
│   ├── __init__.py
│   ├── main.py            (CLI entry point: check / build subcommands)
│   ├── parser.py           (comment + response parsing, ParseError)
│   ├── response_matcher.py (CompletenessReport + matching logic)
│   ├── ai_polish.py        (deterministic fallback + optional Anthropic polish)
│   └── report.py           (Markdown / HTML / plain-text rendering)
└── tests/
    ├── test_parser.py
    ├── test_response_matcher.py
    ├── test_ai_polish.py
    ├── test_report.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Comment parsing across header/number-style variations, multi-line continuation, single-reviewer fallback (no header present), and hard failure modes (no comments found at all, duplicate comment IDs).
  - Response-file parsing (block markers, key normalization) and its own failure modes (no keys found, duplicate keys).
  - Completeness matching: fully addressed, missing responses, orphaned responses, percentage math on edge counts (0 comments, 100%, partial).
  - The AI/fallback boundary: deterministic fallback formatting is correct; the injected client factory is called with the expected prompt when `--ai` + a key are supplied; the client factory is called **zero** times when `--ai` is omitted (proving no network path is reachable); an exception from the (mocked) API degrades gracefully to the fallback text instead of crashing.
  - Report rendering: all comments/responses appear in Markdown and plain-text output; HTML output `html.escape`s user-supplied text (a `<script>`-bearing comment must not appear unescaped); missing comments are visually flagged in HTML.
  - CLI integration: `check` exits 0 when complete and 1 when incomplete; `build` refuses to write output when incomplete unless `--force`; `build` produces all three output files with correct content; running `build` without `--ai` never touches the injected Anthropic client factory.

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests, each covering a real failure mode.
2. `check` correctly identifies every missing and orphaned comment ID against the bundled `sample_data/` files and returns the correct exit code.
3. `build` (without `--ai`) generates a complete, correctly-ordered, human-readable letter in all three formats from the sample data with zero network calls.
4. HTML output is safe against injection from adversarial comment/response text (verified by a dedicated escaping test) and renders a completeness dashboard.
5. The AI-polish path is fully exercised via mocks (both success and failure branches) without ever making a real network call during the build or test run.

---

## Scope Changes

None — full scope as planned was completed.
