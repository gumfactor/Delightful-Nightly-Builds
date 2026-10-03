# Session Atlas — Manual

Explore your Claude Code session logs: time, tokens, estimated cost, tools, files edited, and a paste-ready resume prompt for every session. Read-only; it never modifies your logs.

## Run

```bash
cd builds/2026-10-03-session-atlas
python3 main.py --tz-offset -4          # indexes ~/.claude/projects, writes atlas.html
python3 main.py --demo                  # try it on synthetic logs
```
Open `atlas.html` in a browser (works offline, phone-readable). Python 3.11+, stdlib only.

## Options
| Flag | Meaning |
|---|---|
| `--logs DIR` | Log root (default `~/.claude/projects`) |
| `--db FILE` | SQLite index (default `atlas.db`); re-runs only re-parse changed files |
| `--out FILE` | HTML output (default `atlas.html`) |
| `--since 2026-09-01` | Only sessions from that date |
| `--tz-offset -4` | Hours from UTC for day/hour charts (Toronto: -5 winter, -4 summer) |
| `--idle-gap 300` | Seconds of silence not counted as active time |
| `--prices prices.json` | Override price table, e.g. `{"sonnet": {"input": 3, "output": 15}}` (USD per million tokens) |
| `--summarize` | Add 2-sentence "where it stopped" summaries via Anthropic API (needs `ANTHROPIC_API_KEY`; sends prompt excerpts to Anthropic; cached; default 25 newest sessions, `--summarize-limit`) |

Subcommands: `python3 main.py search "firebase rules"` (terminal prompt search), `python3 main.py stats` (totals).

## Using the explorer
- KPI row, daily chart (switch metric), weekday x hour heatmap.
- Click a project row to filter sessions; click again to clear. Column headers sort.
- Search box filters live across prompts, files, branch, summaries.
- Click a session for details and the **resume prompt**; "Copy resume prompt" puts it on the clipboard. Paste into a fresh Claude session.

## Caveats
- Costs are estimates from an editable table; models with no price entry are excluded and marked `*`.
- Log format is not formally documented; unknown lines are skipped.
- Only the first 40 prompts per session (300 chars each) are embedded in the HTML search; `search` on the CLI covers everything.

## Tests
```bash
pip install -r requirements.txt
python3 -m pytest tests/ -v
```
Browser tests use the Chromium at `/opt/pw-browsers` or `CHROMIUM_PATH`; they skip if none is found.
