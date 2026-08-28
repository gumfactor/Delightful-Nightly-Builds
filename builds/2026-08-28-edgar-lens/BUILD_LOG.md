# Build Log — EDGAR Lens

> **Date:** 2026-08-28
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:16 UTC] Session Start

- Checked Step 0: most recent dated local folder was `2026-06-18-regex-dojo`, complete. But `gh`/GitHub MCP showed 30 open build PRs going up to #82 (2026-08-27, Regression Lab), all merge-clean, none needing resumption — that PR's own BUILD_LOG ends "Build complete. Success criteria reviewed." Local `main`/working branch was already at the same base commit as PR #82, so nothing to resume; local `builds/index.md`/`ideas.md` were pulled fresh from PR #82's branch (`claude/cool-sagan-4m4ixe`) before proceeding, since the committed-on-main copies were ~2 months stale.
- Read PROFILE.md, the freshly-synced `builds/index.md` (111 prior builds) and `builds/ideas.md`, STANDARDS.md.
- Day of year 240 → category rotation index `(240-1) % 9 = 5` → Category F (Data Explorer).
- Category F backlog: 3 pending rows (#10, #20, #21), all unrated → 25% lottery chance. Rolled 29 (Python `random.randint(1,100)`) → missed, fresh generation.
- Topic diversity check on last 10 builds (2026-08-16 → 2026-08-27): investment/finance appeared once (Trading Book) — not saturated.
- Decided to build: EDGAR Lens — SEC EDGAR XBRL financial-statement explorer with deterministic multi-year anomaly flagging.
- Build folder created: `builds/2026-08-28-edgar-lens/`.

### [08:16 UTC] PRD Written

- Goal: pull real multi-year financial statements from SEC EDGAR's free XBRL API and surface deterministically-flagged anomalies (revenue decline, margin compression, leverage spike, negative equity, swing to loss) in an HTML dashboard.
- Scope: `sync`/`list`/`show`/`flags`/`render` CLI, SQLite persistence with dedupe, tag-resolution layer over inconsistent US-GAAP tags, optional Claude Haiku one-line anomaly narrative with unconditional deterministic fallback.
- Notable constraint: SEC EDGAR requires a self-identifying `User-Agent` header. STANDARDS.md forbids hardcoding a real email, so the default `User-Agent` is a generic non-personal placeholder, configurable via `--user-agent`/`EDGAR_USER_AGENT` for the user's own runtime use.

### [08:17 UTC] Build Phase — data layer

Built `src/extract.py` (tag-resolution + fiscal-year alignment over SEC XBRL companyfacts), `src/metrics.py` (deterministic ratios and 5 named-threshold anomaly flags), `src/storage.py` (SQLite upsert schema), `src/edgar_client.py` (rate-limited urllib client with a configurable, non-personal default User-Agent), `src/ai_narrative.py` (optional Claude Haiku one-sentence anomaly narrative, aggregate-numbers-only input, unconditional deterministic fallback), `src/render.py` (self-contained dark-mode dashboard, JSON-in-script-tag with `</` escaping, DOM built via createElement/textContent only), and `src/cli.py` + `main.py` (sync/list/show/flags/render).

### [08:26 UTC] Tests Run

Wrote a hand-verifiable fixture (`tests/fixtures/sample_companyfacts.json`, 4 fiscal years) whose values were computed by hand before writing assertions: a duration-bounds trap (a 214-day stub period filed *later* than the genuine annual fact, to catch a broken duration filter that would otherwise pick it via the latest-filed tie-break), a 10-Q entry mixed into the same tag's fact list, and a restated FY2023 revenue fact where the later `filed` date must win.

Tests: 81 passed, 0 failed. (`python -m pytest tests/ -v`)

### [08:28 UTC] Manual Verification

A manual smoke test against the fixture found a wording bug the 81 automated tests hadn't checked for: three anomaly detail strings used Python's default numeric formatting on an already-signed delta, producing double negatives ("Revenue fell -15.0%", "a net loss of $-50,000,000", "equity ... ($-20,000,000)"). Fixed by using `abs()` in the three affected f-strings in `metrics.py`; re-ran the full 81-test suite (all still passing, since no test had asserted the exact buggy wording) and manually re-verified the corrected narrative text.

Live end-to-end verification in headless Chromium (global Chromium binary at `/opt/pw-browsers`, driven via a scratch `npm install playwright@1.56.1` kept entirely outside the build folder — not shipped, since this is a Python CLI build with no browser-test requirement) against a rendered dashboard seeded with the fixture data plus a second company whose ticker/company-name pair used a live `</script><script>window.__xss=true;</script>` payload:
- Zero page errors other than the CDN's own blocked-request network error (expected: this build container's egress proxy blocks `cdnjs.cloudflare.com`, confirmed via `window.Chart === undefined`)
- Zero dialogs, `window.__xss` never set — the malicious company name rendered as literal, inert text in the comparison table
- Exactly 3 `<script>` tags present in the live DOM (Chart.js CDN tag, JSON data tag, app-logic tag) — no injected script node from the payload
- The Chart.js-unavailable DOM-table fallback engaged correctly and showed the real per-year revenue/net-income figures
- A first 375px-mobile-viewport pass found a real bug the 81 automated tests hadn't caught: `document.documentElement.scrollWidth` (391px) exceeded `clientWidth` (375px) by 16px. Walking every element's bounding rect isolated the cause to `#company-select` (354px wide, right edge at 391px) — a native `<select>` sizes itself to its longest `<option>` text, and the QA fixture's company-select option included the full malicious `EVIL -- </script><script>...` string. Fixed by adding `max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;` to the `select` rule in `render.py`; re-rendered and re-verified live that `scrollWidth === clientWidth` (375 === 375) at the same viewport. The wide comparison table itself (824px) correctly stays a contained horizontal scroll inside its own `overflow-x: auto` panel and does not contribute to page-level overflow

### [08:31 UTC] Verify — Step 7

Success criteria (see PRD.md) reviewed against the fixture-driven test suite and the live QA pass above:
1. All tests pass, 81/81 (exceeds the 15-test minimum) — met
2. `sync` against a mocked EDGAR response resolves the ticker, extracts via the tag-resolution chain, and a second sync upserts without duplication — met (`test_sync_resolves_ticker_and_stores_financials`, `test_sync_is_idempotent_on_rerun`)
3. Every anomaly type fires on a triggering fixture and not on a non-triggering one, including exact-threshold-boundary cases — met (`test_*_threshold_boundary` tests plus the full fixture sequence test)
4. `render` produces a self-contained `dashboard.html` opening directly with zero build step, showing the comparison table and trend chart/fallback, with script-injection payloads confirmed inert both at the string level (pytest) and live in a real browser — met
5. `render --ai` omitted (default, no `--ai` flag) makes zero network calls with no `ANTHROPIC_API_KEY`, confirmed both by a `spy_urlopen` that raises `AssertionError` if ever called (pytest) and by the CLI-level `test_render_produces_dashboard_file_without_ai` test using a network-call-forbidding fake — met

Security checklist (STANDARDS.md): no `.env` files; no real credential/secret values (the Anthropic API key is read from `ANTHROPIC_API_KEY`/env only, never a literal); no `eval()`/`exec()`; no `innerHTML` from data (render.py builds the DOM exclusively via `createElement`/`textContent`); no `os.system()`/`subprocess`; no user-controlled file paths; no reads outside the build folder. The SEC `User-Agent` default is a generic non-personal placeholder (`test_default_user_agent_contains_no_real_personal_email` asserts this), configurable by the user at runtime via `--user-agent`/`EDGAR_USER_AGENT` for their own SEC-compliant identification.

Build complete. Success criteria reviewed. All tests passing.

### [08:42 UTC] Post-PR Review — Codex Automated Review

An automated Codex review on PR #83 raised 5 findings (3 P1, 2 P2) plus one general comment. Verified each against the actual code before acting, per the "bot findings are bug reports, verify then fix" rule:

1. **P1 -- 10-K/A amendments silently rejected.** `_is_annual_fact` checked `form == "10-K"` exactly, excluding `"10-K/A"` entirely -- so a genuine financial restatement filed as an amendment would never be picked up on re-sync, contradicting the PRD/Manual's own claim that a re-sync "reflects the latest-filed values... after a 10-K/A restatement." Confirmed as a real bug: the code and the docs disagreed. Fixed by accepting both `"10-K"` and `"10-K/A"` in a new `ANNUAL_FORMS` set, letting the existing latest-`filed`-wins tie-break correctly prefer the amendment.
2. **P1 -- Tag resolved once per company, not per year.** `resolve_tag()` picked a single tag per concept for the *whole* company based only on "does this tag exist with a USD unit" -- if that tag's annual coverage was incomplete (e.g. a filer switched revenue tags after adopting ASC 606), every year the winning tag didn't cover came back `None`, even when a lower-priority candidate tag had the data. Confirmed as a real, plausible bug given SEC XBRL's well-documented history of filers changing tags over time. Fixed by rewriting extraction to merge *all* candidate tags per fiscal year (`_merge_candidate_tags`) -- a higher-priority tag wins a year it covers, a lower-priority tag only fills years the higher-priority one is missing. `resolve_tag()` itself is kept as a small, still-independently-tested utility, no longer used to gate extraction.
3. **P1 -- Facts keyed by SEC's `fy` field, which describes the filing, not necessarily the individual value's own reporting period.** A single 10-K's XBRL can include comparative prior-year figures that are not guaranteed to carry a fiscal year distinct from the filing's own `fy`. Given genuine uncertainty about this without live SEC access from this build container, treated it as real: rewrote extraction to group facts by their actual `(start, end)` period first (so two different periods can never collide even if `fy`/`filed` match), then derive the fiscal-year *label* from that period's own `end.year` rather than trusting `fact["fy"]` verbatim. Verified this doesn't change any existing fixture-derived test expectation (the fixture's `fy` always happened to equal `end.year`, the common case), then added a dedicated test with a deliberately mismatched `fy` field to prove the derivation, plus a test with two comparative-year facts sharing one `fy`/`filed` to prove they land in separate fiscal years.
4. **P2 -- YoY metrics computed across a fiscal-year gap.** `compute_yearly_metrics`/`flag_anomalies` compared each row only to the previous *row in the list*, not the previous *fiscal year* -- a gap (e.g. FY2021 -> FY2023 because FY2022 had no usable tag data, now much rarer after fix #2 but still possible) would silently get labeled and flagged as a single year's change. Confirmed as real. Fixed by gating every YoY/delta computation, including the `swing_to_loss` check in `flag_anomalies` (same underlying bug, not explicitly flagged but identical root cause), on `fiscal_year == prev_fiscal_year + 1`.
5. **P2 -- Script-tag escaping claimed to miss uppercase `</SCRIPT>` variants.** Checked directly: `_escape_for_script_tag` replaces every literal `"</"` substring unconditionally -- it never tests for the word "script" at all, so case only affects letters that were never part of the match condition in the first place. Verified with a standalone Python check (`</script>`, `</SCRIPT>`, `</ScRiPt>` all correctly neutralized) before concluding this finding does not apply to this implementation. No code change; added a regression test (`test_escape_for_script_tag_is_case_insensitive`) and a live-payload test with mixed-case tags to codify why, and left a reply on the review comment explaining the verification rather than silently dismissing it.

Added 11 new tests (81 -> 92) targeting these fixes directly, including hand-constructed facts proving each bug's failure mode existed before the fix. Full suite re-run: 92 passed, 0 failed. No existing test's expected value changed.

Build complete. Success criteria reviewed. All tests passing.
