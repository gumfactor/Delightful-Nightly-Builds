# Build Log — Psychological Study Vignette Generator (Vignette Lab)

> **Date:** 2026-06-15
> **Session start:** 08:05 UTC
> This is a live log. Claude appends entries throughout the build session.

---

## Log

### [08:05 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, builds/index.md, STANDARDS.md in full
- Today is Monday (day-of-week 1) → complexity target: Focused Utility
- Day of year 166 → category index (166-1) % 9 = 3 → Category D: Creative/Generative
- Step 0: checked builds/2026-06-10-investment-portfolio-snapshot/BUILD_LOG.md —
  final entry reads "Build complete. Success criteria reviewed. All tests passing (103/103)."
  → build is done, no resumption needed
- Lottery: no Category D ideas in builds/ideas.md → filtered pool empty → fresh ideas path
- Environment check: no ANTHROPIC_API_KEY, no GITHUB_TOKEN; anthropic package not installed;
  requests and Python stdlib available; pip accessible for pytest
- Generated 3 fresh ideas: Vignette Lab (winner), Exam Question Generator, Research
  Hypothesis Combinatorics Tool, Grant Aims Drafter
- Non-winners appended to builds/ideas.md (IDs 9, 10, 11)
- Build folder created: builds/2026-06-15-vignette-lab/

### [08:12 UTC] PRD Written

- Goal: combinatorial vignette generator for psychological research stimuli and teaching
- Scope: 3 themes (stress, empathy, moral), participant + researcher output files,
  seeded reproducibility, de-duplication within batches
- Stack: Python 3 stdlib, pytest only
- Notable design: element banks in banks.py, assembly in generator.py, markdown in formatter.py

### [08:20 UTC] Build Phase — Source Files

- Wrote src/banks.py: CHARACTERS (10 entries), STRESS/EMPATHY/MORAL theme dicts each with
  6 settings, 8 events, 4 checks, 4 prompts, and researcher note
- Wrote src/generator.py: `_fill()` template substitution, `_to_be()` subject-verb agreement,
  `_build_narrative()`, `list_themes()`, `generate_vignettes()` with seeded RNG and
  character-pool cycling
- Wrote src/formatter.py: `format_participant()`, `format_researcher()`, `format_stdout()`
- Wrote main.py: argparse CLI with `list` and `generate` subcommands, `--output` file mode,
  `--seed`, `--researcher` flags
- Fixes applied during build:
  - "They is" → "They are" (added `_to_be()` helper for pronoun-correct verb agreement)
  - Added `{pronoun_sub}` subject prefix to all empathy/moral events (events had missing subjects)
  - Rewrote `MORAL_SETTINGS` from event-context descriptions to neutral locations to prevent
    incompatible setting+event combinations

### [08:35 UTC] Tests Written and Run

- Wrote tests/test_generator.py: 15 tests covering list_themes, generate_vignettes (count, fields,
  indexing, error handling, reproducibility, pool cycling, character names in checks)
- Wrote tests/test_formatter.py: 14 tests covering participant format (no checks), researcher format
  (checks + note), format_stdout delegation, empty-list fallback
- Tests: 29 passed, 0 failed (first run after all fixes)

### [08:40 UTC] Success Criteria Verified

1. `python3 main.py generate --theme stress --count 5` exits 0, prints 5 vignettes — ✓
2. `python3 main.py generate --theme empathy --count 3 --output /tmp/test_study` writes
   `test_study_participant.md` and `test_study_researcher.md` with correct content — ✓
3. `python3 main.py list` prints all 3 themes with element counts — ✓
4. `--seed 42` produces identical output on two consecutive calls — ✓ (verified in tests)
5. All 29 tests pass, 0 failures — ✓

Security scan: no eval(), exec(), os.system(), subprocess, innerHTML, hardcoded credentials.
All output files confined to `builds/2026-06-15-vignette-lab/` and user-specified paths.

### [08:45 UTC] Documentation Complete

- FutureFeatures.md: 9 concrete suggestions (5 quick wins, 2 medium, 2 ambitious)
- Manual.md: quick start, theme table, command reference, output file descriptions,
  Qualtrics usage guidance, test run instructions

Build complete. Success criteria reviewed. All tests passing.
