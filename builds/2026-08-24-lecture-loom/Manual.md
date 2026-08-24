# Manual — Lecture Loom

> **Version:** 1.0 (built 2026-08-24)
> **Complexity:** Ambitious Project

---

## What This Is

A Python CLI that takes a folder of raw, inconsistently-formatted lecture notes and produces a consistent slide outline and student handout for each one — while deterministically flagging lectures likely to run over their time slot, lectures missing learning objectives, and sections that are unusually dense relative to the rest of the lecture. The timing/objective/structure checks are computed directly from the notes' own word counts and headings, not guessed by AI — an optional Claude Haiku layer only polishes bullet phrasing and drafts discussion questions on top of that.

---

## Quick Start

1. Point it at one lecture file or a folder of them (`.md` or `.txt`).
2. Run `python3 src/main.py check <path>` for a quick terminal-only sanity pass (no files written).
3. Run `python3 src/main.py format <path> --output <output-dir>` to write `<name>.outline.md` and `<name>.handout.md` for every lecture.
4. Run `python3 src/main.py render <path> --output <output-dir>` to build a batch dashboard, then open `<output-dir>/dashboard.html` in a browser.

No install step and no third-party dependencies — `requirements.txt` is intentionally empty.

---

## How to Use It

### `check` — terminal-only sanity pass

```bash
python3 src/main.py check my-lectures/ --target-minutes 75
```

Prints, per lecture: estimated vs. target minutes and budget status, the longest section (if over budget), objective count and flag, any dense sections, and a heading-skip warning if one exists. Writes nothing to disk.

### `format` — write outline + handout files

```bash
python3 src/main.py format my-lectures/ --output loom-output/
```

For each input file, writes:
- `<name>.outline.md` — title, objectives, a timing summary, and one heading per section annotated with its estimated minutes (for building your own slides from).
- `<name>.handout.md` — title, objectives, and section content with no timing annotations (student-facing).

### `render` — batch HTML dashboard

```bash
python3 src/main.py render my-lectures/ --output loom-output/
```

Builds `loom-output/dashboard.html` — a self-contained, mobile-readable, dark-mode page summarizing every lecture in the batch: a status badge (on target / over budget / under budget), estimated vs. target minutes, section/objective counts, and any flags. Click a row to expand its full objective list and per-section breakdown. Use the search box to filter by title. Open the file directly in any browser — no server needed.

### Optional AI polish

Add `--ai-polish` to any command with `ANTHROPIC_API_KEY` set in your environment:

```bash
ANTHROPIC_API_KEY=sk-... python3 src/main.py format my-lectures/ --ai-polish
```

This sends only the already-extracted structure (title, section headings, bullet text — never full file content beyond that, never personal data) to Claude Haiku, which rewrites bullets into cleaner presenter phrasing and drafts 2–3 discussion questions per lecture. Without a key, a deterministic whitespace/capitalization cleanup runs instead and zero network calls are made — every command is fully useful with no API key at all.

### Claude Code Skill

Copy `skill/SKILL.md` into your project's `.claude/skills/lecture-loom/SKILL.md` to invoke this tool by name inside a Claude Code session (e.g. "format my lecture notes for next week").

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--target-minutes` | `50` | The class period length in minutes. The budget check uses a ±10% tolerance band around this. |
| `--wpm` | `130` | Assumed instructional speaking pace in words/minute — a documented assumption, not a measurement of your actual delivery. Raise it if you talk fast, lower it if you pause a lot. |
| `--ai-polish` | off | Enables the optional Claude Haiku polish layer (requires `ANTHROPIC_API_KEY`). |
| `--output` | `loom-output` | Output directory for `format`/`render`. |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `error: no .md or .txt files found in <path>` | The folder you pointed at has no `.md`/`.txt` files | Double-check the path, or convert your notes to Markdown/plain text first |
| `error: No such file or directory` | Typo in the path, or a relative path run from the wrong directory | Use an absolute path or double-check your current directory |
| Every lecture flagged `missing` objectives even though you wrote some | Your objectives use different phrasing than "Objectives"/"Learning Objectives" heading or "By the end of this lecture, students will..." | Rename the heading, or phrase one sentence using that pattern — see Known Limitations in `FutureFeatures.md` |
| `--ai-polish` silently does nothing different | `ANTHROPIC_API_KEY` isn't set in your environment | Export the key before running, or check for typos in the variable name |

---

## Known Limitations

- The words-per-minute constant is a documented assumption, not measured from your actual speaking pace.
- Objective extraction only recognizes English-language heading and sentence patterns described above.
- No direct `.pptx`/`.key` export — output is Markdown, meant to be pasted into whatever slide tool you already use.
- Section-density and objective-sparsity thresholds are fixed constants (not yet user-configurable).
