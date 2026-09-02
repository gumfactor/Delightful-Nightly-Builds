# Build Log — CiteForge

> **Date:** 2026-09-02

---

### [Orient] Step 0-2 — Session start
- Checked for incomplete builds: last dated folder was 2026-06-18-regex-dojo, which is `complete`. No resume needed.
- Resynced `builds/index.md` and `builds/ideas.md` from the most recent open PR branch (`origin/claude/cool-sagan-5a08cd`, PR #86, 2026-09-01) since local `main` was 2+ months stale (19 builds vs. 79 on the recent branch).
- Category rotation: day of year 245 → index 1 → **B — Productivity Utility**.
- Category B backlog held one pending row (#14), found stale (superseded by last night's Fleet Drift build) and corrected to `skipped` before the lottery, emptying the pool → fresh generation.
- Generated 3 fresh Category B candidates, selected CiteForge. Full reasoning in `WhyThis.md`.

### [PRD] Step 4 — PRD complete
Wrote `PRD.md` — scope, data model, folder structure, testing strategy, and success criteria all filled before any code.

### [Build] Step 5 — implementation
Building in dependency order: models → text_case/names/pages (pure logic) → styles/* → bibtex_parser → crossref → ai_extract → db → cli → render_html.

All style-formatting worked examples were hand-derived from the actual style rules (APA 7 author-list/et-al thresholds, AMA/Vancouver "Family II" inverted-initials format, Chicago Author-Date inverted-first-author convention, ICMJE's page-elision convention) before being encoded as test assertions — not reverse-engineered from whatever the code happened to output.

### [Tests] Step 6 — first test run
138 tests written across 13 files. First run: 1 failure — `test_vancouver_et_al_threshold_seven_authors`. Root cause: `_numbered_common.build_reference` unconditionally appended a period after the author-list string (`f"{authors}."`), but `format_authors_vancouver`/`format_authors_ama` already end their own string in a period when the et-al branch fires (`"...Family5 G, et al."`), producing a double period (`"...et al.."`). Fixed by only appending a period when the author string doesn't already end in one. Also caught and fixed a bad assertion in the same test (`result.endswith("et al.")` — wrong, since the citation continues with title/journal/year after the author segment; the real fix was checking the author segment appears correctly rather than the end of the whole string).

Second run: all 138 tests passed.

[15:00 UTC] Tests: 138 passed, 0 failed. (`python -m pytest tests/ -v`)

### [Verify] Step 7 — live manual verification (not just mocks)
Ran the real CLI end-to-end against a fixture `.bib` file containing a real published APA-verifiable reference (Grady, Her, Moreno, Perez, & Yelinek, 2019, *Psychology of Popular Media Culture*), a real book (Kahneman, 2011), and a deliberately malicious entry with a `</script><script>window.__xss=true;</script>` payload in its title:

- `add-bibtex` parsed all 3 entries correctly; re-running `add-bibtex` on the same file reported "0 added, 3 updated" — confirms dedupe-by-DOI/author-year-title works, not just insert-only.
- `format --style apa` reproduced the real published APA reference for the Grady et al. entry to the letter, except lowercasing "United States" → "united states" — a documented, expected limitation of the acronym/internal-capital-only proper-noun heuristic (no name dictionary), not a bug.
- `format --style ama` / `--style vancouver` correctly applied ICMJE page elision (`207-217` → `207-17`).
- `render` produced a real HTML report. Verified live in headless Chromium (playwright 1.56.1 installed to a scratch directory outside the build folder, matching this catalog's established pattern for Python-only builds needing a one-off browser check): zero page errors, zero dialogs, `window.__xss` never set (confirms the `</script><script>...</script>` payload never executed), the payload rendered as literal visible text in all 4 style blocks, the live search filter correctly narrowed 3 cards to 1, and a 375px mobile viewport showed zero horizontal overflow (`scrollWidth === clientWidth`).

Security checklist (STANDARDS.md):
- No `.env` files, no hardcoded credentials/personal data (grepped for common patterns — none found)
- No `eval()`/`exec()`, no `innerHTML`, no `subprocess`/`os.system` calls anywhere in `src/`
- `ANTHROPIC_API_KEY` read only from the environment at call time, never hardcoded
- Anthropic API call only fires with `--ai` explicitly passed and a key present; only the reference-text line itself (public bibliographic text, not personal data) is sent
- Crossref/Anthropic HTTP transports are fully injectable; every test uses a fake transport, zero live network calls during `pytest`

### [Docs] Step 8 — documentation complete
- `Manual.md`: quick start for all 8 CLI commands, the `--ai` flag's exact gating behavior, all 5 documented limitations, test-run instructions, and the companion Skill
- `FutureFeatures.md`: 7 concrete, scoped suggestions

Build complete. Success criteria reviewed. All tests passing.
