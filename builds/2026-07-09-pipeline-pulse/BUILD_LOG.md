# Build Log — Pipeline Pulse

> **Date:** 2026-07-09
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:09 UTC] Session Start

- Checked `builds/` for an interrupted build (Step 0): most recent dated folder is `2026-06-18-regex-dojo`, whose `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — nothing to resume.
- Read `CLAUDE.md`, `PROFILE.md`, `STANDARDS.md`.
- Today is 2026-07-09, day-of-year 190 → `(190-1) % 9 = 0` → **Category A — Dashboard / Visualizer**.
- Resynced `builds/index.md` from the most recent open PR branch (`claude/cool-sagan-5axlxd`, PR #33, 2026-07-08 "Ledger Lens") via the GitHub MCP tools, since `gh` CLI isn't available in this session — 28 catalog rows on that branch vs. 19 on local `main`.

### [08:12 UTC] Idea Selection

- Filtered `builds/ideas.md` (also resynced from the same branch, 25 entries) to pending Category A ideas: IDs 3, 5, 6. Only ID 3 has a numeric rating (4) → `R=1` → `lottery_chance = min(75, 25+2) = 27%`.
- Rolled a cryptographically random 1–100 via `secrets.randbelow` (not a workflow script, so no restriction on real randomness here): **73** → above 27% → fresh-idea path per Step 2c.
- Noted idea ID 5 ("GitHub Repository Health Scorecard") duplicates the already-built 2026-06-21 build of the same name — would have needed to be skipped even if drawn.

### [08:16 UTC] Network/Environment Reality Check

- Before committing to an idea, probed this session's actual outbound network policy (the proxy documented at `/root/.ccr/README.md`), since several candidate ideas depended on it.
- Findings: `api.open-meteo.com`, `query1.finance.yahoo.com`, `www150.statcan.gc.ca`, `en.wikipedia.org`, `data.sec.gov`, and `eutils.ncbi.nlm.nih.gov` all return `403 Forbidden` at the proxy. Direct GitHub REST calls using the `GITHUB_TOKEN` env var also 403 with `"GitHub access is not enabled for this session"` — that env var is a proxy placeholder, not a usable PAT, in this session. Only `api.github.com` (via the pre-authorized `mcp__github__*` MCP tools), `pypi.org`, `raw.githubusercontent.com`, and `api.anthropic.com` (reachable, but no key set) passed.
- This ruled out most of the "Available with no credentials" data sources in PROFILE.md for tonight's *testable* scope, and ruled out any new GitHub-REST-API-driven dashboard (already covered twice in category A regardless).
- While investigating, confirmed via `git log origin/main` that `main` is still at 2026-06-18, while the catalog goes through 2026-07-08 — roughly three weeks / ~21 branches of nightly builds are unmerged. This became tonight's build.

### [08:19 UTC] PRD Written

- Goal: reconcile `builds/index.md` against this repo's own git history to show merged vs. backlog builds, ranked by wait time.
- Key design decision: use local `git` plumbing (`ls-tree`, `diff --name-only`, `merge-base --is-ancestor`) instead of the GitHub REST API — needs no token, fully testable tonight, and answers the actual question.
- Scope Changes section in PRD.md documents the network findings above in full.

### [08:20 UTC] Build Phase — Core Modules

- `git_inspector.py`: all git calls behind an injectable `runner` (never touches the network in tests), argument-list subprocess calls only (no `shell=True`, no string interpolation into shell).
- `catalog_parser.py`: parses the `## Full Catalog` markdown table into structured records; blank (`—`) ratings parsed as `None`.
- `pipeline_stats.py`: reconciles catalog records against folder sets from git, computes merged/backlog counts, rating coverage, distributions, and a "needs attention" ranked list.
- `ai_brief.py`: optional Claude Haiku briefing (aggregate stats only, no titles/notes sent) with a deterministic fallback template, following the established `ai_client.py` pattern from the 2026-07-08 Ledger Lens build (verified by reading that build's source on its branch).
- `report_html.py` + `main.py`: self-contained dark-mode HTML dashboard (Chart.js 4.4.4 pinned via CDN) and the CLI entry point.

### [08:23 UTC] Tests Run (first pass)

Tests: 46 passed, 0 failed.

### [08:24 UTC] Live Verification Against This Repo

- Ran `git fetch origin '+refs/heads/*:refs/remotes/origin/*'` to pull all 33 remote branches locally, then ran `python3 src/main.py` against the real repo end-to-end (no mocks) with `--no-ai`.
- Bug found: 2 discarded builds (2026-06-09, 2026-06-12) were counted as "backlog" even though they were intentionally never merged — misleading, since "backlog" should mean "needs your review," not "was abandoned on purpose." Fixed by excluding `discarded`/`aborted` statuses from backlog/needs-attention metrics in `pipeline_stats.summarize`, added `test_summarize_excludes_discarded_and_aborted_from_backlog`.
- Screenshot review (Playwright, Chromium) of the regenerated dashboard surfaced the same inconsistency visually in the build table (still showing a red "backlog" badge for discarded builds even though the summary excluded them). Fixed by adding a neutral "closed" badge for unmerged-but-non-actionable builds in `report_html.py`, added `test_render_shows_closed_badge_for_discarded_unmerged_build`.
- Second bug found via the same Playwright check: this sandbox's network policy blocks `cdn.jsdelivr.net`, so `Chart.js` never loads here — and the generated dashboard's single inline `<script>` block let the resulting `ReferenceError` from `new Chart(...)` silently abort the rest of the script, which meant the search box and column-sort **also** stopped working, even though they have nothing to do with charts. Fixed by moving search/sort wiring before chart code and wrapping each chart in a `renderChartOrFallback` helper that shows a text fallback per-card instead of throwing. Verified via Playwright that search/sort work correctly with Chart.js absent, and that the fallback text renders cleanly instead of blank canvases.
- Re-ran against the real repo after both fixes: 28 builds tracked, 5 merged (18%), 21 actionable backlog (75%), oldest unmerged "Investment Thesis Journal" (2026-06-14, 25 days waiting), rating coverage 36% (avg 4.1/10). These numbers were spot-checked by hand against the folder list on `origin/main` (`git ls-tree --name-only origin/main:builds/`) and matched exactly.

### [08:27 UTC] Tests Run (final)

Tests: 48 passed, 0 failed.

### [08:28 UTC] Verify — Step 7 Success Criteria Check

1. ✓ All tests pass, 48 ≥ minimum 15 — confirmed above.
2. ✓ Correctly identifies `main` is behind the catalog with the correct non-zero backlog count and oldest-unmerged build — verified against the real repo, cross-checked by hand.
3. ✓ HTML dashboard opens standalone, renders hero stats, all four chart cards (with graceful text fallback confirmed live in this sandbox), the sortable/searchable table, and the Needs Attention list with working compare links — verified via Playwright screenshots and DOM assertions.
4. ✓ Runs correctly with zero network access and zero `ANTHROPIC_API_KEY` — this *is* the mode it was verified in tonight, since neither was available in this session.
5. ✓ No writes outside `builds/2026-07-09-pipeline-pulse/` by default (`output/` is inside the build folder and gitignored); no other build folder's source was imported — only `builds/index.md` (text) and local git metadata were read, consistent with what Step 0/1 already read every night.

Security checklist:
- No `.env` files, no hardcoded credentials/secrets/tokens.
- No `eval()`/`exec()` anywhere.
- No `innerHTML` from user-controlled data — `html.escape()` used for all catalog text (title/notes/etc.) in `report_html.py`, regression-tested with a `<script>`-tag title.
- No `os.system()` / shell-string subprocess calls — all `git` invocations use argument lists via `subprocess.run(["git", ...])`, never `shell=True`.
- No file paths built from user input beyond explicit, user-supplied CLI flags (`--repo-path`, `--index-path`, `--output`), which is the same trust boundary every prior CLI build in this repo uses for its own arguments.
- All code self-contained in this build's folder; only reads `builds/index.md` and repo-level git metadata (both already-sanctioned reads per Step 0/1 of every nightly session).

### [08:29 UTC] Documentation

- `FutureFeatures.md`: 9 concrete suggestions across quick wins, medium effort, and ambitious extensions, plus known limitations and integration points.
- `Manual.md`: quick start, full CLI flag reference, dashboard reading guide, troubleshooting table, known limitations.

Build complete. Success criteria reviewed. All tests passing.
