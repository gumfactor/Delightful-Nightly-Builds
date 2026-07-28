# PRD — Voiceprint

## Goal

Audit a writing draft (blog post, book chapter, manuscript prose) for the lexical and structural
patterns that make prose read as AI-generated or formulaic, produce an explainable "Human Voice
Score," and track that score over repeated drafts of the same project.

## User Story

As someone who writes blog posts, book chapters, and public-facing articles and who explicitly
dislikes writing that sounds obviously AI-generated, I want to run a tool against a draft before
I publish it, see exactly which phrases and patterns are tripping the "sounds like AI" alarm (with
line numbers and counts, not a vague vibe), get a plain-English second opinion on the worst
passages, and see whether my scores are improving across drafts of the same long-running project —
so I can fix the prose myself instead of guessing.

## Scope

### In Scope

- Deterministic heuristic engine analyzing a single Markdown/plain-text file:
  - Curated AI-tell phrase/transition list (~60 phrases: "delve into", "it's important to note",
    "in today's world", "moreover", "furthermore", "testament to", "tapestry", "navigate the
    complexities", "in the realm of", "that being said", "leverage", "seamless", "robust",
    "underscores", "boasts", etc.) — counted with line numbers and surrounding excerpt.
  - Structural checks: em-dash density, semicolon density, hedge-word density ("might", "could",
    "perhaps", "arguably", "in some ways"), rule-of-three list density (comma-separated triads),
    passive-voice heuristic (regex-based "was/were/been + past participle").
  - Burstiness: standard deviation of sentence length (low stddev relative to mean = mechanically
    uniform rhythm, a known AI tell).
  - Vocabulary diversity: type-token ratio (unique words / total words) over a rolling window.
  - Paragraph-opening repetition: same first word/phrase opening 3+ paragraphs.
- Weighted, documented scoring formula → 0–100 Human Voice Score (100 = most natural/human-reading,
  lower = more flagged patterns). All weights defined as named constants, no black-box ML.
- Batch mode: run against every `.md`/`.txt` file in a directory.
- Local SQLite history: each run of a given file (keyed by absolute path) stores
  `(timestamp, word_count, score, flag_count)`, so re-running the tool on revisions of the same
  file over time shows a trend. A `history` command prints a per-file score trend as a terminal
  sparkline + delta from the previous run.
- Optional Claude Haiku holistic pass: sends the 3 lowest-scoring flagged paragraphs (the user's
  own draft text, not third-party personal data) and asks for a one-sentence diagnosis + a
  rewritten example per paragraph. Runs only when `ANTHROPIC_API_KEY` is set at runtime.
  Deterministic template fallback (keyed to which heuristics fired) when no key is present —
  the tool is fully functional with zero configuration.
- Output: colored terminal report (score, top offending patterns, worst paragraphs), JSON export,
  and a self-contained dark-mode HTML report (score gauge, flagged-excerpt list with highlighted
  spans, history sparkline chart) — readable on a phone.

### Out of Scope

- No plagiarism detection or third-party AI-detection API calls (OpenAI classifier, GPTZero, etc.)
  — this is a self-authored style auditor, not a plagiarism/authorship forensic tool.
  Only free/no-auth-required behavior (fully local heuristics) is used.
- No automatic rewriting of the user's file in place — the tool reports and suggests; the user edits.
- No web UI / server — this is a CLI + generated static HTML report, matching Category B's
  "automation script / workflow tool" framing.
- No support for `.docx`/`.pdf` input in this build (Markdown/plain text only) — see FutureFeatures.

## Tech Stack

- Python 3, standard library only for the deterministic core (`re`, `statistics`, `sqlite3`,
  `argparse`, `json`, `html`).
- Anthropic API (optional, runtime-only) via `urllib.request` — no `anthropic` package dependency,
  consistent with prior builds' pattern (Ledger Lens, Deadline Guardian, etc.).
- Chart.js 4.4.4 pinned via CDN for the HTML report's history chart, with a verified plain-table/
  SVG-sparkline fallback if the CDN is unreachable.
- pytest for testing.

## Data Structure

SQLite database `voiceprint.db` (created in the build folder, or a path the user specifies):

```sql
CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    run_at TEXT NOT NULL,        -- ISO 8601 UTC timestamp
    word_count INTEGER NOT NULL,
    score REAL NOT NULL,
    flag_count INTEGER NOT NULL,
    details_json TEXT NOT NULL   -- full per-run flagged-pattern breakdown, for history drill-down
);
```

No personal data fields — `file_path` is a local filesystem path the user supplies, not a
third-party's information.

## Folder Structure

```
builds/2026-07-28-voiceprint/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── heuristics.py      # all deterministic pattern-detection functions
│   ├── scoring.py         # weighted score aggregation
│   ├── storage.py         # SQLite history read/write
│   ├── ai_review.py       # optional Claude Haiku call + deterministic fallback
│   ├── report.py          # terminal / JSON / HTML report rendering
│   └── cli.py             # argparse entry point (analyze / batch / history)
├── main.py                # thin entry point calling src.cli
└── tests/
    ├── test_heuristics.py
    ├── test_scoring.py
    ├── test_storage.py
    ├── test_ai_review.py
    ├── test_report.py
    └── test_cli.py
```

## Testing Strategy

- **Unit tests for every heuristic function** (`test_heuristics.py`): each AI-tell phrase category,
  em-dash/semicolon/hedge-word density counters, passive-voice regex, rule-of-three detector,
  burstiness (stddev) calculation on both uniform and varied sentence-length fixtures, type-token
  ratio, paragraph-opening repetition — each with a positive fixture (pattern present) and a
  negative fixture (clean prose that must not false-positive).
- **Scoring tests** (`test_scoring.py`): verify the weighted formula is monotonic (more flags →
  lower score, never negative, never above 100), and that an empty/whitespace-only file is
  handled without a crash (score defined, zero flags).
- **Storage tests** (`test_storage.py`): using a temp SQLite file — insert and retrieve a run,
  confirm history ordering by timestamp, confirm multiple files don't cross-contaminate history.
- **AI review tests** (`test_ai_review.py`): the Anthropic HTTP call is fully mocked (injectable
  `request_fn`) — covers success-path parsing, no-API-key fallback (must not attempt a network
  call), and malformed-response/network-error fallback. **No live API calls in any test.**
- **Report tests** (`test_report.py`): JSON output is valid and round-trips; HTML output correctly
  `html.escape`s a deliberately adversarial excerpt (e.g. containing `<script>`) so it cannot
  execute — verified by asserting the raw `<script>` substring never appears unescaped in the
  rendered HTML.
- **CLI tests** (`test_cli.py`): `analyze` on a real fixture file end-to-end (temp dir, no network),
  `batch` mode across a fixture directory, `history` command against a pre-seeded temp database,
  and error handling for a missing input file.
- Minimum 15 tests required; target is well above that given six test modules.
- Run with `python -m pytest tests/ -v` from the build folder.

## Success Criteria

1. Running `python main.py analyze <file>` on a fixture file containing known AI-tell phrases
   produces a report that names each phrase, its line number, and a count — verified by tests.
2. The Human Voice Score is deterministic and reproducible: the same input file always yields the
   same score, and a version of the file with AI-tell phrases stripped out scores strictly higher.
3. Running `analyze` twice on the same file records two distinct history rows in SQLite, and
   `history <file>` shows both runs with a computed score delta.
4. With no `ANTHROPIC_API_KEY` set, `analyze --ai` still completes successfully using the
   deterministic fallback and makes zero network calls (verified by test assertion on the mock).
5. The generated HTML report renders with zero unescaped user content — verified by a script-tag
   injection test — and opens correctly in a browser with the score, flagged excerpts, and history
   chart all visible and legible on a narrow (mobile-width) viewport.
