# Build Log — Deadline Guardian

> **Date:** 2026-07-17
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [Session Start]

- Step 0: checked `builds/` for an interrupted prior session. The most recent dated folder (`2026-06-18-regex-dojo` on the local `main`-derived checkout) was complete. Fetched the most recent open PR branch (`claude/cool-sagan-gdhf3r`, PR #43, 2026-07-16 "AgentLint") per Step 1 — its `builds/index.md` and `BUILD_LOG.md` confirm it too ended with "Build complete. Success criteria reviewed. All tests passing." Nothing to resume.
- Read `PROFILE.md`, the most current `builds/index.md` (36 builds, last build 2026-07-16), `builds/ideas.md`, and `STANDARDS.md`.
- Day of year 198 → `(198-1) % 9 = 8` → Category **I — Life Admin Helper**, consistent with the observed 7-night rotation B→C→D→E→F→G→H (07-10 through 07-16).
- `builds/ideas.md` has zero `pending` rows with `Category = I` → lottery skipped per Step 2c, went straight to fresh idea generation (Step 2d).
- Generated 3 candidates: Deadline Guardian, TripCast (weather-aware packing planner), Lab Reagent & Equipment Calibration Log. Chose **Deadline Guardian** — see `WhyThis.md` for full rationale. The other two will be appended to `builds/ideas.md` as new pending rows (IDs 26–27) after the build.
- Build folder created: `builds/2026-07-17-deadline-guardian/`
- Current git branch: `claude/cool-sagan-1sbxkw`, confirmed equal to `origin/main` (no prior unmerged commits on it) — building directly on it.

### [PRD Written]

- Goal: local deadline tracker for recurring academic/research admin (grants, IRB/ethics, courses, conferences, manuscripts) with Claude-powered extraction from pasted text and a self-contained HTML dashboard.
- Scope: SQLite store, `add`/`capture`/`complete`/`list`/`render` CLI commands, recurrence math (annual/semesterly/custom-month), AI extraction with a deterministic regex/keyword fallback when no API key is present, dark-mode dashboard with urgency buckets.
- Out of scope: calendar/email integration (no OAuth credentials available at build time), notifications/daemons, multi-user.
- Notable decision: Anthropic API is called directly via stdlib `urllib.request` (no `anthropic` package dependency), matching the established pattern from GrantScope/Schema Sentinel/Ledger Lens — keeps `requirements.txt` empty and avoids a runtime pip install step for the user.

### [Build Phase]

Implemented in order: `src/recurrence.py` (month-add date math with day-of-month clamping for leap years/short months), `src/db.py` (SQLite CRUD, category/recurrence validation, `complete_deadline` auto-creates the next occurrence for recurring rules), `src/ai_client.py` (stdlib `urllib.request`-only Anthropic Messages API client — no `anthropic` package dependency, matching the established pattern from GrantScope/Schema Sentinel/Ledger Lens), `src/extraction.py` (deterministic regex/keyword fallback parser for dates/category/recurrence, plus a Claude-backed extractor that falls back automatically on any API failure), `src/render.py` (self-contained dark-mode HTML dashboard — deadline data is inlined as JSON in a `<script type="application/json">` block, and all user text is inserted via `textContent` in vanilla JS rather than string-interpolated HTML, so a hostile title can't execute), `src/cli.py` (argparse dispatch for `add`/`capture`/`complete`/`list`/`render`), and the thin `deadline_guardian.py` entry point.

### [Tests Run]

Wrote 74 tests across `tests/test_recurrence.py`, `tests/test_db.py`, `tests/test_extraction.py`, `tests/test_ai_client.py`, `tests/test_render.py`, and `tests/test_cli.py`. All external Anthropic API calls are mocked (`urllib.request.urlopen` and `ai_client.call_claude` are monkeypatched — no real network access happens anywhere in the suite). Installed `pytest` via `pip3 install --user pytest` (not present in the base image).

Tests: 74 passed, 0 failed. `python3 -m pytest tests/ -v` from the build folder.

### [Verify] Success criteria + manual end-to-end check

Ran the full CLI lifecycle by hand from a clean `data/` state: `add` (two manual deadlines, one annual/IRB and one custom-12-month/Grant), `capture` with `ANTHROPIC_API_KEY` unset (fallback parser correctly extracted "Conference" category and the `March 1, 2027` date from a natural-language reminder), `list` and `list --json`, `complete --id 2` on the recurring Grant deadline (correctly created occurrence #4 dated exactly 12 months later), and `render`. Installed `playwright` (browsers were already pre-installed at `/opt/pw-browsers/chromium-1194`) to load the generated `dashboard.html` in headless Chromium: zero console/page errors, urgency buckets (Due This Month / Upcoming / Completed) rendered correctly for the test data, and the category filter chips work (clicking "Grant" correctly narrowed the table to the two Grant-category rows). Screenshots reviewed visually — dark mode renders cleanly, mobile breakpoint CSS present.

Security checklist (STANDARDS.md) run via grep across `src/` and `deadline_guardian.py`: no `eval`/`exec`, no `innerHTML` (verified the one grep hit is a docstring describing the deliberate avoidance, not usage), no `os.system`/`subprocess`, no hardcoded credential-shaped strings, no `.env` files. `git status --porcelain --ignored=matching` confirms `data/`, `dashboard.html`, and both `__pycache__`/`.pytest_cache` directories are correctly excluded by the build folder's own `.gitignore` and will not be staged.

All 5 PRD success criteria met:
1. 74/74 tests pass — exceeds the 15-test minimum.
2. `add`/`capture` (both fallback and AI-mocked paths)/`complete`/`list --json` verified end-to-end against a real SQLite file the tool created itself.
3. Recurring completion verified for annual (2026→2027, +12mo) and every_N_months (2026-07-20→2027-07-20, +12mo) rules; unit tests separately cover semesterly and the Jan-31→Feb-28 / Feb-29-leap-year month-clamp edge cases.
4. `dashboard.html` opens via `file://`, buckets correctly, and a deliberately hostile title (`</script><img onerror=...>`) was confirmed both by a dedicated unit test and via headless-Chromium execution (zero JS errors, no unexpected alert) to never break out of its JSON container.
5. No network call occurs anywhere in the 74-test suite — confirmed by inspection (every Anthropic call site is monkeypatched) and by the tests passing in this sandboxed container with no outbound HTTPS allowed to api.anthropic.com.

### [Documentation]

- `FutureFeatures.md`: 7 concrete suggestions.
- `Manual.md`: quick start, full CLI reference, configuration, troubleshooting, known limitations.

Build complete. Success criteria reviewed. All tests passing.
