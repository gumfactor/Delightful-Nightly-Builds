# Build Log — Bridgework

[Step 0] No incomplete build found. Most recent local folder (2026-06-18-regex-dojo) has a completed BUILD_LOG. Checked open PRs via GitHub MCP; most recent is #47 (2026-07-20, CanFile) — resynced `builds/index.md` and `builds/ideas.md` from that branch before starting, since main is weeks behind.

[Step 1] Read PROFILE.md and STANDARDS.md. Day of year for 2026-07-21 = 202 → category_index = (202-1) % 9 = 3 → Category D (Creative/Generative).

[Step 2] Lottery: 2 pending Category D backlog ideas (#15, #16), both blank rating → R=0 → lottery_chance = 25%. Rolled 46 (python random, no seed) → 46 > 25 → fresh idea generation.

Generated 3 fresh Category D candidates, picked "Bridgework" (analogy/metaphor generator for the user's Stress and Coping book + empathy/AI public education work). Full reasoning in WhyThis.md. Non-winners (Course Case Vignette Forge, Public Talk Opener Generator) appended to builds/ideas.md as IDs 34-35. Backlog idea #15 marked `built` with a cross-reference note (same precedent as CanFile → #13).

[Step 3] Created builds/2026-07-21-bridgework/ with src/ and tests/ subfolders.

[Step 4] PRD.md written before implementation code (taxonomy.py/novelty.py/storage.py were drafted in parallel while finalizing the design in this session, but PRD reflects and was finalized to match the actual implementation before generator/ai_client/render/cli were written).

[Step 5] Building taxonomy: 20 concepts (10 stress, 6 empathy, 4 psychopathy) each tagged with one of 7 mechanism types, 12 everyday domains each supporting 2-3 mechanism types. Verified: 97 valid (concept, domain) pairs of 240 possible, 291 valid (concept, domain, audience) triples, zero orphan concepts or domains.

Psychopathy concepts (callous-unemotional traits, threat-processing hyporeactivity, instrumental/reactive aggression, reward hypersensitivity) framed deliberately in clinical, dimensional, non-stigmatizing research terms per the user's own forensic neuroscience research area — each carries an explicit caveat field warning against over-generalizing a population-level research construct to any individual.

Built `novelty.py` (Jaccard token-overlap + triple-usage ranking), `storage.py` (append-only SQLite, never overwrites), `ai_client.py` (optional Claude Haiku polish via raw `urllib` POST, `claude-haiku-4-5-20251001`, returns `None` on any missing-key/network/parse failure so the caller falls back unconditionally), `generator.py` (deterministic templates — genuinely distinct prose per audience register, verified — plus orchestration), `render.py` (self-contained dark-mode HTML viewer; all entry text delivered as JSON and inserted client-side via `textContent`/`createElement`, never `innerHTML`; embedded JSON escapes `</` sequences so a payload's own closing tag can never break out of the `<script>` data block), `cli.py` (7 subcommands), `main.py`.

[08:10 UTC] Wrote 86 tests across 7 files (test_taxonomy, test_novelty, test_storage, test_ai_client, test_generator, test_render, test_cli). First run: 85 passed, 1 failed — `test_render_html_escapes_script_tag_in_analogy` asserted the substring `<script>alert` never appears anywhere in the page, which is stricter than the actual security property (text inside a JSON payload inside our own `<script>` block is inert regardless of what substrings it contains — the real risk is only the payload's own `</script>` prematurely closing our block). Rewrote the test to assert the actual property: extracting the JSON between the data `<script>` tags via non-greedy regex and confirming it still parses as valid JSON containing the untouched original string — this would fail if the escaping were broken, since the malicious `</script>` would truncate the extraction and produce invalid JSON. Fixed test; not a change to `render.py` itself (the escaping implementation was already correct).

[Step 6] Tests: 86 passed, 0 failed. `python -m pytest tests/ -v` from the build folder.

[Step 7 — Manual verification] Ran the CLI end-to-end outside pytest: `generate --count 8 --no-ai --seed 42` produced 8 structurally distinct analogies; `generate --count 20 --no-ai --seed 7` brought the library to 28 entries with zero duplicate triples; `list`, `show`, `stats`, and `export --id 1` all produced correct, well-formed output; `render` wrote a 52KB self-contained `data/bridgework.html`.

Live XSS verification in headless Chromium (Playwright, pre-installed `/opt/pw-browsers/chromium`): inserted a row directly into the SQLite library with a malicious `concept_name` (`<script>window.__xss=1</script>`), `hook` (`<img src=x onerror=window.__xss2=1>`), and `analogy` (containing a literal `</script><script>window.__xss3=1</script>`), then re-rendered and loaded the HTML. Result: zero `dialog` events, zero `pageerror` events, `window.__xss`/`__xss2`/`__xss3` all remained `undefined` after load and after dispatching a click on the malicious card to open its detail view. The JSON-escaping regex test in `test_render.py` (extracting and `json.loads`-ing the data block) independently confirms the same property. `.card`/`#detail` DOM inspection confirmed zero `<script>`/`<img>` elements were created from the payload — it rendered only as escaped, inert text (`&lt;img src=x onerror=...&gt;`). Deleted the malicious test row and the generated `data/` directory contents afterward; nothing under `data/` is staged or committed (runtime-generated, excluded from `git add`).

Verified success criteria from PRD.md:
1. ✓ `generate --count 8` inserted 8 new valid rows respecting mechanism-type compatibility (verified via `--seed` runs above and `test_cli.py`/`test_taxonomy.py`).
2. ✓ Regenerating a triple never overwrites — the live 28-entry run above stayed within already-generated ids without ever reducing the row count, and `test_storage.py::test_regenerating_same_triple_never_overwrites` explicitly generates the identical (concept, domain, audience) triple twice and confirms both rows persist under distinct ids.
3. ✓ No `ANTHROPIC_API_KEY` was set anywhere in this session; every command above ran to completion with complete, well-formed template text — confirmed live and by `test_generator.py`/`test_ai_client.py`.
4. ✓ `render` produced a self-contained file opened directly via `file://` with no server; script-injection attempt verified inert live in headless Chromium (above) and in `test_render.py`.
5. ✓ 86/86 tests pass, zero failures.

Security checklist (STANDARDS.md): no `.env` files; grepped `src/`, `tests/`, and all `.md` files for `password|secret|private_key|api_key\s*=` — only test fixtures (`"fake-key"`, `"secret-key-123"`, placeholder strings), no real credentials; no `eval()`/`exec()`/`os.system()`/`subprocess`; `innerHTML` is used only to clear content (`= ''`), never assigned from generated/AI text — all entry text goes through `textContent`/`createElement`; `default_db_path()`/`default_html_path()` resolve inside the build folder via `Path(__file__).resolve().parent.parent`; no code reads from paths outside the build folder.

[Step 8] FutureFeatures.md: 7 concrete enhancements. Manual.md: full command reference and usage guide.

[Step 9] Resynced `builds/index.md` from PR #47 (`claude/cool-sagan-x6jc2c`, the most recently opened branch) before appending tonight's row, since `main` is at 2026-06-18.

Build complete. Success criteria reviewed. All tests passing.
