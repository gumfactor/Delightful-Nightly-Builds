# Build Log — TrialScope: Behavioral & Reaction-Time Data QC Explorer

> **Date:** 2026-07-05
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:05 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Checked `builds/` for an interrupted prior session: the most recent local dated folder, `2026-06-18-regex-dojo`, has a final `BUILD_LOG.md` entry of "Build complete. Success criteria reviewed. All tests passing." — nothing to resume.
- Fetched the most recent open PR branch (`claude/cool-sagan-4m88cn`, PR #29, 2026-07-04) to read the current `builds/index.md` and `builds/ideas.md`, since the local `main` copy is weeks behind (25 completed builds exist upstream that aren't in this local checkout). Last build date upstream: 2026-07-04 (Power Lab, category E).
- Day of year for 2026-07-05 is 186. `(186-1) % 9 = 5` → category **F — Data Explorer**. Cross-checked the formula against the last two builds (07-03 → index 3 → D → WeatherSong; 07-04 → index 4 → E → Power Lab) — both matched.
- Checked `builds/ideas.md` for pending F-category rows: 2 found (1 rated, 1 unrated). R=1 → lottery chance = min(75, 25+1×2) = 27%. Rolled 59 via `secrets.randbelow(100)+1` → above threshold → fresh-idea path (Step 2d).

### [08:20 UTC] Environment Reality Check

- Before generating ideas, tested the free public APIs PROFILE.md lists as available (Yahoo Finance, Open-Meteo, PubMed E-utilities, arXiv, Wikipedia, ClinicalTrials.gov, SEC EDGAR, NIH RePORTER). All returned `403 Forbidden` from this session's egress proxy — confirmed via direct Python `urllib` calls AND via a real headless-Chromium `page.evaluate(fetch(...))` call, ruling out a client-side-browser workaround. Only `api.github.com`, `pypi.org`/`registry.npmjs.org`, and `api.anthropic.com` are reachable.
- Also discovered two further constraints: `pip install <anything>` is denied outright by this session's permission policy (`.claude/settings.json` has a blanket `Bash(pip install:*)` deny rule, confirmed by testing with multiple unrelated package names), and `ANTHROPIC_API_KEY` is not actually set in this environment (a real API call returned `401 x-api-key header is required`) — despite CLAUDE.md/PROFILE.md describing both as always available.
- These are real constraints of this specific session, not assumptions to route around. GitHub, while reachable, is also topic-saturated: 4 of the last 10 upstream builds (06-26, 06-28, 06-29, 06-30) already use GitHub activity/CI/commit data as their core dataset.

### [08:30 UTC] Idea Selection

- The highest-rated build in the whole catalog is the Jun 17 Qualtrics Survey Data Inspector (9/10) — a local-file-processing tool with no live API, built directly against the user's own research-data format. That precedent, combined with the network constraints above, pointed toward a local research-data QC tool.
- Decided to build **TrialScope**: a trial-level behavioral/reaction-time data QC explorer. Full rationale and alternatives considered are in `WhyThis.md`.
- Two non-winning fresh ideas appended to `builds/ideas.md` (IDs 17–18, category F, today's date, status pending).

### [08:35 UTC] PRD Written

- Goal: local trial-level CSV in, QC-flagged interactive HTML report + cleaned CSV + exclusions CSV out.
- Scope: auto-detecting column mapping, configurable QC flag rules, per-subject/condition stats, hand-drawn SVG charts (no external chart library — zero network dependency in the shipped artifact), AI/template methods paragraph.
- Notable constraint recorded in PRD's Scope Changes: AI layer would use `requests` rather than the `anthropic` SDK, since `pip install` is unavailable in this session. (This was revised again during the build phase — see below.)

### [09:10 UTC] Build Phase — Core Logic

- Implemented `src/parsing.py`: CSV loading, column auto-detection against common naming aliases per role, explicit CLI override support, numeric/boolean coercion with a warning counter for malformed cells, clear `ColumnResolutionError` messages when a required column can't be resolved.
- Implemented `src/qc.py`: `SubjectSummary`/`ConditionSummary` aggregation, all five QC flag rules, binomial chance-level test by hand with `math.comb` (no `scipy`), configurable exclusion-threshold logic.
- **Design correction found while writing tests:** the initial outlier rule compared each trial's RT to `subject_mean ± N×population_SD`, where the SD was computed from a set that included the outlier trial itself. Working through concrete numbers revealed this is mathematically close to unusable: for one outlier among `n` samples, the maximum possible mean/SD z-score is bounded by `sqrt(n-1)`, *no matter how extreme the outlier's value is* — so at a typical n≈10 trials, a default 3-SD threshold could essentially never fire. Fixed by switching to a modified z-score using each subject's median and MAD (median absolute deviation, Iglewicz & Hoaglin's standard robust-outlier method), which stays sensitive regardless of sample size since a single extreme value barely moves the median/MAD. Default threshold changed from 3.0 to the conventional 3.5. Verified the fix with a dedicated regression test (`test_robust_outlier_flag_triggers_even_though_meansd_zscore_would_be_masked`) that reproduces the exact masking scenario. PRD.md updated to describe the corrected method.
- **Second design correction:** initially wrote `src/ai_summary.py` against the `requests` library (already present for the system Python at `/usr/local/bin/python3`). Running the test suite revealed that `pytest`'s CLI runs from a separate `uv`-managed tool environment (`/root/.local/share/uv/tools/pytest/bin/python`) that does *not* have `requests` installed, and `pip install` is blocked for both environments regardless. Rewrote `ai_summary.py` to use stdlib `urllib.request`/`urllib.error` instead, removing the third-party dependency entirely — `requirements.txt` is now stdlib-only, consistent with several prior Python builds in this catalog (e.g. Qualtrics Survey Data Inspector, dep-check).
- Implemented `src/report.py`: self-contained dark-mode HTML report (inline CSS/JS, hand-drawn inline SVG bar/histogram/line charts — no CDN, no external request of any kind), `cleaned_data.csv` and `exclusions.csv` writers.
  - **Caught before testing:** an early version of the subject-row HTML builder mixed an f-string with a trailing `.format(excl=...)` call on the same concatenated string literal. Since f-string substitutions (including HTML-escaped user data) happen before the literal concatenation, any subject ID or flag text containing a literal `{` or `}` character would have broken `.format()`'s placeholder parsing and crashed report generation on attacker-influenced input. Rewrote to build the `data-excluded` attribute value as a plain variable inside a single f-string, with no `.format()` call at all.
- Implemented `src/trialscope.py`: CLI (`argparse`) with documented defaults, orchestrates parsing → QC → AI summary → report generation. Simplified an initial over-engineered `--no-ai` branch that referenced a nonexistent `__wrapped__` attribute down to a direct call of `_deterministic_paragraph`.

### [09:40 UTC] Tests Written

- `tests/fixtures/sample_trials.csv`: 3 subjects × 8 trials across 2 conditions, including a chance-level-performing subject and two deliberately malformed cells (a blank RT, a non-numeric accuracy value) to exercise the coercion/warning path.
- `tests/test_parsing.py` (10 tests), `tests/test_qc.py` (18 tests) — using directly-constructed `Trial` objects for precise, hand-verified QC rule boundaries rather than relying on the shared CSV fixture for exact-value assertions — `tests/test_ai_summary.py` (8 tests, including one genuine unmocked network call against the real Anthropic API with a deliberately invalid key, verifying the real HTTP/error-handling plumbing rather than only a mocked path), `tests/test_report.py` (8 tests, including HTML-escaping of a malicious subject ID and a "no external network reference" structural check).
- `tests/conftest.py` centralizes the `sys.path` setup for importing from `src/` so it isn't duplicated across four test files.

### [09:55 UTC] Tests Run

Tests: 45 passed, 0 failed. (`pytest tests/ -v`, run from this build's folder.)

### [10:00 UTC] Manual CLI Verification

Ran `python3 src/trialscope.py tests/fixtures/sample_trials.csv --out-dir <scratch>` and confirmed: `report.html`, `cleaned_data.csv`, `exclusions.csv` all produced; report content matches expected subject/condition/flag counts; `--no-ai` flag works; missing-file and missing-required-column CLI errors exit cleanly with code 1 and an actionable message; an empty (header-only) input CSV produces a valid "no data" report with exit code 0 rather than crashing.

### [10:05 UTC] Verify — Step 7

1. All tests pass — confirmed above.
2. CLI run against the fixture produces all three output files — confirmed above.
3. `report.html` is fully self-contained: no `http://`/`https://` substrings anywhere in the generated file (checked with `grep -c`), no `fetch(`/`XMLHttpRequest`; all charts are inline SVG built from computed values.
4. Every QC threshold (RT floor, MAD-z multiplier, ceiling ms, chance rate/alpha, completion fraction, exclusion flag-count) is a CLI-configurable `QCConfig` field computed live against the input — none are hardcoded per-dataset.
5. Report includes the "Participants & Data Quality" paragraph via the deterministic template (no Anthropic API key present in this environment, confirmed directly); the AI code path is covered by both a mocked-response test and one genuine (unmocked) call to the real API.
- Security checklist: no `.env` files; no hardcoded credentials (the one API-key string in the test suite, `"fake-test-key"`/`"sk-ant-invalid-test-key"`, is a deliberately fake literal used only to exercise error-handling paths, never a real credential); no `eval`/`exec`; no `innerHTML` assignment from unescaped data (`report.py`'s `esc()` helper HTML-escapes every user-derived value, and a dedicated test confirms a malicious subject ID like `<img src=x onerror=alert(1)>` is escaped in the output); no `os.system`/`subprocess` calls anywhere in the build; file paths are only ever the CLI-provided input/output paths; all code confined to this build's folder.

### [10:10 UTC] Documentation

- `FutureFeatures.md`: 7 concrete suggestions across quick-win/medium/ambitious tiers.
- `Manual.md`: quick start, column-detection reference, full QC-flag/CLI-option reference, troubleshooting (including an honest note about the chance-level test's low power at small trial counts), known limitations.

Build complete. Success criteria reviewed. All tests passing.
