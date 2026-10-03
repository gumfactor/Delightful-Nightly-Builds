# PRD — Session Atlas

> **Build date:** 2026-10-03
> **Category:** F — Data Explorer
> **Complexity:** Ambitious
> **Day of week:** Saturday

## Goal

Turn the raw Claude Code session logs on the user's machine (`~/.claude/projects/**/*.jsonl`) into a searchable SQLite index and an interactive HTML explorer showing where AI-assisted time, tokens and edits actually go, with a one-click "resume prompt" for every past session.

## User Story

As a researcher-founder running many simultaneous AI-assisted projects, I want to explore every Claude Code session I have run (time, tokens, estimated cost, tools, files touched, what I asked, where I stopped), so that I can re-establish context across sessions and see which projects consume my AI effort.

## Scope

### In Scope
- Tolerant JSONL parser for Claude Code transcripts: user prompts (excluding tool results and meta messages), assistant messages deduplicated by message id, usage (input/output/cache), models, tool calls, files edited, tool errors, sidechain (subagent) messages, git branch, cwd, timestamps.
- Active-time estimate (gaps over a configurable idle threshold are not counted).
- Cost estimate from an editable price table (`--prices prices.json`), clearly labelled as an estimate; unknown models flagged, not guessed.
- SQLite index (`atlas.db`) with incremental re-indexing (skips files whose size+mtime are unchanged) and FTS5 full-text search over prompts, falling back to LIKE when FTS5 is missing.
- Aggregations: daily activity, weekday x hour heatmap, per-project rollups, tool usage, model mix, cache hit ratio, files churned (edited repeatedly in one session).
- Self-contained HTML explorer (no CDN, no build step): KPI row, daily chart, heatmap, sortable/filterable projects and sessions tables, full-text search, per-session detail with a copyable resume prompt. Mobile readable, light/dark.
- Optional AI layer: `--summarize` asks the Anthropic API (runtime `ANTHROPIC_API_KEY`) for a 2-sentence "where I left off" summary per session; cached in SQLite; only runs for sessions without a cached summary.
- `--demo` generates a synthetic log tree so the explorer can be tried immediately.
- CLI subcommands: `report` (default), `search <query>`, `stats`.

### Out of Scope
- Reading transcripts from other tools (Codex, Copilot).
- Editing or deleting logs. The tool only reads logs.
- Hosted/shared dashboards.

## Tech Stack

- **Language:** Python 3.11+ (generator) + vanilla JS (report)
- **Framework:** None
- **Dependencies:** stdlib only at runtime; pytest and playwright (browser smoke tests) for development
- **Runtime requirement:** `python3 main.py` then open `atlas.html`

## Data Structure

Log line (subset used): `{type, timestamp, sessionId, cwd, gitBranch, isSidechain, isMeta, message:{id, role, model, content: str | [ {type:text|tool_use|tool_result, ...} ], usage:{input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens}}}`.

SQLite tables: `files(path, size, mtime)`, `sessions(id, project, branch, start, end, active_seconds, prompts, assistant_msgs, sidechain_msgs, tool_errors, input_tokens, output_tokens, cache_write_tokens, cache_read_tokens, cost_usd, unpriced, models_json, tools_json, files_json, first_prompt, last_prompt, last_assistant, summary, source)`, `prompts(session_id, ts, text)` + `prompts_fts` virtual table.

## Folder Structure

```
builds/2026-10-03-session-atlas/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── main.py
├── requirements.txt
├── src/atlas/__init__.py
├── src/atlas/parser.py
├── src/atlas/pricing.py
├── src/atlas/store.py
├── src/atlas/stats.py
├── src/atlas/summarize.py
├── src/atlas/report.py
├── src/atlas/demo.py
├── src/atlas/template.html
└── tests/
    ├── conftest.py
    ├── test_parser.py
    ├── test_pricing.py
    ├── test_store.py
    ├── test_stats.py
    ├── test_summarize.py
    ├── test_report.py
    └── test_browser.py
```

## Testing Strategy

pytest. Parser tests use inline fixtures covering streaming duplicates, tool-result-only user turns, malformed lines, string vs block content, sidechains and idle gaps. Store tests cover incremental indexing and search (FTS and LIKE paths). Summarizer tests inject a fake transport (no network). Report tests check the embedded JSON is script-safe (`</script>` escaping). Browser tests (Playwright via pytest, skipped if Chromium is unavailable) load the generated demo report, check KPIs, filtering, search, the detail panel and that prompt text containing HTML is rendered as text.

## Success Criteria

1. `python main.py --demo` produces an `atlas.html` that opens offline and shows KPIs, daily chart, heatmap, projects and sessions from the synthetic logs.
2. Re-running against unchanged logs re-parses zero files; changed files are re-parsed.
3. Search finds prompts across sessions (FTS5 and fallback) and the HTML explorer filters live.
4. Every session detail offers a resume prompt built from its real first/last prompts, files edited and last assistant message.
5. No network calls except the optional `--summarize`, which is fully mocked in tests; at least 15 tests pass.

## Scope Changes
(none yet)
