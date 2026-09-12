# Build Log — Throughline

### [Step 0] Incomplete-build check

Local checkout's `builds/` only goes up to 2026-06-18 (this session's designated branch was created from `main`, which is far behind). Checked the most recent open PR branch instead (`claude/cool-sagan-hrldlh`, PR #96, 2026-09-11 "GradeLine") — its `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." No incomplete build to resume. Proceeding with tonight's new build.

### [Step 1] Orient

Read `PROFILE.md`, `builds/index.md` (resynced from PR #96 branch — 89 total builds, 86 complete, 3 discarded, last build 2026-09-11), and `STANDARDS.md`.

### [Step 2] Decide

Day-of-year 255 → category index 2 → Category C (Personal Knowledge Tool). Lottery: 5 pending Category C backlog ideas, all unrated → 25% draw chance, rolled 91 → no draw, fresh idea generation. Full reasoning in `WhyThis.md`. Chose **Throughline**: a local knowledge base of the user's own publications and live citation counts (Semantic Scholar Graph API, free/no-auth), deterministic thematic clustering, citation-growth tracking, and an optional AI-written research narrative per cluster.

### [Step 3-4] PRD

Wrote `PRD.md` before any code — goal, scope, tech stack, SQLite schema, folder structure, testing strategy, and 6 success criteria.

### [Build] Implementation

Implemented `src/semantic_scholar.py` (Graph API client — author search + author/papers fetch, transport-injected for testing, HTTP 429/network/malformed-JSON error handling), `src/storage.py` (SQLite: author, papers, citation_snapshots, clusters, cluster_papers, narratives — upsert-by-paperId with an append-only snapshot per sync), `src/cluster.py` (fully deterministic, stdlib-only TF-IDF-style keyword extraction + Jaccard-similarity union-find clustering — no ML libraries), `src/narrative.py` (deterministic template + optional Claude Haiku synthesis via `urllib.request` against `https://api.anthropic.com/v1/messages`, unconditional fallback on any error), `src/render.py` (self-contained dark-mode HTML dashboard, JSON-in-`<script>` payload with `</script` escaped, DOM built exclusively via `createElement`/`textContent`, Chart.js 4.4.4 CDN with a DOM-table fallback), `src/cli.py` (argparse: lookup/sync/cluster/narrative/growth/render/papers), `main.py` entry point, and a companion Claude Code Skill (`skill/SKILL.md`) following this catalog's established precedent (GradeLine, Promptbook, Grant Vault, etc.).

### [Math check] Deterministic clustering — hand-verified worked example

Before trusting the clustering algorithm, hand-computed its output for a 5-paper corpus (2 stress/cortisol papers, 2 regex/pattern papers, 1 unrelated boat-design paper) by tokenizing each title+abstract, computing corpus-wide document frequency, scoring `tf * idf` per term with `idf(t) = ln((n_docs+1)/(df(t)+1)) + 1`, and taking each paper's top-6 keywords (ties broken alphabetically). Worked by hand: the two stress papers' top-6 sets share exactly `{cortisol, stress}` (Jaccard 2/10 = 0.2), the two regex papers' sets share exactly `{matching, pattern}` (Jaccard 2/10 = 0.2), and the boat paper shares nothing with either — so at `similarity_threshold=0.2` the expected grouping is `{stress_a, stress_b}`, `{regex_a, regex_b}`, `{boat}`. Encoded this exact worked example as `test_cluster_papers_realistic_corpus_groups_by_theme` and it passed on the first run, confirming the arithmetic and the implementation agree. A second, simpler worked example with hand-picked words (`test_cluster_papers_groups_by_hand_verified_jaccard_overlap`) cross-checks the Jaccard/union-find logic in isolation from TF-IDF tie-breaking.

### [Tests] Step 6 — Test run

`/root/.local/bin/pytest tests/ -v` — the sandboxed `python3` had no `pytest` installed and `pip install` was denied by the session's permission settings; found and used the pre-existing `/root/.local/bin/pytest` (pytest 9.0.2) instead.

Tests: 60 passed, 0 failed, first run — no fixes needed.

### [Manual Verification] End-to-end smoke test

Ran the real CLI end-to-end (not just pytest mocks) via a small driver script: `sync` (injected fetch returning 5 fixture papers, one with a `</script><script>window.__xss=true;</script>` hostile title/abstract), a second `sync` with bumped citation counts, `cluster` (correctly grouped into the same 3 clusters as the hand-verified worked example above, using real fetched-shaped data), `narrative` (deterministic mode, correct totals), `growth` (correct `+5` delta for every paper after the second sync), and `render` (11.4 KB self-contained HTML).

Live-checked the rendered dashboard in the container's pre-installed headless Chromium (global npm Playwright 1.56.1, `executablePath` pointed at `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`, matching this catalog's established pattern for Python-only builds): zero page errors, zero dialogs, `window.__xss` never set, exactly 3 `<script>` tags present (the page's own CDN/JSON-payload/inline-logic tags — no 4th, injected one), the hostile title rendered as inert visible text, and the live search filter correctly narrowed 5 rows to 2 on a "stress" query. Confirmed the Chart.js CDN is genuinely blocked by this build container's egress proxy (`window.Chart` was `undefined`) and that the DOM-table growth fallback correctly rendered all 5 rows instead. A 375px mobile viewport check showed zero horizontal overflow (`scrollWidth === clientWidth === 375`).

### [Verify] Step 7 — Success criteria check

1. ✓ `lookup` prints a disambiguated candidate list and never auto-selects — verified by `test_cmd_lookup_prints_candidates` and the API-error/no-results tests
2. ✓ `sync` upserts without duplicating — verified by `test_upsert_papers_updates_existing_without_duplicating` and the live smoke test's second sync
3. ✓ `cluster` deterministically groups the hand-verified fixture corpus and is stable across repeated runs — verified by the worked-example test and `test_cluster_papers_is_deterministic_across_runs`
4. ✓ `narrative` produces correct deterministic output with zero network calls with no API key, and falls back correctly on any AI error — verified by 5 dedicated narrative tests including an assertion transport that raises if called
5. ✓ `render` is safe against script injection (verified by 3 dedicated tests plus the live headless-Chromium check) and correctly displays clusters/papers/growth
6. ✓ All tests pass: 60 passed, 0 failed (`python -m pytest tests/ -v` via the installed pytest)

Security checklist run against all created files: no `.env`, no hardcoded credentials/secrets (the only "API key" references are `os.environ.get(...)` reads), no `eval()`/`exec()`, no `innerHTML` assignment from data-derived text (verified by `test_render_dashboard_never_uses_innerhtml_for_dynamic_text`), no `os.system()`/`subprocess` calls anywhere in the build, no file-path traversal (the only user-supplied paths are `--db`/`--output`, used only to open files the user explicitly named, never derived from remote data), all files within the build folder. No personal data hardcoded — the author's name/id is always a runtime CLI argument, never baked into source.

### [Docs] Step 8 — Documentation complete

- `FutureFeatures.md`: 6 concrete enhancements
- `Manual.md`: usage guide, command reference, sample run, test command

Build complete. Success criteria reviewed. All tests passing.
