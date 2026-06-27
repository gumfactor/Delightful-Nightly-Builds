# BUILD_LOG — Neurofact

## [Orient] Step 0–1

- Most recent build folder: `2026-06-18-regex-dojo` — BUILD_LOG ends with "Build complete." ✓
- builds/index.md resynced from PR #21 branch (claude/cool-sagan-d57lw0, 2026-06-26)
- ANTHROPIC_API_KEY is not set in this build environment — game ships with 30 seed questions; generator.py calls API when key is available at runtime

## [Decide] Step 2

- Day of year: 178 → category index 6 → **G — Game / Puzzle**
- Lottery roll: 76 > 25% threshold → fresh ideas
- Selected: **Neurofact** — 30 questions (15 real findings / 15 plausible fakes)
- Non-winners: Coping Style Compass, Canada List Brand Challenge → appended to ideas.md

## [Build] Step 5 — Implementation

### Game content design
- 30 questions across 8 neuroscience topic categories
- Real findings drawn from established research (cognitive neuroscience, affective neuroscience, stress, psychopathy, memory, sleep, hormones, neuroanatomy)
- Fake findings crafted to match the register and specificity of real findings — plausible but factually incorrect
- Each question has difficulty label (Foundational / Advanced / Expert) and topic category
- Full explanations clarify why real findings are real and what's wrong with fakes

### Architecture decisions
- Self-contained `index.html` — all CSS, JS, and game data embedded; runs from `file://` with zero dependencies
- Questions shuffled per session using Fisher-Yates for replayability
- `src/generator.py` ships as regeneration tool — fetches arXiv abstracts + calls Anthropic API to produce fresh `game_data.json` when key is available
- Playwright tests use `file://` URL against `index.html` directly

## [Tests] Step 6

Fixed 1 bug found during testing: QUESTIONS_SEED in generator.py initially had 20 real and 10 fake (the last 5 "real" items from index.html were extra real items that hadn't been balanced). Updated both index.html and QUESTIONS_SEED to 15 real + 15 fake = 30 total.

Tests: **72 passed, 0 failed**
- `python3 -m pytest tests/test_generator.py -v` → **36 passed**
- `npx playwright test` → **36 passed** (27.1s)

## [Verify] Step 7 — Success criteria check

1. ✓ **Playable** — `index.html` loads from `file://`, shows all 30 questions, reaches end screen — verified by Playwright tests 29–36
2. ✓ **Functional feedback** — answering reveals verdict, explanation, and highlights correct button before Next is enabled — verified by Playwright tests 20–24
3. ✓ **Score integrity** — score increments correctly, final score = correct/30, grade maps to accuracy — verified by pytest (grade tests) and Playwright end-screen tests
4. ✓ **Content quality** — 30 questions across 13 topic categories (Memory, Stress, Social Neuroscience, Psychopathy, Emotion Regulation, Reward, Cognitive Neuroscience, Neuroanatomy, Developmental Neuroscience, Hormones, Autonomic Neuroscience, Interoception, Moral Cognition) — verified by test_seed_data_spans_multiple_categories
5. ✓ **All tests pass** — 36 Playwright + 36 pytest = 72 total, 0 failures

Security checklist:
- No .env files
- No hardcoded credentials (ANTHROPIC_API_KEY read from os.environ)
- No eval() on user-controlled input
- No innerHTML from user-controlled data (question text set via .textContent)
- No os.system() or subprocess calls
- No file path traversal
- All code within build folder

## [Docs] Step 8 — Documentation complete

- FutureFeatures.md: 7 concrete enhancements
- Manual.md: play instructions, scoring table, question categories, test commands, generator usage

Build complete. Success criteria reviewed. All tests passing.
