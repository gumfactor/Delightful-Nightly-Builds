# Manual — Preprint Pulse

> **Version:** 1.0 (built 2026-09-13)
> **Complexity:** Ambitious Project

---

## What This Is

Preprint Pulse turns "I should write something about this research trend" into an actual first draft. Point it at a topic and it queries arXiv live, runs a deterministic trend/fact-extraction engine over the matched papers, and hands back a Markdown article draft plus an HTML report — trend direction, rising keywords, and concrete figures (sample sizes, p-values, effect sizes) each traced to a specific paper. With an `ANTHROPIC_API_KEY` set, an optional Claude Haiku pass turns those facts into polished prose; without one, a deterministic template still produces a complete, readable draft.

---

## Quick Start

1. `cd` into this build folder.
2. `python3 src/main.py digest --topic "your research topic here"`
3. Open the printed HTML report path in a browser, or the `.md` file in your editor/CMS.
4. Optionally add `--ai` with `ANTHROPIC_API_KEY` set in your environment for an AI-polished draft instead of the template version.

No install step is required beyond Python 3.11+ — everything is standard library.

---

## How to Use It

### `digest` — full pipeline (fetch, analyze, draft, render)

```bash
python3 src/main.py digest --topic "affective neuroscience of empathy" \
  --categories q-bio.NC,cs.CY \
  --months 12 \
  --max-results 150 \
  --out ./output
```

Writes `<out>/<slugified-topic>.md` and `<out>/<slugified-topic>.html`. Prints a one-line summary (paper count, trend direction, draft source) to the terminal.

Add `--ai` to attempt a Claude Haiku drafting pass. It reads `ANTHROPIC_API_KEY` from your environment — nothing is ever prompted for or hardcoded. If the key is missing, or the API call fails for any reason (network, rate limit, malformed response), the tool falls back automatically to the deterministic template and still produces a complete draft; check the printed "draft source" line (`ai` or `template`) to see which path was used.

### `trend` — quick terminal-only check, no files written

```bash
python3 src/main.py trend --topic "large language model agents" --months 6
```

Useful for a fast "is this actually heating up?" sanity check before committing to a full digest run.

### Example output

See `sample_output/digest.md` and `sample_output/digest.html` for a full worked example (a 12-paper synthetic corpus on "large language model agents") showing the shape of the deliverable without needing to run the tool first.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--months` | 18 | Trailing window size, in months, for both the arXiv query and the trend/keyword analysis |
| `--max-results` | 150 | Maximum papers fetched from arXiv per run |
| `--categories` | none | Comma-separated arXiv category codes (e.g. `cs.AI`, `q-bio.NC`) to narrow the search |
| `--out` | `./output` | Directory for the generated draft, report, and local cache |
| `--no-cache` | off | Skip the local response cache and always hit arXiv fresh |
| `--cache-ttl-hours` | 24 | How long a cached response stays fresh before a re-run re-fetches |
| `--ai` (digest only) | off | Attempt a Claude Haiku drafting pass using `ANTHROPIC_API_KEY` from the environment |
| `ANTHROPIC_API_KEY` (env var) | unset | Your own Anthropic API key, read only when `--ai` is passed. Never hardcode this — export it in your shell or a local `.env` you `source` yourself. |
| `ANTHROPIC_MODEL` (env var) | `claude-haiku-4-5` | Override the model used for the AI drafting pass |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `error: could not fetch from arXiv: ...` and exit code 1 | No network access, or arXiv API is temporarily down/rate-limiting | Retry after a moment; check your own network connection. This tool makes no other external calls unless `--ai` is passed. |
| Digest report shows "draft source: template" even with `--ai` passed | `ANTHROPIC_API_KEY` isn't set, or the API call failed and the tool fell back safely | Check `echo $ANTHROPIC_API_KEY` is set in the shell you're running from; check your API usage/limits if it is set |
| "No arXiv papers matched" in the draft | Topic too narrow, or `--months`/`--categories` filtered everything out | Try a broader topic phrase, a longer `--months` window, or drop `--categories` |
| Chart doesn't render in the HTML report | The Chart.js CDN is unreachable (e.g. offline, or a restricted network) | A plain data table renders automatically in its place — all the same numbers, just without the bar chart |
| Re-running the same topic returns stale-looking data | The local cache under `<out>/cache/` is still within its TTL | Pass `--no-cache`, or lower `--cache-ttl-hours` |

---

## Known Limitations

- Single data source: arXiv only. Fields or venues with low preprint adoption (much of clinical medicine, most social science) will return thin or empty results — this tool is strongest for CS/AI/physics/quantitative-biology topics.
- The AI drafting pass sends the full extracted-fact set to Claude in one request; on an unusually broad topic with hundreds of matched papers, the prompt could get large. `--max-results` caps this in practice.
- Rising-keyword detection is a straightforward first-half-vs-second-half presence count, not a statistical significance test — treat "rising" as a useful heuristic pointer, not a p-value-backed claim.
- `sample_output/` is a hand-authored demonstration corpus (12 realistic but synthetic papers), not a live arXiv snapshot — regenerate it from a real `digest` run once you have network access to see live data.
