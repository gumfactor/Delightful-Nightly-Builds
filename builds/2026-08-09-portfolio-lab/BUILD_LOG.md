# Build Log — Portfolio Lab

> **Date:** 2026-08-09
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:15 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: local `builds/` (branch `claude/cool-sagan-8259vy`, at the same commit as `origin/main`, 5ed4d5f) only goes up to `2026-06-18-regex-dojo`, whose BUILD_LOG.md ends with "Build complete. Success criteria reviewed. All tests passing." — nothing to resume there. But `main` is known to lag badly behind actual build history (documented by the 2026-07-09 Pipeline Pulse and 2026-08-03 Landing Pattern builds: dozens of nightly builds sit in unmerged open PRs). Per CLAUDE.md Step 1, fetched the most recently created open PR instead: #65, branch `claude/cool-sagan-dgjedg`, "build(2026-08-08): Panel Prep". Read its `BUILD_LOG.md` directly from that branch — it ends with "Build complete. Success criteria reviewed. All tests passing." and its PR is `mergeable_state: clean`. Nothing interrupted; proceeding to tonight's new build.
- Step 1: read `builds/index.md` and `builds/ideas.md` from PR #65's branch (the current catalog: 58 builds, last build date 2026-08-08).
- Day of year for 2026-08-09 (UTC) is 221. `category_index = (221 - 1) % 9 = 4` → **Category E — Learning Aid**.
- Checked `builds/ideas.md` (from the PR #65 branch) for pending Category E rows: zero — all 18 backlog entries are categories A, B, C, D, F, G, H (no E). Lottery is skipped per Step 2c; proceeding to fresh idea generation (Step 2d).
- Topic diversity check on the last 10 builds (2026-07-30 through 2026-08-08): D, E, F, G, H, I, A, B, C, D — categories well distributed, no topic domain repeats more than twice (investing last appeared 2026-07-27, outside the last-10 window; git/GitHub-workflow tooling appears twice: Waymark 08-07, Landing Pattern 08-03, both Category C/H respectively — not a Learning Aid repeat).
- Reviewed the 4 existing Category E builds: Power Lab (statistical power/sample size), CircuitLab (neuroanatomy), Bayes Lab (Bayesian inference), Signal Detection Lab (SDT/d′/ROC) — all four are neuroscience/statistics trainers. A 5th in that same vein would be redundant even under a different rotation slot. PROFILE.md separately names "Continue learning quantitative investing and algorithmic trading" as an explicit learning goal and "quantitative investing" as a named interest/hobby — untouched by any Learning Aid build to date (investing has only appeared as Dashboard/CLI builds: Investment Research Platform, SiliconWatch).
- Generated three fresh Category E candidates (full reasoning in `WhyThis.md`): (1) **Portfolio Lab** — an interactive Modern Portfolio Theory trainer (diversification, correlation, efficient frontier, Sharpe ratio) driven by real historical price data the user fetches locally via `yfinance`; (2) **Git Internals Playground** — a clickable commit-DAG visualizer teaching branch/merge/rebase/detached-HEAD mechanics; (3) **Agent Orchestration Sandbox** — a visual explainer of pipeline vs. parallel multi-agent execution patterns.
- Chose **Portfolio Lab**: it is the only one of the three tied to a real, named PROFILE.md data source (Yahoo Finance, no credentials required) rather than being purely synthetic/illustrative, it fills a genuine gap (investing has never been taught, only dashboarded), and it reuses the from-scratch-math + Canvas 2D + optional-AI-narrative + quiz-mode architecture that scored well across the other three Learning Aid builds.
- Non-winning ideas appended to `builds/ideas.md` as new pending Category E rows (IDs 19–20).
- Build folder created: `builds/2026-08-09-portfolio-lab/`.
- Verified tooling: Python 3.11.15, pytest 9.1.1 (installed via `pip install --user pytest`), Node 22.22.2, Playwright 1.56.1 (Chromium pre-installed at `/opt/pw-browsers`), `yfinance` 1.5.2 (installs fine from PyPI — only the *live* Yahoo Finance network calls are blocked by this container's egress proxy, which is expected and irrelevant to the design per CLAUDE.md's API-access guidance; `fetch_data.py` is written for the user's runtime and every yfinance call is mocked in tests).

### [08:40 UTC] PRD Written

- Goal: interactive Modern Portfolio Theory trainer (diversification, efficient frontier, Sharpe ratio) driven by real historical market data.
- Scope: `fetch_data.py` (yfinance → `data.js`), a vanilla-JS/Canvas 2D app with five tabs (Explainer, Efficient Frontier, Sharpe & Risk-Free, Correlation Matrix, Quiz), optional direct-browser Claude Haiku explanations with deterministic fallback, `localStorage` persistence.
- Notable decisions: honest "no data yet" onboarding state rather than shipping fake demo numbers (the shipped `data.js` defaults to `PORTFOLIO_DATA = null`, only overwritten by a real `fetch_data.py` run); the analytical efficient frontier is the standard *unconstrained* (shorting-allowed) Markowitz two-fund closed form, explicitly labeled as such in the UI, since a proper long-only QP solver was out of scope for one session (documented in `FutureFeatures.md`).

### [09:05 UTC] Build Phase — Core Math (`src/math.js`)

- Implemented from scratch, no external math library: seeded PRNG (mulberry32, for reproducible Monte Carlo/quiz rounds), Gauss-Jordan matrix inversion with partial pivoting (throws cleanly on a singular matrix instead of returning NaN), two-asset and N-asset portfolio statistics, long-only Monte Carlo sampling via the exponential-normalization simplex trick, the closed-form Markowitz two-fund efficient frontier (A/B/C/D coefficients from Σ⁻¹), and the global minimum-variance portfolio.
- Verified 15 pure-math correctness properties directly in a headless-Chromium test harness (`tests/math-harness.html` + `tests/math.spec.js`) before wiring any UI: matrix inverse against a hand-calculated reference, GMV weights summing to 1, GMV dominance over 500 sampled portfolios, and frontier dominance over the Monte Carlo cloud at matching return levels (an exact, provable property rather than an approximate visual check).

### [09:35 UTC] Build Phase — Data Pipeline (`fetch_data.py`)

- 12-ticker teaching basket chosen deliberately: AAPL+MSFT as a highly-correlated pair (little diversification benefit) and GLD+TLT as historically low/negatively-correlated diversifiers, spanning 8 equity sectors otherwise.
- `align_log_returns`/`compute_stats` built as pure functions over pandas DataFrames, testable against small hand-calculated reference series without any network dependency; `build_dataset` wraps per-ticker fetch failures so one bad ticker degrades gracefully instead of aborting the whole run (minimum 4 successful tickers required).
- 15 pytest tests, every `yfinance`/network call replaced with an injected fake `downloader` — matches CLAUDE.md's "mock all external API calls in tests" requirement exactly; zero live network calls anywhere in the suite.

### [09:50 UTC] Build Phase — Frontend UI (`index.html`, `src/app.js`, `src/styles.css`)

- Five-tab dark-mode UI wired against `math.js` + `PORTFOLIO_DATA`; every displayed number is computed live from the data, nothing hardcoded (verified by the quiz-mode "always live-derived" test).
- Direct-browser optional Claude Haiku calls (session-only key, `anthropic-dangerous-direct-browser-access` header, `claude-haiku-4-5-20251001`) with an unconditional deterministic-template fallback built from the same real numbers, matching the pattern used by several prior builds (CircuitLab, Lexicon, Vizstract).

### [10:05 UTC] Tests Written and Run — first pass

- 16 Playwright UI/integration tests (`tests/app.spec.js`) against a hand-constructed 4-asset test fixture (`tests/fixtures/fixture-data.js`) injected via `page.addInitScript`, covering onboarding state, tab navigation, mixer boundary conditions (0%/100% weight exactly matches single-asset stats), AI mock success + zero-network-call fallback, quiz streak/localStorage persistence, correlation-cell click-through, and an XSS payload in ticker metadata confirmed inert.
- First run: 14 of 16 failed. Root cause: the `.data-meta` div in `index.html` had a `data-testid` but no `id` attribute, so `cacheEls()`'s `document.getElementById('data-meta')` returned `null`, and `renderDataMeta()` threw on `els['data-meta'].textContent = ...` — this halted `init()` before any tab/quiz/mixer wiring ran, cascading into "element not visible" timeouts across almost every other test. Fixed by adding the missing `id="data-meta"`.
- Second run: 15 of 16 passed. The one remaining failure ("quiz mode tracks attempts... across reload") was a real bug in `answerQuiz()`: `btn.classList.add(i === correctIndex ? 'correct' : (i === chosenIndex ? 'incorrect' : ''))` calls `classList.add('')` (throws a DOMException) whenever the user clicks the *correct* answer on their first try, since the other button then falls through to the empty-string branch — silently aborting the rest of the function before `state.quiz.attempts` was ever incremented. The sibling "resets streak on an incorrect answer" test had passed only because clicking the *wrong* answer never hits that empty-string branch. Fixed by restructuring to explicit `if`/`else if` with no empty-class fallthrough.
- Third run: all 32 (16 app + 16 math, after two more tangency tests were added — see below) passed.

### [10:20 UTC] Manual Verification — Efficient Frontier / Tangency Portfolio

- Manually ran `fetch_data.py` against a mocked-but-realistic 12-ticker random-walk price series (not committed — verification only) and rendered every tab in headless Chromium with zero page errors or console errors.
- Visual inspection of the Sharpe & Risk-Free tab caught a real bug the automated tests hadn't: the tangency (max-Sharpe) marker was rendering at the exact edge of the plotted frontier curve regardless of the risk-free-rate slider, meaning `maxSharpeOnFrontier`'s bounded numerical sweep (`frontierReturnRange.min`..`max`, capped at a heuristic multiple of GMV return) was hitting its boundary rather than finding the true interior maximum. Replaced the numerical sweep entirely with the closed-form tangency portfolio formula (Merton 1972: w = Σ⁻¹(μ−rf·1) / 1'Σ⁻¹(μ−rf·1)) — exact, and independent of any display range. Also made the drawn frontier curve's view range dynamically widen (`frontierReturnRange.max = tangency.return * 1.1`) whenever the tangency point would otherwise fall outside it, so the marker is always visible regardless of the slider position.
- Re-verified visually: the tangency marker now sits exactly on the frontier curve, tangent to the dashed Capital Market Line, and moves correctly as the risk-free rate slider changes (spot-checked at 2.0% and 4.5%).
- Added two more math tests for the closed-form tangency portfolio (Sharpe ≥ GMV Sharpe; a true local — and by convexity of the frontier, global — maximum verified against frontier points sampled just above and below it) and removed the now-unused `maxSharpeOnFrontier`.

### [10:35 UTC] Cleanup

- Discovered `fetch_data.py main()`'s `dataset.json` output path was hardcoded to `Path(__file__).parent / "data"` instead of being derived from the `--out` argument — meaning the `test_main_writes_files_and_exits_zero` pytest test was writing a real (test-fixture-sourced, not live-market) `data/dataset.json` into the actual build folder as a side effect, violating "tests are independent — each test sets up and tears down its own state." Fixed to derive from `args.out.parent`; removed the stray generated file; reran the full suite to confirm no further pollution.
- Added a build-local `.gitignore` (`node_modules/`, `test-results/`, `playwright-report/`, `.pytest_cache/`) matching the pattern used by the 2026-06-18 Regex Dojo build, since the root repo `.gitignore` only covers Python bytecode caches.

Tests: 47 passed, 0 failed (15 pytest + 32 Playwright).

### [10:45 UTC] Verify — Step 7 — Success criteria check

1. All tests pass (zero failures) — confirmed above.
2. `fetch_data.py` correctness — 15 mocked pytest tests pass; a manual mocked-but-realistic 12-ticker run produced a valid `data.js` covering all 12 tickers with correctly-shaped mean/volatility/covariance/correlation matrices.
3. Two-asset mixer and efficient frontier mathematically correct — verified by dominance/boundary tests (`math.spec.js`) and by visual inspection (frontier curve visibly bows left of the Monte Carlo cloud; tangency point sits exactly on the curve, tangent to the CML, at multiple risk-free rates).
4. Quiz answers always live-derived, streak/accuracy persist — verified by dedicated tests reading the actual live `quizRound` object and by a reload-persistence test.
5. Onboarding honesty — the shipped `data.js` is `PORTFOLIO_DATA = null`; verified live in headless Chromium that the real committed `index.html` (no fixture injected) shows the onboarding instructions, not fabricated numbers.

Security checklist (STANDARDS.md): no `.env` files; grepped for credential-pattern assignments (none); grepped for `eval(`/`exec(` (none); grepped for `innerHTML` (two hits, both `= ''` literal clears, never assigned from data); grepped for `os.system`/`subprocess` (none); no file paths built from user input; all code self-contained in the build folder.

### [10:50 UTC] Documentation

- `FutureFeatures.md` — 8 concrete enhancements (long-only constrained frontier, custom asset basket, rolling-window history, backtest, short-selling toggle for the cloud, factor decomposition, export, quiz difficulty tiers).
- `Manual.md` — quick start, per-tab walkthrough, AI-explain privacy note, test commands, troubleshooting table.

Build complete. Success criteria reviewed. All tests passing.
