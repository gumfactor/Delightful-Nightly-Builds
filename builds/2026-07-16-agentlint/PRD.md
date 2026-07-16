# PRD — AgentLint

> **Build date:** 2026-07-16
> **Category:** H — Developer Tool
> **Complexity:** Ambitious Project
> **Day of week:** Thursday

---

## Goal

A CLI (and companion Claude Code Skill) that audits AI agent instruction files (CLAUDE.md, AGENTS.md, and similar) for broken file references, missing required sections, self-contradicting rules, and — via optional Claude API review — semantic drift between claims made in the instructions and the actual project data those claims describe.

## User Story

As a solo founder/researcher who maintains agent instruction files across many simultaneous projects (this nightly-build repo, The Canada List, Kwyeter, lab tooling), I want to run one command against any CLAUDE.md/AGENTS.md file and get a concrete list of what's broken, stale, or contradictory in it, so that I catch instruction drift before an agent silently follows outdated or self-contradicting rules.

This build's own repo supplied a live example while researching tonight: `CLAUDE.md`'s calibration note claims "Every rated build to date has scored 4/10 or below," but `builds/index.md` now shows a 9/10 (Qualtrics Survey Data Inspector) and several other builds above 4. That drift is exactly the failure mode this tool is built to catch — a deterministic check can't catch it (it requires reading both documents and reasoning about the claim), but an AI-assisted review pointed at both files can.

## Scope

### In Scope
- Markdown parser: extracts headings (with GitHub-style slugs), inline-code file-path candidates, and markdown links (internal anchors vs. relative file links vs. external URLs)
- Deterministic check: broken file/path references (backtick or link paths that don't resolve relative to a root directory)
- Deterministic check: broken internal anchor links (`[text](#heading)` where no heading slugifies to that anchor)
- Deterministic check: missing required sections (user supplies a comma-separated list or JSON list of required `##`/`###` headings)
- Heuristic check: possible modal contradictions — pairs of "Always X" / "Never Y" style statements with high keyword overlap, flagged for manual review (explicitly labeled as a heuristic, not a definitive contradiction)
- Optional AI semantic review (requires `ANTHROPIC_API_KEY` at runtime, via direct `urllib` call to the Claude Messages API, structured JSON output): flags ambiguous instructions, internal contradictions, and — when a `--ground-truth` file is supplied — claims in the instructions that are contradicted by data in that file. Deterministic template/no-op fallback when no key is set.
- Report rendering: colored terminal text, JSON, and a self-contained dark-mode HTML report (all user-controlled text HTML-escaped)
- CLI flags: `--root`, `--require-sections`, `--ground-truth`, `--format {text,json,html}`, `--out`, `--fail-on {error,warning}` (non-zero exit code for CI/manual gating)
- A Claude Code Skill definition (`skill/SKILL.md`) wrapping the CLI so it can be invoked as `/agentlint <path>` inside a Claude Code session, with install instructions in Manual.md
- Test fixtures modeling the real CLAUDE.md-vs-index.md drift scenario found tonight, to prove the AI-review path works against a realistic case (with the Anthropic call mocked in tests)

### Out of Scope
- Automatic fixing/rewriting of the instruction file (report-only; the user decides what to change)
- A general-purpose Markdown linter (spelling, prose style, link-rot for external URLs) — scope is agent-instruction-specific structural and semantic integrity
- Multi-file cross-referencing across an entire repo of docs (single target file + optional single ground-truth file per run)
- Installing the Skill into this repo's live `.claude/skills/` — it ships as a documented, copyable deliverable inside the build folder only, per the "never modify files outside the build folder" rule

## Tech Stack

- **Language:** Python 3
- **Framework:** None
- **Dependencies:** stdlib only (`urllib.request` for the optional Anthropic API call — no `anthropic` SDK dependency, matching this repo's established pattern for optional-AI builds)
- **Runtime requirement:** `python3 src/main.py audit <path-to-instructions.md> [options]`

## Data Structure

Input: a single Markdown file (the instructions being audited) plus an optional second Markdown/text file (`--ground-truth`) whose content the AI review cross-checks factual claims against.

Internal representation — a `Finding`:
```python
{
  "check": str,       # e.g. "broken_file_reference", "ai_contradiction"
  "severity": str,    # "error" | "warning" | "info"
  "message": str,     # human-readable description
  "excerpt": str,      # the offending quoted text (HTML-escaped on render)
  "line": int | None, # best-effort line number
}
```

Output: a `Report` — ordered list of `Finding` plus summary counts by severity, rendered as text/JSON/HTML. No persistent storage; every run is stateless.

## Folder Structure

```
builds/2026-07-16-agentlint/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── skill/
│   └── SKILL.md
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── parser.py
│   ├── checks.py
│   ├── ai_review.py
│   └── report.py
└── tests/
    ├── fixtures/
    │   ├── clean_instructions.md
    │   ├── broken_instructions.md
    │   ├── mini_claude_md.md
    │   └── mini_index_md.md
    ├── test_parser.py
    ├── test_checks.py
    ├── test_ai_review.py
    ├── test_report.py
    └── test_cli.py
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v` (run from `builds/2026-07-16-agentlint/`)
- **What will be tested:**
  - Markdown parsing: heading extraction + slug generation (including duplicate-heading suffixing), file-path candidate extraction from inline code (including rejecting non-path code spans), markdown link classification (internal anchor vs. relative file vs. external URL)
  - Deterministic checks: broken file reference detection (both flag and pass cases), broken anchor detection (both cases), required-section detection (both cases), modal contradiction heuristic (flags real overlap, ignores unrelated statements)
  - AI review: parses a valid mocked JSON response into findings; degrades gracefully on malformed JSON from the mocked API; is skipped entirely (no network call attempted) when no API key is set; flags a ground-truth contradiction using fixtures modeling the real CLAUDE.md/index.md drift found tonight — the Anthropic API call is mocked in every test, never live
  - Report rendering: JSON structure correctness, text report contains all findings, HTML report escapes user-controlled excerpt text (XSS regression test)
  - CLI: exit code 0 on a clean file, exit code 1 on error-severity findings with `--fail-on error`, graceful error on a missing input file, HTML output actually written to the `--out` path

## Success Criteria

1. All tests pass (zero failures, minimum 15 tests)
2. Running the CLI against the fixture with broken references/anchors/sections correctly flags every seeded issue and only those issues (no false positives on the clean fixture)
3. The AI-review path, exercised with a mocked Anthropic response modeling the real CLAUDE.md/index.md drift scenario, correctly surfaces a ground-truth contradiction finding
4. HTML report renders correctly in a browser, is dark-mode, mobile-readable, and safely escapes injected excerpt text (verified by test, not just visual inspection)
5. The tool runs standalone (`python3 src/main.py audit ...`) with zero required third-party dependencies, and the Skill wrapper's documented invocation matches the CLI's actual interface

---

## Scope Changes

None — full scope as designed shipped tonight.
