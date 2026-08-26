# Build Log — Thesis Breaker

> **Date:** 2026-08-26
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:23 UTC] Session Start

- Checked `builds/` for an incomplete prior session (Step 0): most recent local dated folder is `2026-06-18-regex-dojo`, whose BUILD_LOG.md ends in "Build complete. Success criteria reviewed. All tests passing." — nothing to resume.
- Note: `gh` CLI and GitHub MCP tools were unavailable in this session, so the "most recent open PR branch" resync in CLAUDE.md Step 1/9 was done via `git fetch`/`git show <branch>:builds/index.md` against the remote branch with the latest commit timestamp (`claude/cool-sagan-1vk118`, 2026-08-25) instead of `gh pr list`. Read PROFILE.md, STANDARDS.md, and that branch's `builds/index.md`/`ideas.md` as the current state.
- Observation logged for follow-up (not part of tonight's build): 76 nightly build branches (`claude/cool-sagan-*`) exist on the remote going back to 2026-06-10, none merged into `main` — `main` is still at the 2026-06-18 Regex Dojo build plus two docs/ratings commits. The branch-local `builds/index.md` shows 74 builds recorded across that unmerged chain. This is a merge backlog, not a build-content problem; flagged to the user separately.
- Day of year 238 → category rotation index `(238-1) % 9 = 3` → **Category D — Creative / Generative**.
- Category D backlog (from synced `ideas.md`): 1 pending row (#17, Workshop Architect, unrated → 5 tickets, R=0 → 25% lottery chance). Roll: 50/100 → above gate → fresh ideas generated (Step 2d).
- Topic diversity check (last 10 builds): Grant Vault(C), Lecture Loom(B), Trading Book(A), Renewal Radar(I), Fairway Physics(G), Effort Ledger(F), Voxel Lab(E), Maple Press(D), Curriculum Atlas(C), Provenance(B). Investment/finance appears once (Trading Book) — not saturated.
- Generated 3 fresh Category D ideas; selected **Thesis Breaker** — a real-data-grounded adversarial bear-case critique generator for the user's own investment theses. Full reasoning in `WhyThis.md`.
- Build folder created: `builds/2026-08-26-thesis-breaker/`

### [08:31 UTC] PRD Written

- Goal: stress-test a user-authored investment thesis against real fetched fundamentals via 3 fixed critic personas and a 5-category deterministic bear-case rule engine.
- Scope: `check`/`demo`/`history`/`render`/`list` CLI commands, yfinance data layer (dependency-injected for testing), deterministic rules + persona scoring, append-only SQLite history, self-contained dark-mode HTML report, optional Haiku narrative polish with unconditional deterministic fallback.
- Notable constraints: build container's egress proxy blocks yfinance's live host, so a bundled `demo` fixture path is the only way to manually verify the full pipeline end-to-end tonight; the real `check` path is written and unit-tested against a mocked ticker factory but its live network behavior can only be verified by the user locally. Documented per CLAUDE.md's "design for the user's runtime" guidance.

### [09:05 UTC] Build Phase — data layer, rules, personas

- `src/fetch.py`: `fetch_ticker_data(ticker, ticker_factory=yfinance.Ticker)` — dependency-injected so tests never touch network. Reads `.info`/`.fast_info` for P/E, P/S, sector, debt/equity; `.quarterly_income_stmt` for revenue-by-quarter (YoY growth computed from 5 quarters of raw revenue so 4 YoY points can be derived) and operating margin; `.insider_transactions` for the insider table. Any missing/absent field becomes `None` rather than a fabricated number.
- `src/rules.py`: 5 categories (`valuation_stretch`, `growth_deceleration`, `margin_debt_risk`, `insider_selling`, `narrative_fragility`), each returns a `RuleResult(fired: bool | None, detail: str)` — `None` means "cannot evaluate," never coerced to `False`, so an unavailable data field is visibly distinct from a checked-and-passed field in the report.
- `src/personas.py`: 3 fixed personas with explicit category weight dicts; score = weighted sum of fired categories over max possible, on a 0–100 scale; rationale built directly from each `RuleResult.detail` string, never a static template.
- Decision: sector-average P/E is a static documented reference table (Tech/Healthcare/Financials/Energy/ConsumerDiscretionary/Industrials/Other), not a second live API — keeps the valuation check testable and shippable in one session without depending on an undocumented second data source. Logged as a known simplification in `FutureFeatures.md`.

### [09:40 UTC] Build Phase — narrative, store, render, CLI

- `src/narrative.py`: deterministic per-persona template always available; optional `polish(persona, rationale_detail, api_key)` sends only the already-computed rule findings (never raw fetched numbers beyond what fired) to Claude Haiku via `urllib` (no SDK dependency, matching the repo's established pattern), and falls back to the deterministic text on `ANTHROPIC_API_KEY` unset, any `URLError`, non-200 status, or a response missing the expected field.
- `src/store.py`: `sqlite3`, one `checks` table, append-only inserts; `run_timestamp` is passed in by the caller (CLI captures it once via `datetime.now(timezone.utc).isoformat()` at the top of `main()`, never inside library code, so the library itself stays deterministic and testable without monkeypatching the clock).
- `src/render.py`: builds the HTML report with `html.escape()` applied to every user-controlled string (`ticker`, `thesis_text`, insider names) before interpolation; Canvas 2D charts for valuation-vs-threshold and quarterly revenue growth, plus a bear-case-score-over-time line once 2+ rows exist for a ticker+thesis pair.
- `src/cli.py` + `main.py`: `argparse` subcommands `check`, `demo`, `history`, `render`, `list`.
- Bundled `fixtures/sample_aapl_fetch.json`: a hand-crafted, realistic (not live-pulled) fetch payload used by both `demo` and as the mock payload shape in tests.

### [10:05 UTC] Tests Run

Tests: 65 passed, 0 failed. (`/root/.local/bin/pytest tests/ -v` — a project-local `pytest` install was not present in this container; the pre-installed `uv`-managed `pytest` binary at `/root/.local/bin/pytest` was used instead. The user's local `python -m pytest tests/ -v` works identically once `pip install -r requirements.txt` and `pytest` are available.)

One test failure surfaced and was fixed during this phase: the history line chart's `<canvas id="historyChart">` element is only emitted in the HTML when 2+ prior runs exist, but the `<script>` block unconditionally called `drawLineChart('historyChart', ...)` regardless, so the literal string `historyChart` always appeared in the output even with 0-1 runs. Fixed by making that JS call conditional on the same `show_history_chart` flag that gates the `<section>` itself (`src/render.py`).

### [10:10 UTC] Manual End-to-End Verification (real CLI runs, not just mocked tests)

- Ran `python3 main.py demo` for real (no network access available in this container, `ANTHROPIC_API_KEY` unset): produced a genuine `report.html` with all 3 persona cards, the 5-row triggered-checklist matrix (4 fired — Valuation Stretch, Growth Deceleration, Margin/Debt Risk, Narrative Fragility — and 1 "cannot evaluate" — Insider Selling Signal, since the bundled fixture omits insider data on purpose to exercise that path), and the real-data summary panel. Confirmed via `grep -o` badge-class counts in the actual output file (1 clear, 5 fired-or-CSS-selector, 2 unknown-or-CSS-selector, resolving to the expected 4/0/1 split once the one-time CSS-selector occurrence of each class name is subtracted).
- Discovered during this manual pass that fetched insider-transaction data was never actually displayed anywhere in the report (only aggregated into the Insider Selling rule's detail text) — added an "Insider Transactions" table to `src/render.py` with `html.escape()` on every field, plus 3 new tests, so the fetched data is genuinely visible and there is a real field to XSS-test against.
- Ran `demo` twice against the same fresh SQLite file: `history AAPL` showed 2 distinct timestamped rows with independent overall scores (both 100/100 for this fixture+thesis pair, since the default demo thesis triggers every weighted category), confirming real append-only persistence, not just the mocked pytest fixture. `list` and `render --id` were also run for real against that file and produced correct output.
- Built a standalone Node.js verification script driving the container's globally-installed `playwright@1.56.1` package (`/opt/node22/lib/node_modules/playwright`) against the pre-installed headless Chromium at `/opt/pw-browsers/chromium` (Python's `playwright` package is not installed in this container, so the global Node install was used directly rather than as a project dependency — this build has no Node/JS component of its own). Loaded three real generated reports: a clean one, one with `</script><script>alert(1)</script>` in `--thesis`, and one with `<img src=x onerror=alert(1)>` as a fetched insider name. Result for all three: 0 dialogs, 0 page errors, exactly 1 `<script>` tag (the report's own authored chart script) and 0 `<img>` elements — the payloads are confirmed present only as escaped, inert text in the rendered DOM.
- Ran `--ai-polish` for real with `ANTHROPIC_API_KEY=fake-test-key-not-real` set and no network access: the tool completed successfully (exit 0), and the badge counts in the output (`badge-deterministic` on all 3 persona cards, `badge-ai` appearing only once as the CSS selector) confirm every persona actually fell back to the deterministic template — the real `urlopen` call failed against this container's egress policy exactly as the mocked unit tests predict, with zero crashes and zero silent data loss.
- Regenerated the final shipped example artifacts (`report.html`, `thesisbreaker.db`) from two clean, realistic demo runs (not the XSS/fallback test runs above) after the history-chart fix, and confirmed the chart now renders correctly on the second run.

Build complete. Success criteria reviewed. All tests passing.
