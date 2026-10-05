# Burnrate — Manual

Analyzes local Claude Code transcripts (`~/.claude/projects/**/*.jsonl`). Nothing leaves your machine; there are no network calls except Chart.js loading from a CDN when you open the HTML.

## Run

```bash
cd src
python -m burnrate demo                # synthetic data, writes burnrate.html
python -m burnrate doctor              # check the parser against your real transcripts
python -m burnrate report --since 30   # HTML dashboard + text summary
python -m burnrate summary             # text only
python -m burnrate json > data.json
```

Options: `--root DIR`, `--since DAYS`, `--tz America/Toronto`, `--pricing FILE`, `--out FILE`. `CLAUDE_CONFIG_DIR` is honoured.

Run `doctor` first. `bad_lines` or `no_usage` close to `assistant_entries` means the transcript format differs from what the parser expects.

## Dashboard
Tiles (cost, cache hit, savings, output tokens, subagent share, active time), findings, daily cost and model charts, project/tool/session tables (click a header to sort). Works on a phone.

## Findings
- `retry_loop`: same Bash command failed 3+ times
- `read_thrash`: same file read 3+ times in a session
- `big_context`: context over 150k tokens
- `low_cache`: under 50% cache hits over 200k+ input tokens
- `high_error_rate`: over 25% of 10+ tool calls errored
- `unpriced_model`: add the model to `pricing.json`

## Pricing
Edit `pricing.json` (USD per million tokens). Values are estimates; check Anthropic's pricing page. Cache write defaults to 1.25x input and cache read to 0.1x.

## Tests
```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```
