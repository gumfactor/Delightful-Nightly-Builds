# PRD — Deadline Guardian

> **Build date:** 2026-07-17
> **Category:** I — Life Admin Helper
> **Complexity:** Ambitious
> **Day of week:** Friday

---

## Goal

A local CLI + dashboard that tracks recurring academic/research administrative deadlines (IRB/ethics renewals, grant progress reports, conference/manuscript submissions, course prep, student evaluations) and uses Claude to turn a pasted email or notice into a structured deadline entry automatically.

## User Story

As an Associate Professor running a research lab who juggles grant reporting, ethics renewals, course prep, and conference deadlines across academic and entrepreneurial work, I want to capture administrative deadlines without manually re-typing every date and recurrence rule, and see at a glance what's overdue or urgent, so that nothing slips through the cracks and I spend less time on administrative overhead.

## Scope

### In Scope
- SQLite-backed local store of deadlines: title, category (Grant, IRB/Ethics, Course, Student Evaluation, Conference, Manuscript, Other), due date, recurrence rule (none / annual / semesterly / custom N-month interval), notes, source text (optional), completed flag, completed-at timestamp.
- `add` command: manually add a deadline via CLI flags.
- `capture` command: paste or pipe in unstructured text (an email, a portal notice) and have Claude (`ANTHROPIC_API_KEY` read from environment at runtime) extract title / category / due date / recurrence into a structured deadline, with a deterministic keyword/date-regex fallback parser when no API key is set so the tool still works without AI.
- `complete` command: mark a deadline done. If it has a recurrence rule, automatically schedule the next occurrence (e.g. completing an annual IRB renewal creates next year's entry) rather than losing the recurring commitment.
- `list` / `render` commands: render a self-contained dark-mode HTML dashboard (no external network calls in the rendered file) grouping deadlines into Overdue / Due This Week / Due This Month / Upcoming / Completed, color-coded, sortable table, category filter chips, and a small "quick add via AI" text box (client-side only — reflects the last `capture` result; the actual AI call happens through the CLI, not from the static HTML file, so no key ever needs to live in the browser).
- `--json` output mode for scripting.
- Recurrence math: given a due date and a rule, compute the next due date after completion.
- Text extraction rule engine: regex/keyword-based date and category detection as the no-API fallback; Claude-based extraction as the enhanced path.
- Data lives in a local SQLite file inside the build folder's `data/` subdirectory (created at runtime, not committed).

### Out of Scope
- Sending emails or calendar invites (no SMTP/OAuth credentials available for this build).
- Google Calendar / Outlook integration (not in PROFILE.md's build-time Data Sources list — requires OAuth this build container can't perform).
- Multi-user / shared access — this is a single local user tool.
- Push notifications or background daemons — the user runs the CLI or opens the dashboard when they want a status check.
- Automatic detection of deadlines from an inbox (no email API access) — text must be pasted or piped in manually.

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None — stdlib only (`sqlite3`, `argparse`, `urllib.request`, `re`, `datetime`, `html`, `json`)
- **Dependencies:** None (stdlib only); Anthropic API called directly via `urllib.request` at runtime, matching the pattern used in prior builds (GrantScope, Schema Sentinel, Ledger Lens) — no `anthropic` SDK dependency needed
- **Runtime requirement:** `python3 deadline_guardian.py <command> ...` — no install step. Opens `dashboard.html` directly in a browser (`file://`, no server).

## Data Structure

SQLite database (`data/deadlines.db`), single table:

```sql
CREATE TABLE deadlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,        -- Grant | IRB/Ethics | Course | Student Evaluation | Conference | Manuscript | Other
    due_date TEXT NOT NULL,        -- ISO 8601 date (YYYY-MM-DD)
    recurrence TEXT NOT NULL,      -- 'none' | 'annual' | 'semesterly' | 'every_N_months' (N stored in recurrence_months)
    recurrence_months INTEGER,     -- NULL unless recurrence is a custom interval
    notes TEXT,
    source_text TEXT,              -- original pasted text, if created via `capture`
    extraction_method TEXT,        -- 'manual' | 'ai' | 'fallback'
    completed INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    created_at TEXT NOT NULL
);
```

`dashboard.html` is generated as a fully self-contained static file (data inlined as a JSON blob in a `<script>` tag) — no fetch calls, no server, safe to open via `file://` or email to yourself.

## Folder Structure

```
builds/2026-07-17-deadline-guardian/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt          (empty — stdlib only, documented per STANDARDS.md)
├── src/
│   ├── __init__.py
│   ├── db.py                 (SQLite schema + CRUD)
│   ├── recurrence.py          (next-due-date math)
│   ├── extraction.py          (fallback regex/keyword parser + Claude-backed parser)
│   ├── ai_client.py            (urllib-based Anthropic API call, mockable)
│   ├── render.py               (HTML dashboard generation, escaped output)
│   └── cli.py                   (argparse command dispatch: add/capture/complete/list/render)
├── deadline_guardian.py        (thin entry point calling src.cli.main)
├── tests/
│   ├── test_db.py
│   ├── test_recurrence.py
│   ├── test_extraction.py
│   ├── test_ai_client.py
│   ├── test_render.py
│   └── test_cli.py
└── data/                        (created at runtime; not committed — .gitkeep + .gitignore only)
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v` (run from the build folder)
- **What will be tested:**
  - DB: create deadline, list deadlines, mark complete, completing a recurring deadline creates the next occurrence with correct date math, completing a non-recurring deadline does not create a follow-on row
  - Recurrence: `none` returns `None`; `annual` adds 1 year (with Feb-29 edge case handling); `semesterly` adds 6 months; `every_N_months` adds N months; month-end overflow (e.g. Jan 31 + 1 month → Feb 28/29, not an invalid date)
  - Extraction fallback (no API key): finds an explicit date in common formats, infers category from keywords ("IRB", "REB", "grant progress report", "abstract deadline"), defaults sensibly when no date is found (raises a clear error rather than guessing silently)
  - Extraction via AI: mocked `urllib.request.urlopen` returns a canned Claude JSON response; verify the parsed fields are correctly extracted from the mocked response and that the raw source text is preserved; verify a network/timeout error falls back to the deterministic parser rather than crashing
  - AI client: request is well-formed (correct headers, no API key leakage into logs/exceptions), missing `ANTHROPIC_API_KEY` raises a specific, catchable error rather than a bare exception
  - Render: HTML output escapes user-entered titles/notes (XSS safety — a `<script>` in a title must not execute), correct urgency bucketing (overdue vs due-this-week vs due-this-month vs upcoming) given a fixed "today", completed items appear in the Completed section
  - CLI: `add` persists a row with correct defaults, `complete` on a recurring item creates the next row, `list --json` produces valid JSON, unknown category is rejected with a clear error, missing required argument produces a non-zero exit with a usage message
  - Edge cases: empty database renders a dashboard with an empty state (no crash), a title containing HTML/JS is escaped in the rendered file, a due date exactly "today" is bucketed correctly, marking an already-completed deadline complete again is a no-op / clear error

## Success Criteria

1. All tests pass (zero failures), minimum 15 tests, run via `python -m pytest tests/ -v`
2. `add`, `capture` (with and without `ANTHROPIC_API_KEY` set — fallback path verified), `complete`, and `list --json` all work end-to-end against a real local SQLite file created by the tool itself
3. Completing a recurring deadline automatically creates the correctly-dated next occurrence (verified for annual, semesterly, and custom-interval rules, including month-length edge cases)
4. `render` produces a self-contained, dark-mode `dashboard.html` that opens directly via `file://`, correctly buckets deadlines by urgency, and safely escapes all user-entered text (verified with a deliberately hostile input string)
5. No network call is made during the test suite; the Claude API path is fully mocked and the deterministic fallback path is exercised without any API key present

---

## Scope Changes

(none yet — filled in during build if scope changes)
