# Manual — AgentLint

> **Version:** 1.0 (built 2026-07-16)
> **Complexity:** Ambitious Project

---

## What This Is

AgentLint audits an AI agent instruction file — a `CLAUDE.md`, `AGENTS.md`, or similar markdown document that a coding agent reads and follows — for problems that are easy to introduce and easy to miss: file references and internal links that no longer resolve, required sections that got deleted during an edit, "Always X" / "Never Y" rules that quietly contradict each other, and (with an Anthropic API key) factual or numeric claims in the instructions that have drifted out of sync with the real project data they describe. It exists because this exact repo's own `CLAUDE.md` was found, during tonight's build session, to contain a stale claim ("every build has scored 4/10 or below") that a quick look at `builds/index.md` disproves.

---

## Quick Start

1. `cd builds/2026-07-16-agentlint`
2. `python3 -m src.main audit path/to/CLAUDE.md` — runs all deterministic checks against the file, printing a text report to the terminal.
3. Add `--require-sections "Goal,Scope,Testing Strategy"` to also check that specific section headings exist.
4. Add `--ground-truth path/to/some-data-file.md` and set `ANTHROPIC_API_KEY` in your environment to also run the AI semantic review, including cross-checking claims against that data file.
5. Add `--format html --out report.html` and open `report.html` in a browser for a readable dashboard instead of terminal text.

---

## How to Use It

### Basic audit

```bash
python3 -m src.main audit CLAUDE.md
```

Runs the four deterministic checks (broken file references, broken internal anchors, missing required sections, possible modal contradictions) plus the AI review (skipped automatically with an `info` finding if `ANTHROPIC_API_KEY` isn't set). Prints a text report and exits `1` if any error-severity finding was found, `0` otherwise.

### Checking required sections

```bash
python3 -m src.main audit CLAUDE.md --require-sections "Goal,Scope,Success Criteria"
```

Comma-separated heading text (case-insensitive, matched against the exact heading text with no leading `#`). Useful for enforcing a template contract, like this repo's own `templates/PRD.md`.

### AI semantic review + ground-truth drift check

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 -m src.main audit CLAUDE.md --ground-truth builds/index.md
```

Sends the instructions (and the ground-truth file, if given) to Claude with a prompt asking it to flag contradictions, ambiguous instructions, and — specifically — claims in the instructions that the ground-truth file's actual content contradicts. This is the check that would have caught tonight's stale calibration-note bug. Costs one Claude API call per run; use `--skip-ai` to disable it even when a key is set.

### Output formats

```bash
python3 -m src.main audit CLAUDE.md --format json
python3 -m src.main audit CLAUDE.md --format html --out report.html
```

`text` (default) and `json` print to stdout unless `--out <path>` is given; `html` always needs `--out` to be useful (or redirect stdout yourself).

### CI / pre-commit gating

```bash
python3 -m src.main audit CLAUDE.md --fail-on error   # default: exit 1 only on errors
python3 -m src.main audit CLAUDE.md --fail-on warning  # exit 1 on warnings too
python3 -m src.main audit CLAUDE.md --fail-on none     # always exit 0, report only
```

### Using it as a Claude Code Skill

`skill/SKILL.md` documents how to wire this up as a `/agentlint` skill inside any Claude Code project: copy the `skill/` folder to `.claude/skills/agentlint/` and the `src/` folder alongside it in that project, then invoke `/agentlint <path>`. It is **not** installed into this repo's own live skill set — this build only ever writes inside `builds/2026-07-16-agentlint/`, per the nightly-build rules.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--root` | the target file's own directory | Directory that referenced paths resolve against |
| `--require-sections` | (none) | Comma-separated heading text that must be present |
| `--ground-truth` | (none) | A second file the AI review cross-checks claims against |
| `--format` | `text` | `text`, `json`, or `html` |
| `--out` | stdout | File path to write the report to |
| `--fail-on` | `error` | Minimum severity (`error`, `warning`, or `none`) that causes a non-zero exit code |
| `--skip-ai` | off | Skip the AI semantic review even if `ANTHROPIC_API_KEY` is set |
| `ANTHROPIC_API_KEY` (env var) | unset | Enables the AI semantic review when set; the tool works fully without it, just without that one check |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Lots of `broken_file_reference` findings on filenames that are clearly fine | The document mentions bare filenames generically (e.g. as part of a template describing what future files should be named) rather than as literal paths meant to resolve right now | This is a known trade-off of the inclusive path-detection heuristic — see `FutureFeatures.md`. For now, review the flagged list and mentally filter out generic template mentions; a future `--ignore` flag will let you suppress known patterns |
| AI review always shows "skipped — no ANTHROPIC_API_KEY set" | The environment variable isn't set in your shell | `export ANTHROPIC_API_KEY=sk-ant-...` before running, or pass it inline: `ANTHROPIC_API_KEY=sk-ant-... python3 -m src.main audit ...` |
| `ModuleNotFoundError` when running `python3 src/main.py audit ...` directly | Running from the wrong directory | Run from inside `builds/2026-07-16-agentlint/` (both `python3 src/main.py audit ...` and `python3 -m src.main audit ...` work from there) |
| Exit code is always `0` even with obvious problems | `--fail-on none` was passed, or all findings are `warning`/`info` under the default `error` threshold | Use `--fail-on warning` to also fail on warnings, or check the printed report — it always shows every finding regardless of the exit code |

---

## Known Limitations

- The path-existence check can produce false positives on documents that mention filenames generically rather than as literal paths (see Troubleshooting above and `FutureFeatures.md`).
- The modal-contradiction check is a keyword-overlap heuristic — every finding it produces is explicitly labeled as needing manual review, not a definitive contradiction.
- One target file and one ground-truth file per run; no multi-file or cross-repo mode yet.
- No run history — each invocation is stateless, so there's no built-in way to track whether a previously flagged issue has been fixed.
- The AI review depends on the target document (and ground-truth file, if given) fitting comfortably in a single Claude request; very large documents aren't chunked in this version.
