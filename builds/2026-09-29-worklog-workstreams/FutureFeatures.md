# Future Features

Enhancements to a working tool (the capture, correlation and retrieval core ships tonight).

1. **MCP server + skill** exposing `standup`, `resume`, `why` so any agent can pull context; the core already has a JSON output mode to build on.
2. **Codex and Copilot session ingestion** — parsers for their local session formats, feeding the same checkpoint schema as `hook.py`.
3. **Cross-project "where was I?"** — one command ranking the latest active workstreams across all repos that have a ledger.
4. **Optional LLM synthesis** — draft `accomplished`/`next_steps` for auto-captured checkpoints from transcript tails; opt-in, every sentence citing event IDs.
5. **Teamwork / Coda link events** — attach tasks and docs as events so lab-admin work correlates with code.
6. **Scheduled sync** — a Claude Code Routine or cron entry running `sync` and mailing the standup each morning.
7. **Local evidence-graph viewer** — static HTML of workstreams and links for reviewing suggestions and accepting them with one click.
8. **Better weak correlation** — learn per-repo file-overlap thresholds from the merges/splits the user has already made.
9. **CI-log events** — failing-test names from Actions logs so `why` can cite the exact regression.
