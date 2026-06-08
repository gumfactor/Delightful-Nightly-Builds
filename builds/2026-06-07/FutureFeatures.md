# Future Features — Git Standup Reporter

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--since DATE` flag** — Accept an explicit date/time string in addition to `--hours`, e.g. `--since "2026-06-06 09:00"`. Git supports arbitrary `--since` values; this just passes it through, removing the need to calculate hours manually when you want commits "since Monday morning."

2. **`--no-merge` flag** — Pass `--no-merges` to git log to hide merge commits (e.g. from pull requests). Merge commits clutter standup output since they rarely represent discrete work items.

3. **`--output FILE` flag** — Write the standup report to a file instead of stdout. Useful for logging daily standups to a journal file automatically via cron.

4. **`--days N` alias** — `--days 7` as a more readable alias for `--hours 168`. Days is a more natural unit when reviewing a week of work.

5. **Relative timestamp in output** — Show "2 hours ago" instead of the raw ISO timestamp for each commit. Python's stdlib `datetime` handles this arithmetic without new dependencies.

## Medium Effort (roughly one nightly build session)

6. **Config file support (`~/.standup.toml` or `standup.toml`)** — Allow the user to define a default list of repo paths, default hours, and default author. Running bare `python3 main.py` from anywhere would then scan all configured repos without any flags. This moves the tool from "useful when remembered" to "run it from anywhere and get your full picture."

7. **Shell-script launcher / installer** — A small `install.sh` that creates a `standup` symlink in `~/.local/bin`, making `standup` callable from any terminal without the full Python path. Includes a short `standup --help` reminder in the output footer.

## Ambitious Extensions (multi-session effort)

8. **Cross-session standup journal** — Append each standup run (with timestamp) to a local JSONL file. Add a `--history` command to review past standups by date, search by keyword, and track which projects have been active most recently. This turns a one-shot report into a searchable personal commit journal — a meaningful complement to the ctxlog build (2026-06-06).

9. **Multi-machine / multi-account support** — Support reading from remote repos via SSH by adding a `--fetch` flag that runs `git fetch` before reading the log. Useful when work happens across a laptop, desktop, and remote server that don't always push immediately.

---

## Possible Integration Points

The AI Session Context Bridge (ctxlog, built 2026-06-06) is a natural complement: the ctxlog `handoff` command generates an AI priming document, and standup output could feed directly into it as the "recent git activity" section, replacing the manual `--files` and `--context` fields that hurt ctxlog's usability score. A future build could wire them together: `standup . | ctxlog add --project X --context -`.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| Commit signing disabled in tests via `commit.gpgsign = false` fixture config | Tests are correct and self-contained; the fix is environment-specific (this remote CI environment uses a signing server). A conftest.py note documents why. |
| Default author detection reads the first valid path only | Loop through all paths and use the most frequently appearing author; or use `git config --global user.name` as a final fallback before giving up. |
| Repos with the same top-level directory name collide in the output dict | Use full path as key when two repos resolve to the same basename; display `name (path)` in the output header to disambiguate. |
| `--hours 0` shows "0 hours" in output instead of a more helpful message | Special-case hours=0 to say "Nothing committed in this window." or prohibit it with an argparse minimum=1 constraint. |
