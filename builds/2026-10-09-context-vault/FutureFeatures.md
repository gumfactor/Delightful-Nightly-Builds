# Future Features — Context Vault

1. **Codex and Copilot importers.** Add parsers for other agents' local session logs so one vault covers every tool, with a `source` column and filter.
2. **Resume-brief hook.** A Claude Code SessionStart hook that runs `ctxvault brief <cwd project>` and injects the result, so context returns automatically.
3. **MCP server.** Expose `search`, `get_session` and `brief` as MCP tools so a live session can query past ones itself.
4. **Semantic search.** Optional embeddings for "what did we decide about X" queries that don't share keywords.
5. **Stale-summary detection.** Record message count at summary time and flag summaries whose session has since grown.
6. **Decision log.** Aggregate every decision across projects into a timeline with links back to the exact message.
7. **Cost view.** Parse token usage fields to show per-project and per-week spend.
8. **Redaction pass.** Strip likely secrets (keys, tokens) before indexing or before sending to the summariser.
