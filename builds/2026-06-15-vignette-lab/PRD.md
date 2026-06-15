# PRD — Psychological Study Vignette Generator (Vignette Lab)

## Goal
A Python CLI that combinatorially generates realistic, themed scenario vignettes for
psychological research stimuli and classroom exercises, outputting print-ready markdown
files with participant-facing text, manipulation check questions, and researcher notes.

## User Story
As a psychology professor and neuroscience lab director, I periodically need sets of
scenario descriptions (vignettes) to use as: (a) stimuli in behavioral studies, (b)
classroom discussion prompts, and (c) case studies for course assignments. Creating
varied, internally consistent vignettes manually is time-consuming and the result is
often a small, repetitive set. This tool maintains validated thematic scenario banks
and generates unique combinations on demand, producing files I can paste directly
into surveys, slide decks, or study materials.

## Scope

### In Scope
- Three themed vignette types: `stress`, `empathy`, and `moral`
- Combinatorial generation from element banks (characters × settings × events)
  yields hundreds of unique scenarios per theme
- Two output files per run: clean participant version + annotated researcher version
- Markdown output, formatted for direct use in course materials or Qualtrics
- Seeded randomization for reproducibility (optional `--seed` flag)
- `list` subcommand: display themes and element counts
- `generate` subcommand: produce N vignettes to stdout or file(s)
- De-duplication guard: within a batch, same character is not reused before exhausting
  the character pool
- All content is written into the build folder; no external dependencies beyond
  Python stdlib and pytest

### Out of Scope
- Web interface or GUI
- Custom theme authoring via CLI (themes are defined in source code)
- Integration with Qualtrics or survey platforms
- AI-generated vignette elements (no Anthropic API available)
- Audio or image output

## Tech Stack
- Python 3.10+ (stdlib only; no third-party runtime dependencies)
- pytest for testing
- `requirements.txt`: `pytest` only

## Data Structure
All scenario banks live in `src/banks.py` as module-level constants:
```
CHARACTERS: list[dict]     - name, age, role, pronouns
STRESS_ELEMENTS: dict      - settings, events, checks, prompts
EMPATHY_ELEMENTS: dict     - settings, events, checks, prompts
MORAL_ELEMENTS: dict       - settings, events, checks, prompts
```

Each generated vignette is represented by a `Vignette` dataclass:
```
theme: str
character: dict
setting: str
event: str
narrative: str          # assembled from character + setting + event
checks: list[str]       # 2 manipulation check questions
prompt: str             # participant response prompt
researcher_note: str    # what the scenario is designed to measure
```

Output files:
- `{output_prefix}_participant.md` — clean vignettes numbered, no notes
- `{output_prefix}_researcher.md` — same + manipulation checks + notes

## Folder Structure
```
builds/2026-06-15-vignette-lab/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── main.py                        ← CLI entry point
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── banks.py                   ← Scenario element banks
│   ├── generator.py               ← Vignette assembly logic
│   └── formatter.py               ← Markdown output formatting
└── tests/
    ├── test_generator.py          ← Generator logic tests
    └── test_formatter.py          ← Formatter output tests
```

## Testing Strategy
- Framework: pytest
- Run command: `python -m pytest tests/ -v`
- Location: `tests/test_generator.py`, `tests/test_formatter.py`

Tests cover:
- `generate_vignettes()`: correct count returned, all required fields present
- Character de-duplication across a batch
- Seeded reproducibility (same seed → same output)
- Handling count > character pool size (wraps without crash)
- Markdown participant formatter: numbered sections, no researcher notes present
- Markdown researcher formatter: includes checks and notes
- `list_themes()`: returns non-empty dict of theme info
- Edge cases: count=0, count=1, missing optional args

## Success Criteria
1. `python3 main.py generate --theme stress --count 5` exits 0 and prints 5 vignettes
2. `python3 main.py generate --theme empathy --count 3 --output study` writes
   `study_participant.md` and `study_researcher.md` with correct content
3. `python3 main.py list` prints theme names and element counts
4. Same seed produces identical output on two calls: `--seed 42` is reproducible
5. All tests pass (≥ 8 tests, 0 failures)
