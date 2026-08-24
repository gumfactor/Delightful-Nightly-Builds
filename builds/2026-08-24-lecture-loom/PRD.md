# PRD — Lecture Loom

> **Build date:** 2026-08-24
> **Category:** B — Productivity Utility
> **Complexity:** Ambitious Project
> **Day of week:** Monday

---

## Goal

Batch-convert a folder of raw, inconsistently-formatted lecture notes into a consistent slide outline and student handout per lecture, while deterministically flagging timing-budget overruns, missing learning objectives, and structurally unbalanced sections before the lecture is ever delivered.

## User Story

As a professor who writes lecture notes in whatever ad hoc format is fastest at the time, I want to batch-run a folder of raw notes through one tool, so that every lecture comes out in a consistent outline + handout format and I get an honest, computed warning if a lecture is likely to run over its time slot or is missing objectives — without re-formatting each file by hand or having to trust an AI's prose alone.

## Scope

### In Scope
- Deterministic Markdown structural parser: title (H1 or filename), learning objectives (explicit "Objectives"/"Learning Objectives" heading block, or "By the end of this lecture/class, students will..." sentence patterns), H2 sections each with their bullet/paragraph content, heading-level-skip detection (H1 → H3 with no H2).
- Deterministic timing engine: word count per section ÷ configurable words-per-minute (default 130 wpm, a documented instructional-pace assumption) → estimated minutes per section and total; compared against a configurable `--target-minutes` with a ±10% tolerance band → `on_target` / `over_budget` / `under_budget` classification, plus the single worst-overrun section named.
- Deterministic section-density outlier detection: sections whose bullet count is more than 2x the lecture's own mean bullet count are flagged as "dense — consider splitting."
- Deterministic objective-completeness check: zero extracted objectives → flagged; objective count wildly mismatched against section count (e.g., 1 objective for 8 sections) → flagged as a soft warning, not blocking.
- Per-lecture output files: `<name>.outline.md` (title, objectives, one heading per section with bulleted talking points and its estimated minutes) and `<name>.handout.md` (fuller student-facing version: title, objectives, section prose/bullets, no timing annotations).
- Batch-wide self-contained dark-mode HTML dashboard (`render` command) summarizing every processed lecture: timing-budget status badge, objective/section/bullet counts, flags, and links to view each lecture's extracted structure — built from an escaped JSON payload via `createElement`/`textContent`, never `innerHTML`.
- Optional Claude Haiku polish (`--ai-polish`, requires `ANTHROPIC_API_KEY`): rewrites each section's bullets into cleaner, parallel-structured presenter phrasing and drafts 2–3 discussion questions per lecture. Sends only the already-extracted structure (title, section headings, bullet text) — never raw file content beyond that, never personal data. Unconditional deterministic fallback (basic whitespace/capitalization cleanup, no discussion questions) makes zero network calls when no key is set.
- CLI commands: `format <path>` (single file or folder, writes outline+handout files next to a `--output` dir), `render <path>` (single file or folder, builds the HTML dashboard), `check <path>` (prints the flags/timing table to the terminal only, no files written — useful for a quick sanity pass).
- Companion Claude Code Skill (`skill/SKILL.md`) so the tool can be invoked as `/lecture-loom <folder>` inside a coding session, per CLAUDE.md's guidance that on-demand productivity tools are usually a better fit as a Skill than a bare script.

### Out of Scope
- Cross-lecture concept-overlap or objective-gap detection across an entire course (already covered by the existing Curriculum Atlas build, 2026-08-16).
- Actual slide file generation (.pptx/.key) — output is Markdown outline/handout files, which the professor pastes into whatever slide tool they use.
- Speech/audio timing calibration to the professor's own actual speaking rate — the wpm constant is a documented, configurable default, not a measured value.
- Multi-language support — English-language heuristics only.

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None
- **Dependencies:** stdlib only (`argparse`, `json`, `re`, `pathlib`, `dataclasses`, `urllib.request` for the optional Anthropic call). `requirements.txt` is intentionally empty.
- **Runtime requirement:** `python3 src/main.py <command> <path> [options]` — no install step, no server.

## Data Structure

No database — the tool is a pure batch transform over files already on disk, matching the "Productivity Utility" shape (no state to persist between runs beyond the output files themselves).

**Input:** one `.md`/`.txt` file, or a folder of them, each containing free-form lecture notes with arbitrary Markdown-style headings and bullets.

**Internal representation** (`Lecture` dataclass, built by the parser):
```
Lecture:
  path: str
  title: str
  objectives: list[str]
  sections: list[Section]
  heading_skip_warning: bool

Section:
  heading: str
  level: int            # 2 for H2, etc.
  bullets: list[str]
  word_count: int
  estimated_minutes: float

LectureReport (computed from a Lecture + config):
  total_minutes: float
  target_minutes: float
  budget_status: "on_target" | "over_budget" | "under_budget"
  worst_section: str | None
  dense_sections: list[str]
  objective_flag: "ok" | "missing" | "sparse"
```

**Output:** `<name>.outline.md`, `<name>.handout.md` per input file (written to `--output`, default `./loom-output/`), and an optional `dashboard.html` for a batch `render` run. No data is written back into the input folder.

## Folder Structure

```
builds/2026-08-24-lecture-loom/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── skill/
│   └── SKILL.md
├── fixtures/
│   ├── well_formed_lecture.md
│   ├── no_objectives_lecture.md
│   ├── overlong_lecture.md
│   └── heading_skip_lecture.md
├── tests/
│   ├── test_parser.py
│   ├── test_timing.py
│   ├── test_flags.py
│   ├── test_ai_polish.py
│   ├── test_render.py
│   └── test_cli.py
└── src/
    ├── main.py
    ├── parser.py
    ├── timing.py
    ├── ai_polish.py
    ├── formatter.py
    └── render.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - Markdown parsing: title extraction (H1 present / absent → filename fallback), section splitting on H2, bullet extraction, heading-level-skip detection (H1 → H3).
  - Objective extraction: explicit "Objectives" heading block, "By the end of this lecture..." sentence pattern, no-objectives case.
  - Timing math: word-count → minutes at a given wpm, total-minutes summation, on/over/under-budget classification at and around the ±10% boundary (exact edge cases).
  - Section-density outlier detection: a section with >2x the mean bullet count is flagged; a uniform lecture flags nothing.
  - Objective-completeness flags: missing vs. sparse vs. ok.
  - Outline/handout file generation: correct structure, correct file count for a batch folder.
  - HTML dashboard rendering and escaping: a `</script><script>alert(1)</script>` payload in a lecture title/bullet must render as inert text, never execute.
  - AI polish deterministic fallback: with no `ANTHROPIC_API_KEY`, `urlopen` is never called (call-count assertion), and the fallback text differs from raw input only by whitespace/capitalization cleanup.
  - AI polish with a mocked Anthropic response: exactly one request made, response correctly merged into the output, and a malformed/error response falls back to the deterministic path without crashing.
  - CLI error handling: missing input path, empty folder, invalid `--target-minutes` (non-positive), invalid `--wpm`.

## Success Criteria

1. All tests pass (zero failures).
2. Given a folder of lecture notes with a deliberately-inserted timing overrun, `check` correctly reports `over_budget` with the specific over-length section named, matching a hand-computed reference value.
3. Given a lecture with no objectives, the tool flags `missing` — verified against a fixture.
4. `render` produces a working, mobile-readable HTML dashboard for a multi-file batch, verified live in headless Chromium with zero console errors and an injected XSS payload confirmed inert.
5. With no `ANTHROPIC_API_KEY` set, every command completes successfully and makes zero network calls (verified via a mocked `urlopen` call-count assertion), so the tool is fully useful without any credential.

---

## Scope Changes

None — full scope as specified above was completed as planned.
