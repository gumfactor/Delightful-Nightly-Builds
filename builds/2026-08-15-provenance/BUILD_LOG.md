# BUILD_LOG.md — Provenance

## [08:11 UTC] Step 0 — Check for Incomplete Builds

Local `builds/` only goes up to `2026-06-18-regex-dojo`, but `origin/main` and the 30 open PR branches are far ahead (through PR #71, 2026-08-14). Fetched the most recently created open PR branch (`claude/cool-sagan-0rrer7`, #71 "Earshot") and read its `BUILD_LOG.md`: final entry is `Build complete. Success criteria reviewed. All tests passing.` — not interrupted, nothing to resume. Proceeding to tonight's new build (2026-08-15).

**Process observation (not in scope to fix tonight, logged for the record):** `gh pr list` shows 30 open PRs (#42–#71, 2026-07-15 through 2026-08-14), none merged since PR #38 closed 2026-07-11. Two prior builds in this catalog (Pipeline Pulse, 2026-07-09; Landing Pattern, 2026-08-03) already diagnosed this exact unmerged-backlog problem in detail. Every nightly session branches from `origin/main`, which is still at the 2026-07-11 docs commit — so `builds/index.md` has to be manually resynced from the latest open branch every night (Step 1/Step 9 both do this), but `builds/ideas.md` has no equivalent resync step in CLAUDE.md. That gap is concretely visible tonight: the 2026-08-06 Manuscript Pipeline build log says it corrected two stale `pending` rows (`Cross-Agent Project Activity Workstreams` / `Worklog`, and `Morning Briefing`) to remove them from future lottery pools, but because that correction lived only on PR #63's branch and was never merged to `main`, tonight's fresh `claude/cool-sagan-ucmjrm` branch (cut from `main`) still shows both as `pending`. Re-corrected below before running the lottery.

## [08:14 UTC] Step 1 — Orient

Read `PROFILE.md`, `STANDARDS.md`, and `builds/index.md` synced from the `origin/claude/cool-sagan-0rrer7` branch tip (65 rows, last build 2026-08-14 Earshot, category A).

## [08:16 UTC] Step 2 — Decide

Day of year: 227. `category_index = (227-1) % 9 = 1` → **Category B — Productivity Utility**.

Read `builds/ideas.md`. Two `pending` rows matched Category B: idea #4 (`Cross-Agent Project Activity Workstreams`, rated 9) and idea #7 (`Morning Briefing`, rated 8). Cross-checked both against the full catalog: idea #4 was implemented as **Worklog** (2026-07-10, index.md row 66) and idea #7 as **Morning Briefing** (2026-06-22, index.md row 49, rated 5/10). Both corrected from `pending` to `built` in `builds/ideas.md` before drawing — this empties the Category B pool, so per Step 2c ("If empty, go to Step 2d") the lottery is skipped and fresh ideas were generated. No roll recorded — the pool was empty by inspection, not by a missed draw.

## [08:18 UTC] Step 2d — Fresh Ideas

Scanned the last 10 builds for topic saturation: investment/finance appeared twice (Portfolio Lab 08-09, Quarter Call 08-11) — at the 2-appearance threshold, not yet over it, but close enough to steer away from a third. Academic/research-admin tooling appeared four times (Impact Ledger, Manuscript Pipeline, Waymark, Panel Prep) — treating this as saturated for tonight per the "apply the same check to other domains that have repeated" instruction.

Three candidates generated (see `WhyThis.md` for full reasoning):
1. **Provenance** — batch Canadian-ownership classifier for The Canada List (chosen)
2. Course Material Batch Formatter — rejected, real risk of the "one Claude prompt replicates this" failure mode that scored 2026-06-24's AI Lecture Builder 2/10
3. Multi-Repo Dependency Batch Auditor — rejected, near-duplicate of the already-built `dep-check` (2026-06-19)

Non-winning ideas appended to `builds/ideas.md` as new pending rows (IDs 13–14).

## [08:22 UTC] PRD Written

`PRD.md` complete — CLI batch classifier extending CanFile's (2026-07-20) proven Wikidata rule-engine pattern from single-company lookups to CSV batch processing, the actual shape The Canada List's real ingestion workload needs. Self-contained within this build folder; no code imported from CanFile's folder, per the hard standard against cross-build imports.

## [08:30 UTC] Build

- `src/wikidata.py`: thin `urllib.request`-based Wikidata API client — entity search, claims lookup (country/headquarters/parent-org/owned-by), label resolution. Every function catches malformed/empty responses and returns `None` rather than raising.
- `src/rules.py`: pure deterministic classifier — `classify(resolved_claims) -> (verdict, confidence, evidence)`. Direct P17 country match is highest confidence (0.95); headquarters/parent/owner one-hop fallbacks step down in confidence at each tier; any conflict between two resolved signals (e.g. Canadian P17 but foreign parent) always lands `uncertain` rather than picking a side; zero resolvable claims returns `uncertain` at confidence `0.0`. Zero network access, fully unit-testable on plain dicts.
- `src/store.py`: SQLite cache/history layer, normalized-name keying, append-only versioning (`save_resolution` never overwrites; `get_latest`/`get_history` read the trail).
- `src/ai_enrich.py`: optional Claude Haiku (`claude-haiku-4-5-20251001`) enrichment, matching the `urllib.request`-direct-call pattern the rest of this catalog's optional-AI builds use (verified against 2026-08-06 Manuscript Pipeline's `ai_parse` for consistency). Only ever called for `uncertain` verdicts; unconditional fallback to `None` on any missing key, network error, or malformed response.
- `src/batch.py`: CSV-in/CSV-out orchestration — cache-first per business, `--refresh` bypass, verdict/cache-hit stat aggregation, AI enrichment gated strictly to `uncertain` rows.
- `src/report.py`: self-contained dark-mode HTML batch report — data delivered as a JSON payload inside a `<script type="application/json">` tag with every `</` sequence escaped to `<\/` (preventing the exact premature-tag-close bug class Manuscript Pipeline's build log flagged), consumed client-side via `JSON.parse` + `createElement`/`textContent` only, zero `innerHTML`.
- `src/cli.py`: `classify` and `history` subcommands via `argparse`.
- `skill/SKILL.md`: companion Claude Code Skill wrapping the CLI, matching the precedent Snipvault (2026-08-12) set for Category H — first Category B build in the catalog to ship one.

## [08:40 UTC] Tests Written

51 tests across 7 files, every Wikidata/Anthropic network call mocked via `unittest.mock.patch` on `urllib.request.urlopen` (or the module-level function it wraps) — zero live network access anywhere in the suite:

- `test_rules.py` (12): direct/one-hop verdicts at each tier, conflicting-claim cases, zero-claims edge case, confidence always in [0, 1].
- `test_wikidata.py` (9): search/claims/label parsing against mocked JSON, empty-name and no-QID short-circuits (asserted via `mock_urlopen.assert_not_called()`), malformed-response resilience.
- `test_store.py` (6): normalization, cache round-trip, append-only versioning (`history` preserves both versions, `get_latest` returns the newest).
- `test_ai_enrich.py` (6): zero network calls with no key, verdict-gating, successful/failed/malformed response handling, environment-variable key fallback.
- `test_batch.py` (7): verdict-distribution end-to-end against mocked Wikidata, cache-hit behavior on a second run (asserted via unchanged mock call count), `--refresh` forcing re-resolution while preserving history, missing-name rows skipped not crashed, AI enrichment call-gating to `uncertain` rows only, CSV round-trip column shape.
- `test_report.py` (5): full-document rendering, XSS payload never producing a literal unescaped `</script>` close, JSON-script-tag delivery (no string concatenation), `createElement`/`textContent`-only DOM construction, data round-trip.
- `test_cli.py` (7): no-command usage/exit-1, end-to-end classify with expected output columns, missing-`name`-column and empty-CSV rejection, `--render` HTML output, `history` with/without prior data.

## [08:42 UTC] Tests Run

First run surfaced two real bugs, both fixed before re-running:

1. `test_ai_enrich.py::test_network_failure_falls_back_to_none` — `ai_enrich.enrich()`'s exception handler only caught `urllib.error.URLError`, not the broader `OSError` a real connection failure can raise. Widened the `except` tuple to include `OSError` (which also covers `URLError` as a subclass).
2. `test_batch.py::test_ai_enrich_only_called_for_uncertain_rows` — `classify_batch` was calling `ai_enrich.enrich()` for every cache-miss row when `--ai-enrich` was set, relying on `enrich()`'s own internal verdict check to no-op for `canadian`/`foreign` rows. That technically made zero network calls for non-uncertain rows but violated the PRD's stated design ("enrichment is only ever invoked for uncertain verdicts"). Fixed by gating the call in `batch.py` itself: `ai_enrich.enrich()` is now only ever invoked when `verdict == VERDICT_UNCERTAIN`.

Tests: 51 passed, 0 failed.

## [08:45 UTC] Manual Verification

Ran `python -m src.cli classify tests/fixtures/sample_businesses.csv --render report.html` against the real (unmocked) Wikidata API. As expected per `PROFILE.md`'s documented build-container network policy, `www.wikidata.org` is unreachable from this container (confirmed independently: a direct `curl` to the Wikidata API from this session was denied by the sandbox's network policy) — every business came back `uncertain` at confidence `0.0` with the honest "no claims could be resolved" evidence string, rather than crashing or fabricating a verdict. This is the correct degradation path, not a bug — see `Manual.md`'s Troubleshooting section, which documents it for the user's real (unblocked) runtime. Re-ran `classify` a second time over the same file and confirmed `Cache hits: 3  Cache misses: 0` in the terminal summary, and `history "Acme Canadiana Ltd."` correctly printed the cached resolution's timestamp/verdict/evidence — validating the cache/history layer end-to-end against real (not just mocked) SQLite I/O. Inspected the rendered `report.html`: valid self-contained document, `createElement`/`textContent` present, zero `innerHTML`, business names round-tripped correctly through the JSON payload.

## [08:47 UTC] Security Checklist

Grepped `src/` for `eval(`/`exec(`, `innerHTML`, `os.system`/`subprocess`, and hardcoded `api_key=`/`password=`/`secret=` literals — zero matches (the one `innerHTML` hit is inside `report.py`'s docstring, describing what the code deliberately avoids, not usage). No `.env` file. No credentials in source. `ANTHROPIC_API_KEY` read only from the environment or an explicit function argument, never hardcoded. No file paths built from unsanitized user input — the only file paths are CLI-supplied `--out`/--db`/`--render` arguments the user controls directly, same trust boundary as any other CLI tool. Nothing outside this build folder was modified.

## [08:48 UTC] Verify — Step 7

All 5 PRD success criteria reviewed:

1. **Real-run output shape** — verified structurally (every row got a `verdict`, `confidence` in [0,1], non-empty `evidence`) even though the build container's network policy prevented a real Wikidata resolution; the code path that would populate a genuine QID/country match is covered by `test_wikidata.py` and `test_batch.py`'s mocked end-to-end tests.
2. **Cache hits on repeat runs** — met, verified live (not just mocked): second `classify` run showed `Cache hits: 3  Cache misses: 0`.
3. **Zero Anthropic calls with no key** — met, verified in `test_ai_enrich.py` and manually (no `--ai-enrich` flag was passed in the live smoke test; no `ANTHROPIC_API_KEY` is set in this container).
4. **XSS payload inert in CSV and HTML report** — met, verified in `test_report.py` with a `</script><script>...</script><img onerror=...>` payload.
5. **Tests pass, security checklist clean** — met, 51/51 passing, checklist above.

## [08:49 UTC] Docs

- `FutureFeatures.md`: 7 concrete suggestions.
- `Manual.md`: quick start, command reference, AI-enrichment setup, rule-engine explanation, companion-Skill usage, troubleshooting, test-run instructions.
- `skill/SKILL.md`: companion Claude Code Skill.

Build complete. Success criteria reviewed. All tests passing.
