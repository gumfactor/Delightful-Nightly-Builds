# Future Features

1. **Semantic search:** local embeddings alongside FTS5 so "the thing about duplicate franchises" finds it without the exact words.
2. **SessionStart hook:** a Claude Code hook that injects `brief <current project>` automatically at session start, so no copy/paste is needed.
3. **MCP server:** expose `search_sessions` and `project_brief` as MCP tools so an agent can look up past decisions mid-session.
4. **More parsers:** Codex, Copilot Chat and Cursor transcript formats via the parser registry.
5. **Decision log view:** cross-session timeline of extracted decisions per project, linking back to the source message.
6. **Stale-open-item tracking:** mark open items resolved when a later session mentions completing them.
7. **Teamwork/Coda link-out:** push open items from the brief into a Teamwork task list.
8. **Watch mode:** re-ingest on file change instead of the manual Rescan.
