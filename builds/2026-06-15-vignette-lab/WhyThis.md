# WhyThis.md — Psychological Study Vignette Generator

## Build Selection Method
Fresh ideas (lottery skipped — no Category D ideas in the backlog).

## Lottery Roll
No roll performed. The filtered pool for Category D / Focused complexity was empty,
so the lottery was bypassed per Step 2d.

## Category and Complexity
- **Category:** D — Creative / Generative (day-of-year 166; index (166-1) % 9 = 3)
- **Complexity target:** Focused Utility (Monday, day-of-week 1)

## Recent Topic Diversification
The last 7 builds were heavily concentrated on:
- Investment / portfolio / thesis tracking (Jun 09, 10, 12, 14)
- Git workflow tooling (Jun 07)
- AI session context (Jun 06)
- Data profiling (Jun 08)

This build moves entirely outside those domains — into academic research tool-building —
using the user's neuroscience lab and teaching work as the domain.

## The Idea

### What problem does it solve?
Creating psychological scenario vignettes (short narrative descriptions used as stimuli in
behavioral studies or as classroom prompts) is surprisingly time-intensive. A researcher
writing a stress study needs 10–30 unique scenarios that each involve a different character,
setting, and event while remaining internally consistent and manipulation-appropriate. Writing
these manually takes 1–3 hours; reviewing and editing them takes more. The problem is not
creativity — it is throughput and variety.

### Why better than manual?
Template documents in Word or Notion accumulate and grow stale. Generating from a bank of
validated elements produces combinatorial variety (hundreds of unique scenarios per theme
from modest banks) while guaranteeing structural consistency. The researcher file format
includes manipulation check questions and design notes automatically — output that would
otherwise require a separate step.

### Why not just use Claude.ai?
The user can prompt Claude directly, but doing so every time requires reformatting output,
adding manipulation checks by hand, ensuring no character repetition, and saving to files.
This tool wraps those steps into a single command with consistent structure and file
output ready for paste-into-Qualtrics or slide decks.

### Preference prior alignment
The pattern that earns high ratings from this user is: *automation that removes a
recurring manual step, producing directly usable output connected to their real work*.
This build targets a recurring task (experiment and course material prep), produces
immediately usable files, and has no manual-entry bottleneck — the banks do the work.

## Alternatives Considered

### Alternative 1: Academic Exam Question Generator (with Anthropic API)
- Stronger AI-generation quality, but ANTHROPIC_API_KEY is not set in this environment
- Deferred — could be revisited when API key is configured as a repo secret
- Would be Category D / Focused Utility — added to ideas.md backlog

### Alternative 2: Research Hypothesis Combinatorics Tool
- Takes two neuroscience constructs and generates testable hypotheses
- More abstract; output requires more interpretation before use
- Less immediately usable than ready-to-run vignettes
- Added to ideas.md backlog

### Alternative 3: Grant Specific Aims Drafter (with Anthropic API)
- High potential value for a recurring, high-effort task
- Blocked by same API key constraint
- Added to ideas.md backlog

## Non-Winning Ideas Appended to builds/ideas.md
IDs 9, 10, and 11 (exam question generator, hypothesis generator, grant aims drafter)
will be appended to the backlog for future lottery consideration.
