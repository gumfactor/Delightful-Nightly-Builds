# PRD — Burnrate

> **Build date:** 2026-10-05
> **Category:** H — Developer Tool
> **Complexity:** Ambitious Project
> **Day of week:** Monday (day-of-year 278, index 7 → H)

---

## Goal

Turn the user's local Claude Code session transcripts into a cost, cache-efficiency and wasted-effort dashboard with concrete findings (Read-thrash, retry loops, runaway context) that the Claude UI does not provide.

## User Story

As an associate professor and solo founder who runs many simultaneous AI coding sessions across projects, I want to see where my tokens and dollars go per project, day and model, and which sessions wasted effort, so that I can change how I work with agents before the bill or the context-loss friction grows.

## Scope

### In Scope
- Recursive scan of Claude Code transcripts (`~/.claude/projects/**/*.jsonl`, or `$CLAUDE_CONFIG_DIR/projects`, or `--root`).
- Defensive JSONL parser: skips malformed lines, dedupes streamed assistant messages by message id (max usage per field), tags subagent (sidechain) turns, links `tool_use` to `tool_result` errors.
- Editable pricing table (`pricing.json`, USD per million tokens, longest-substring model match, cache write/read multipliers); unknown models reported as unpriced, never silently zero-costed.
- Metrics: tokens and estimated cost by day (configurable timezone, default America/Toronto), model, project, session; cache hit ratio and estimated dollars saved by caching; tool histogram and error rate; peak context per session; active time (gaps under 5 minutes); subagent share.
- Findings engine with severity: `read_thrash`, `retry_loop`, `low_cache`, `big_context`, `high_error_rate`, `unpriced_model`.
- Outputs: self-contained mobile-readable HTML dashboard (Chart.js 4.4.4 pinned CDN, light/dark), text summary, JSON export, `doctor` command that reports parse health.
- `demo` command generating a synthetic transcript corpus so the dashboard can be seen without personal data.

### Out of Scope
- Sending any transcript content anywhere (fully local; no API calls at all).
- Other agents' formats (Codex, Copilot) — parser is isolated so adapters can be added.
- Billing reconciliation with Anthropic invoices (costs are estimates).

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None
- **Dependencies:** stdlib only at runtime (`zoneinfo`); `pytest` for tests; Chart.js 4.4.4 via CDN in the HTML
- **Runtime requirement:** `python -m burnrate report` from `src/`; open the generated HTML file

## Data Structure

Input line (one JSON object per line; fields used, all optional-tolerant):
`type` (`assistant`|`user`), `sessionId`, `cwd`, `timestamp` (ISO-8601), `isSidechain`, `requestId`, `message.id`, `message.model`, `message.usage.{input_tokens,output_tokens,cache_creation_input_tokens,cache_read_input_tokens}`, `message.content[]` blocks `tool_use{id,name,input}` and `tool_result{tool_use_id,is_error}`.

Internal: `Turn(session_id, project, ts, model, input, output, cache_write, cache_read, sidechain, tools[(id,name,key)])`, `Session(id, project, turns, results{tool_use_id: is_error})`. Analysis output is one JSON-serializable dict (`totals`, `by_day`, `by_model`, `by_project`, `sessions`, `tools`, `findings`, `unpriced_models`).

## Folder Structure

```
builds/2026-10-05-burnrate/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── pricing.json
├── src/burnrate/__init__.py
├── src/burnrate/__main__.py
├── src/burnrate/parse.py
├── src/burnrate/pricing.py
├── src/burnrate/analyze.py
├── src/burnrate/report.py
├── src/burnrate/demo.py
├── src/burnrate/cli.py
├── tests/conftest.py
├── tests/test_parse.py
├── tests/test_pricing.py
├── tests/test_analyze.py
└── tests/test_report_cli.py
```

## Testing Strategy

pytest against synthetic JSONL fixtures written to `tmp_path`: parser (malformed lines, streaming dedupe, sidechain, tool-result linking, missing usage), pricing (substring match, overrides, unpriced, cache multipliers), analysis (cost math, cache savings, timezone day bucketing, each finding rule with positive and negative cases), report (HTML embeds valid JSON, `</script>` in names is escaped), CLI (`demo`, `report`, `doctor`, missing root exit code). No network, no real transcripts.

## Success Criteria

1. `demo` then `report` produces a self-contained HTML dashboard whose embedded data matches the text summary.
2. Streamed duplicate assistant entries are counted once; malformed lines never crash a scan and are counted in `doctor`.
3. Every finding rule fires on a crafted bad session and stays silent on a healthy one.
4. Unknown models are listed as unpriced rather than costed at zero.
5. At least 15 tests pass; no network access or transcript content leaves the machine.
