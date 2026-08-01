# PRD — ItemScope

> **Build date:** 2026-08-01
> **Category:** F — Data Explorer
> **Complexity:** Ambitious
> **Day of week:** Saturday

---

## Goal

Turn a CSV of student-by-item exam or quiz responses into a classical-test-theory item-analysis report (difficulty, discrimination, distractor health, test reliability) with a flagged-item action list and a self-contained HTML dashboard.

## User Story

As a professor who writes and grades exams and quizzes across multiple courses each term, I want to paste in my item-level response export and immediately see which items were too easy, too hard, poorly discriminating, or had broken answer choices, so that I can revise or retire weak items before the next time I use the exam — without manually computing point-biserial correlations and KR-20 in a spreadsheet.

## Scope

### In Scope
- CLI (`itemscope analyze`) that reads a CSV of per-item, per-student responses. Two supported input shapes:
  1. **Binary-scored**: one column per item, values are 0/1 (or True/False, or correct/incorrect strings) — most common LMS/Scantron export.
  2. **Raw-option**: one column per item, values are the option letter the student selected (A/B/C/D/...), paired with a separate one-row answer key (CSV or inline `--key`) so ItemScope can score it itself and also run distractor analysis.
- Column auto-detection: first column assumed to be a student identifier if it's non-numeric/non-binary; everything else treated as an item column, with graceful handling if a `--student-id-col` is passed explicitly.
- Per-item statistics: difficulty (p-value = proportion correct), point-biserial discrimination (item score vs. corrected total — total score minus that item), and for raw-option input, the % of students selecting each option split by top/bottom 27% scorers (upper-lower index) to flag non-functioning distractors (an incorrect option nobody picks) and items where a distractor out-pulls the keyed answer among top scorers.
- Test-level statistics: KR-20 (binary items) reliability, mean score, SD, SEM, min/max.
- Flagging rules (all thresholds are named constants, not hardcoded magic numbers): too easy (p > 0.95), too hard (p < 0.20), poor discrimination (r < 0.15), negative discrimination (r < 0), non-functioning distractor (an incorrect option, present somewhere in the observed data, chosen by 0% of both the upper-27% and lower-27% scoring groups — the classic upper-lower technique's definition of a distractor that isn't discriminating), reversed distractor pull (an incorrect option chosen by a *higher* proportion of the upper-scoring group than the lower-scoring group — the opposite of what a well-functioning distractor should do).
- Edge-case handling: zero-variance items (p = 0 or p = 1) report point-biserial as "undefined (zero variance)" instead of crashing or producing NaN; single-item inputs report KR-20 as "not meaningful for a single item" instead of dividing by zero; small classes (fewer than ~8 students, so upper/lower 27% would be 0-2 people) still compute an upper/lower split on whatever N is available but label it "small-N — interpret cautiously" in the report.
- Output modes: `--format text` (colored terminal summary), `--format json` (machine-readable), `--format html` (default; self-contained dark-mode dashboard with a difficulty-vs-discrimination quadrant scatter plot drawn in native Canvas 2D — no CDN dependency — plus a sortable/searchable per-item table and a flagged-items panel).
- Optional AI layer: `--ai` flag (or auto-enabled when `ANTHROPIC_API_KEY` is set) sends only the aggregated per-item statistics (p-value, discrimination, flag reasons — never raw student responses or names) for the worst-scoring items to Claude Haiku for a plain-English revision suggestion. A deterministic template-based suggestion (keyed off which flag(s) fired) is always generated first and used whenever no key is set or the API call fails, so the tool is fully functional offline.
- `requirements.txt` (stdlib only — empty file with a comment, since no third-party packages are used).

### Out of Scope
- Multi-page/multi-test longitudinal tracking across semesters (a single `analyze` run per file tonight; no persistence layer).
- Automatic parsing of proprietary Scantron binary formats — CSV export only.
- Partial-credit / polytomous item scoring (e.g., short-answer rubric scores 0-5) — binary correct/incorrect and single-best-answer MCQ only.
- Real student names or IDs ever leaving the machine — the optional AI call sends only aggregated numeric statistics per item, never a response matrix or identifiers.

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** stdlib only (`csv`, `argparse`, `json`, `html`, `statistics`, `urllib.request` for the optional Anthropic call)
- **Runtime requirement:** `python3 src/itemscope/cli.py analyze responses.csv` (no install needed beyond Python 3.9+)

## Data Structure

Input CSV, binary-scored example:
```
student_id,item_1,item_2,item_3
S001,1,0,1
S002,1,1,1
S003,0,0,1
```

Input CSV, raw-option example (with `--key key.csv` where key.csv is `item,answer` rows):
```
student_id,item_1,item_2,item_3
S001,A,C,B
S002,A,A,B
S003,B,C,D
```

Internal representation: a `ResponseMatrix` (list of student IDs, list of item IDs, 2D list of raw cell values) is parsed once, then scored into a `ScoredMatrix` (2D list of 0/1) regardless of input shape, which everything downstream (stats, flags, report) consumes uniformly.

Output JSON schema (illustrative):
```json
{
  "n_students": 42,
  "n_items": 20,
  "reliability_kr20": 0.78,
  "mean_score": 14.3,
  "items": [
    {"item_id": "item_1", "p_value": 0.85, "discrimination": 0.42, "flags": []},
    {"item_id": "item_7", "p_value": 0.98, "discrimination": -0.05, "flags": ["too_easy", "negative_discrimination"]}
  ]
}
```

## Folder Structure

```
builds/2026-08-01-itemscope/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── sample_data/
│   ├── responses_binary.csv
│   ├── responses_raw.csv
│   └── answer_key.csv
├── src/
│   └── itemscope/
│       ├── __init__.py
│       ├── parser.py       (CSV/response-matrix loading, column auto-detection)
│       ├── stats.py        (p-value, point-biserial, KR-20, distractor analysis, flags)
│       ├── report.py       (text/JSON/HTML renderers)
│       ├── ai.py           (optional Claude Haiku narrative + deterministic fallback)
│       └── cli.py          (argument parsing, analyze command, entry point)
└── tests/
    ├── test_parser.py
    ├── test_stats.py
    ├── test_report.py
    ├── test_ai.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Parser: binary CSV parsing, raw-option CSV + answer-key parsing/scoring, student-ID column auto-detection, malformed CSV (mismatched column counts) raises a clear error, empty file raises a clear error.
  - Stats: p-value calculation against hand-computed values, point-biserial against a hand-computed reference dataset, zero-variance item returns the "undefined" sentinel instead of raising or returning NaN, KR-20 against a hand-computed reference, single-item KR-20 returns the "not meaningful" sentinel, distractor analysis correctly identifies a non-functioning distractor and a reversed-pull distractor, small-N upper/lower split still returns a result with a small-N flag.
  - Report: HTML output escapes a literal `<script>` payload placed in an item ID (XSS regression test), JSON output round-trips through `json.loads` and matches expected keys, text output contains the flagged-item summary.
  - AI: deterministic template fallback produces a non-empty, item-specific suggestion with no network call when no API key is set (mocked — never a live call), and the Anthropic call path is exercised against a mocked `urllib.request.urlopen` so no live network access happens in tests.
  - CLI: end-to-end `analyze` run on the binary sample data produces valid JSON with the correct item/student counts; missing input file produces a clean error exit code instead of a traceback; `--format` flag selects the right renderer.

## Success Criteria

1. All tests pass (zero failures)
2. Running `itemscope analyze` on both sample CSVs (binary and raw-option) produces correct, hand-verified p-values, point-biserial discrimination, and KR-20 reliability for at least one fully worked example
3. The HTML report renders in a browser with the quadrant scatter plot, sortable item table, and flagged-items panel all populated, and a `<script>` payload injected into an item label is verified inert (rendered as text, not executed)
4. Zero-variance and single-item edge cases produce a clear labeled result ("undefined"/"not meaningful") rather than a crash or a silently wrong number
5. The tool runs end-to-end with zero API keys set (deterministic fallback path), and separately with a mocked Anthropic call, without any live network request in either case

---

## Scope Changes

None — full scope as specified above was completed.
