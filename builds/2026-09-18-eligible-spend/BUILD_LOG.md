# Build Log — Eligible Spend

> **Date:** 2026-09-18
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [Session Start]

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: most recent dated local folder is `2026-06-18-regex-dojo`; its BUILD_LOG.md ends with "Build complete. Success criteria reviewed. All tests passing." — no resume needed.
- Resynced `builds/index.md` and `builds/ideas.md` from the most recent open PR branch (`claude/cool-sagan-xst4xj`, PR #101, 2026-09-16) — local main copies were stale from 2026-06-18; the real catalog has 94 completed builds through 2026-09-16.
- Day of year for 2026-09-18 = 261. `category_index = (261-1) % 9 = 8` → Category I — Life Admin Helper.
- Category I backlog: 4 pending ideas, all unrated → lottery_chance = 25%. Rolled 21/100 (bash `$RANDOM`) → draw. Weighted roll 12/20 → idea #51, "Tri-Agency Grant Budget Compliance Checker." Marked `built` in `builds/ideas.md`.
- Build folder created: `builds/2026-09-18-eligible-spend/`.

### [Research]

- WebSearch confirmed the Tri-Agency Guide on Financial Administration (TAGFA) moved to a principles-based approach in April 2020 — it no longer publishes a simple fixed eligible/ineligible category list, which is what the original backlog idea assumed. Corrected the build's design around this before writing the PRD.
- WebSearch corroborated (across NSERC's own FAQ page summary and multiple university research-office quick-reference pages: Waterloo, Queen's, Acadia, Guelph, UCalgary, Carleton) three core principles (direct cost & attributable to the grant; not normally provided by the administering institution; effective and economical) plus specific named ineligible items: alcohol, hospitality conditional on direct relation to a research gathering, tuition/thesis-related education costs, passport/immigration fees, international driver's licences, home-to-workplace commuting, frequent-flyer-points-purchased airfare reimbursement, sabbatical living expenses.
- Direct fetch of the primary NSERC guide page (`www.nserc-crsng.gc.ca`) was blocked by the build container's egress proxy (`EGRESS_BLOCKED`) — consistent with CLAUDE.md's documented build-environment constraint, not a redesign signal. WebSearch (routed differently) was used as the verification fallback, same pattern as prior builds (Headroom, Almanac).
- Every rule implemented cites its source principle/directive rather than presenting itself as a complete or authoritative eligibility determination. Manual.md and the dashboard both carry an explicit disclaimer to confirm with the institution's research grants office.

### [PRD Written]

- Goal: rule engine + dashboard flagging Tri-Agency-ineligible budget line items, scoped to publicly documented rules only, no overhead-rate math.
- Scope: CSV in, date-range check, always-ineligible keyword rules, conditional (hospitality) rule, default "no blocking rule found" verdict, optional AI-assisted review layer, terminal + HTML + flagged-CSV output.
- See `builds/2026-09-18-eligible-spend/PRD.md` for full detail.

### [Build Phase]

- `src/rules.py`: deterministic rule engine. Date-range check first (short-circuits), then 8 always-ineligible keyword rules (alcohol, tuition, institution-overhead, passport/immigration, international driver's licence, commuting, frequent-flyer airfare, sabbatical living), then a conditional hospitality rule (cleared only by a justification naming a research gathering), then a default missing-justification flag, then "no blocking rule found" (never presented as a guarantee of eligibility). Every rule carries its specific TAGFA principle/directive citation.
- `src/csv_io.py`: CSV parsing with BOM/whitespace handling, `$`/comma-stripped amount parsing, required-column and per-row validation.
- `src/ai_review.py`: optional Claude Haiku layer via `urllib.request` (no SDK), only called for `requires_justification`/`no_blocking_rule_found` items (never for unambiguous rule matches), grounded strictly in the item's own category/description/justification text. Deterministic fallback on missing key or any error; zero network calls attempted with no key.
- `src/report.py`: terminal report, self-contained HTML dashboard, flagged-items CSV export.
- `src/main.py`: CLI entry point (`argparse`), wires the above together.
- Built `sample_data/sample_budget.csv` as a 16-row fixture, hand-computed by category before any code was run: 4 no-blocking-rule, 2 requires-justification, 8 ineligible (one per always-ineligible rule), 2 outside-grant-period (one before start, one after end) -- total budget $26,880.00.

### [Dataviz]

- Loaded the `dataviz` skill before building the HTML report's bar chart. Used the skill's fixed status palette (good `#0ca30c`, warning `#fab219`, critical `#d03b3b`) for the three/four verdict tiers, paired with icon + text label on every use (bar rows and table badges) per the skill's mitigation rule for sub-3:1-contrast status colors on the light surface -- never color alone.
- Ran `scripts/validate_palette.js` against the status colors; it FAILed under the *categorical* lightness-band gate, but `palette.md` documents the status palette as a fixed, separately-governed role with its own known contrast numbers (warning 1.79:1 light) and the icon+label mitigation, which this build already implements -- the categorical FAIL doesn't apply to a status role, so no palette change was made.
- Chose a hand-built CSS bar chart (no Chart.js CDN) since the report is a lightweight 4-bar breakdown -- this also sidesteps the CDN-blocked-in-build-container fallback complexity several prior builds needed.

### [Tests Run]

Tests: 53 passed, 0 failed. (`python -m pytest tests/ -v` from the build folder.)

One test failure during development: `test_html_report_escapes_hostile_payload_in_item_and_justification` initially asserted `html_out.count("<script") == 2`, which is the wrong check -- a hostile payload containing the literal substring `<script>` will always appear once as inert JSON text even when correctly neutralized (the HTML parser only tokenizes `</script` as an exit point while inside an existing `<script>` element, never a nested `<script>` open). Fixed by asserting `html_out.count("</script>") == 2` instead (the real, structural discriminator: only the payload's `</script>` occurrences need neutralizing to prevent early exit) plus a direct check that the neutralized `<\/script><script>` sequence appears in the output. Verified manually in headless Chromium below that this is the correct security property.

### [Manual Verification]

Ran the CLI against `sample_data/sample_budget.csv` with `--grant-start 2026-04-01 --grant-end 2027-03-31`: terminal output matched the hand-computed fixture exactly (16 items, $26,880.00 total, 12 flagged, verdict counts/amounts per category as recorded in PRD.md).

Verified `report.html` in headless Chromium (global npm Playwright 1.56.1, `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`) beyond the automated suite:
- Desktop (1200px) and mobile (375px) viewports: zero console/page errors, zero horizontal overflow, exactly 2 `<script>` tags, 16 rendered rows.
- Search filter ("wine" -> 1 row) and column sort (by amount, ascending, first row $25.00) both worked live.
- A dedicated hostile-payload fixture (`<img onerror>` in `item`, `</script><script>window.__xss2=true;</script>` in `justification`) confirmed: `window.__xss`/`window.__xss2` never set, zero injected `<img>` DOM nodes, exactly the page's own 2 `<script>` tags, zero dialogs, zero console/page errors, and the payload rendered as visible inert text in the table row.

Security checklist (STANDARDS.md): no `.env` files, no real credentials/secrets (grepped `src/` and `tests/` -- only placeholder test fixture strings like `"fake-test-key"`), no `eval()`/`exec()`, no `innerHTML` (grepped clean -- all DOM construction in the dashboard's JS uses `textContent`/`createElement`), no `os.system()`/`subprocess`, all file I/O confined to user-supplied CSV input and user-specified `--out-dir` output (a local CLI tool operated by the user, not a network-facing service).

### [Verify] Step 7 -- Success criteria check

1. All 53 tests pass (zero failures) -- confirmed above.
2. Every always-ineligible and conditional rule cites a specific principle/directive and has a passing test proving both correct firing and non-over-firing -- 16 of the 53 tests in `test_rules.py` cover exactly this, one pair (fire/does-not-fire) per rule.
3. CLI run against the sample fixture produced terminal + `report.html` + `flagged_items.csv` matching the hand-computed expectation exactly (12 flagged, $26,880.00 total) -- confirmed both by `test_cli.py::test_successful_run_produces_report_and_flagged_csv_matching_fixture` and the manual run above.
4. `report.html` opens directly via `file://`, renders correctly at 1200px and 375px with zero console errors, and the hostile-payload fixture confirmed zero script injection -- confirmed manually in headless Chromium above.
5. `--ai` path fully optional: `test_ai_flag_without_api_key_still_completes` and `test_no_api_key_returns_fallback_without_network_call` both confirm zero network calls and a complete report with no `ANTHROPIC_API_KEY` set.

### [Docs] Step 8 -- Documentation complete

- `FutureFeatures.md`: 8 concrete suggestions across quick wins, medium effort, and ambitious extensions.
- `Manual.md`: quick start, full CLI reference, dashboard guide, troubleshooting table, known limitations -- disclaimer repeated from the PRD's scope.

Build complete. Success criteria reviewed. All tests passing.
