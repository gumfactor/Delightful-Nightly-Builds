---
name: agentlint
description: Audit an AI agent instruction file (CLAUDE.md, AGENTS.md, or similar) for broken file references, missing required sections, possible self-contradictions, and — with ANTHROPIC_API_KEY set — AI-reviewed semantic drift against a ground-truth data file. Use when the user asks to check, lint, audit, or validate a CLAUDE.md/AGENTS.md file, or asks whether their agent instructions are stale or self-contradicting.
---

# AgentLint

This skill wraps the AgentLint CLI shipped in this same nightly build
(`builds/2026-07-16-agentlint/src/main.py`). It is **not** installed into
this repo's live skill set — copy this folder to `.claude/skills/agentlint/`
in whichever project you want to run it against, alongside the `src/`
directory from the same build, then invoke it as `/agentlint <path>`.

## What to do when this skill is invoked

1. Determine the target file. If the user names a file, use it. Otherwise
   default to `CLAUDE.md` in the current project root if one exists, or
   ask which file to audit.
2. Determine whether a ground-truth file makes sense for this run — e.g.
   if the target instructions make claims about data tracked elsewhere in
   the repo (a catalog, a changelog, a stats file), pass it via
   `--ground-truth <path>`.
3. Run:
   ```bash
   python3 -m src.main audit <target-file> \
     --ground-truth <optional-ground-truth-file> \
     --format text \
     --fail-on error
   ```
   (Run from the directory containing the `src/` package copied alongside
   this skill.)
4. If `ANTHROPIC_API_KEY` is set in the environment, the AI semantic
   review runs automatically as part of the same command — no separate
   step needed. If it is not set, deterministic checks still run and the
   report will note that the AI review was skipped.
5. Summarize the findings for the user: lead with error-severity findings
   (broken references, missing sections), then warnings (possible
   contradictions, AI-flagged issues). Offer to open the HTML report
   (`--format html --out report.html`) if there are more than a handful
   of findings.
6. Do not automatically edit the audited file — this tool is report-only
   by design. Propose specific fixes and let the user decide.

## Example invocations

- "Check CLAUDE.md for problems" → `python3 -m src.main audit CLAUDE.md`
- "Does CLAUDE.md still match builds/index.md?" →
  `python3 -m src.main audit CLAUDE.md --ground-truth builds/index.md`
- "Give me an HTML report" →
  `python3 -m src.main audit CLAUDE.md --format html --out agentlint-report.html`
