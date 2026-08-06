# Build Log — Manuscript Pipeline

> **Date:** 2026-08-06
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:20 UTC] Session Start

- Step 0: most recent local dated build folder was `builds/2026-06-18-regex-dojo`; its `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — nothing to resume.
- Read PROFILE.md, STANDARDS.md. Resynced `builds/index.md` and `builds/ideas.md` from the most recent open PR branch (`claude/cool-sagan-2525au`, PR #62, `build(2026-08-05): Impact Ledger`) rather than the local/main copies, which were weeks behind (last local build 2026-06-18; last PR build 2026-08-05, 55 total builds recorded).
- Day of year 218 → `(218-1) % 9 = 1` → Category B (Productivity Utility).
- Found and corrected a data-integrity bug in `builds/ideas.md`: backlog rows #4 and #7 (both Category B) were marked `pending` but had actually already been built (2026-07-10 Worklog, 2026-06-22 Morning Briefing respectively) and never flipped to `built`. Corrected both before running the lottery.
- With the pool empty post-correction, lottery skipped per `builds/ideas.md`'s own rule; generated 3 fresh Category B candidates. Selected: **Manuscript Pipeline** — a CLI tool tracking academic manuscripts through submission → review → revision → publication, with Crossref-based auto-detection of publication. Full reasoning in `WhyThis.md`.
- Build folder created: `builds/2026-08-06-manuscript-pipeline/`

### [08:30 UTC] PRD Written

- Goal: track a researcher's own manuscripts through the submission pipeline and auto-detect when one is quietly published.
- Scope: SQLite-backed CLI (`add`, `list`, `update`, `capture`, `sync`, `report`), deterministic regex-based decision-email parsing with optional Claude Haiku enrichment, Crossref-based publication auto-detection, terminal + self-contained dark-mode HTML report.
- Notable constraints/decisions: stdlib only (`urllib`, `sqlite3`, `argparse`, `re`) to keep the build dependency-free; Anthropic API strictly optional and mocked in all tests; Crossref calls mocked in all tests.

### [08:45 UTC] Build Phase

- Implemented `src/db.py` (SQLite schema: manuscripts + append-only status_log), `src/parsing.py` (deterministic decision-email parser + optional Claude Haiku enrichment with unconditional fallback), `src/crossref.py` (Crossref works-search client + title/author match scoring), `src/render.py` (terminal report + HTML dashboard), `src/main.py` (argparse CLI wiring `add`/`list`/`update`/`capture`/`sync`/`report`).
- Decision: Crossref auto-detection match threshold set to normalized token-overlap ratio ≥ 0.72 on title **and** at least one matching author surname, to avoid false-positive "published" flips on similarly-titled unrelated papers. Documented in Manual.md.
- Decision: "at risk" threshold for `submitted`/`under_review` is a configurable expected-review-days value (default 90, override with `--expected-days` on `add`); revision deadlines are explicit dates captured via `capture`/`update`, not estimated.

### [09:00 UTC] Tests Run — first pass, 3 real bugs found and fixed

Initial run: 58 passed, 3 failed. All three were genuine bugs, not test problems:

1. `parsing.deterministic_parse` mis-classified a rejection email ("...unable to accept your manuscript...") as an acceptance, because the bare keyword `"accept"` matched the substring inside "unable to accept" before the rejection keyword list was checked. Fixed by reordering `DECISION_KEYWORDS` to check rejection/revision phrases first and removing the overly-generic bare `"accept"` keyword in favor of specific acceptance phrases.
2. `cmd_capture` used `args.text if args.text else sys.stdin.read()`, which treats an empty string (`--text ""`) as falsy and incorrectly falls through to blocking on stdin. Fixed to check `args.text is not None`.
3. `render_html` used `html.escape()` on the JSON blob embedded in a `<script type="application/json">` element. `<script>` content is HTML "raw text" — character references are never decoded by the browser inside it — so escaping the quotes to `&quot;` would have corrupted the JSON the moment `JSON.parse` tried to read it back via `.textContent`, silently breaking the entire report page for any manuscript with a title containing a quote or angle bracket. Fixed by switching to JSON-safe `\uXXXX` escaping of `<`, `>`, and `&` (the standard "safe JSON for script embedding" pattern), which neutralizes injection while keeping the payload valid, parseable JSON. Re-verified by round-tripping the embedded blob through `json.loads` after rendering.

Tests: 62 passed, 0 failed after fixes.

### [09:10 UTC] Manual End-to-End Verification

Ran the CLI against a real temp SQLite database (not the test suite): `add` (3 manuscripts, including one with a `<script>alert(1)</script>` title), `list` (correctly flagged the one manuscript past its 60-day expected-review window as at-risk, left the other two unflagged), `capture` against two hand-written sample decision emails (an acceptance and a revise-and-resubmit with an explicit deadline date — both correctly parsed and applied via the deterministic fallback, since no `ANTHROPIC_API_KEY` is set in this environment), and `report` (terminal output correct; HTML report's embedded JSON blob round-tripped successfully through `json.loads`, and the injected `<script>` payload appeared only as its escaped, inert `<script>...` form — confirmed via `grep -c` that zero raw `<script>alert` occurrences exist in the output file).

### [09:15 UTC] Verify — Success Criteria & Security Checklist

PRD success criteria:
1. All tests pass (62/62, zero failures) — met.
2. `add → list → update → capture → sync → report` all function end-to-end — met, verified both in pytest and manually above (`sync` verified via mocked Crossref responses in `tests/test_main.py` and `tests/test_crossref.py`, since this container's egress proxy blocks `api.crossref.org` — consistent with prior builds in this catalog, e.g. Citation Vault, Impact Ledger).
3. `sync` never calls the network for a terminal-state manuscript, and Crossref matching distinguishes true match from similarly-titled unrelated paper — met, see `test_sync_skips_manuscripts_already_in_terminal_state` and `test_find_publication_match_true_negative_similar_title_different_authors`.
4. HTML report renders with zero unescaped user-controlled HTML, verified against two injection payloads (`<script>` and `<img onerror>`) — met.
5. Zero Anthropic API calls when `ANTHROPIC_API_KEY` is unset — met, see `test_ai_parse_makes_no_network_call_without_api_key` (asserts the mock was never invoked).

Security checklist: no `.env` file; no hardcoded credentials/secrets; no `eval`/`exec`; no `os.system`/`subprocess`; no `innerHTML` assignment anywhere in `render.py` (verified by `test_render_html_uses_textcontent_not_innerhtml_for_dynamic_rows`); no file paths built from user-controlled input; all code reads/writes only within the build folder (`manuscripts.db` and `report.html` are created relative to the CLI's working directory / `--db`/`--out` flags, never a hardcoded external path).

### [09:20 UTC] Documentation

- `FutureFeatures.md`: 7 concrete suggestions across quick-win/medium/ambitious tiers.
- `Manual.md`: quick start, full command reference, match-threshold and at-risk-threshold configuration notes, troubleshooting, known limitations.

Build complete. Success criteria reviewed. All tests passing.

### [08:30 UTC] PRD Written

- Goal: track a researcher's own manuscripts through the submission pipeline and auto-detect when one is quietly published.
- Scope: SQLite-backed CLI (`add`, `list`, `update`, `capture`, `sync`, `report`), deterministic regex-based decision-email parsing with optional Claude Haiku enrichment, Crossref-based publication auto-detection, terminal + self-contained dark-mode HTML report.
- Notable constraints/decisions: stdlib only (`urllib`, `sqlite3`, `argparse`, `re`) to keep the build dependency-free; Anthropic API strictly optional and mocked in all tests; Crossref calls mocked in all tests.

