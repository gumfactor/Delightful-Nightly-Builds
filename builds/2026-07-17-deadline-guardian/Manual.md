# Manual — Deadline Guardian

> **Version:** 1.0 (built 2026-07-17)
> **Complexity:** Ambitious Project

---

## What This Is

Deadline Guardian is a local command-line tool that tracks the recurring administrative deadlines that come with running a research lab and teaching — IRB/ethics renewals, grant progress reports, conference and manuscript submissions, course prep, student evaluations. Instead of retyping a due date and category every time a renewal notice or portal email arrives, you can paste the raw text at it and it extracts the structured deadline for you (using Claude if you supply an API key, or a built-in deterministic parser if you don't). It keeps everything in a local SQLite file and renders a self-contained, dark-mode HTML dashboard that groups deadlines by urgency — no server, no account, no cloud dependency.

---

## Quick Start

1. `cd` into this build folder.
2. Add your first deadline manually: `python3 deadline_guardian.py add --title "IRB renewal" --category "IRB/Ethics" --due-date 2026-09-01 --recurrence annual`
3. Or capture one from pasted text: `python3 deadline_guardian.py capture --text "Your grant progress report is due 2026-10-15."`
4. Generate the dashboard: `python3 deadline_guardian.py render`
5. Open `dashboard.html` in any browser (double-click it, or `open dashboard.html` / `xdg-open dashboard.html`).

---

## How to Use It

### Adding a deadline manually

```
python3 deadline_guardian.py add \
  --title "Annual empathy-lab IRB renewal" \
  --category "IRB/Ethics" \
  --due-date 2026-09-01 \
  --recurrence annual \
  --notes "Renew via the REB portal, not email"
```

`--category` must be one of: `Grant`, `IRB/Ethics`, `Course`, `Student Evaluation`, `Conference`, `Manuscript`, `Other`.

`--recurrence` is one of `none` (default), `annual`, `semesterly` (every 6 months), or `every_N_months` (requires `--recurrence-months N`).

### Capturing from pasted text (with or without AI)

```
python3 deadline_guardian.py capture --text "Reminder: your NSERC progress report is due October 15, 2026."
```

You can also pipe text in, or read from a file:

```
cat renewal_email.txt | python3 deadline_guardian.py capture
python3 deadline_guardian.py capture --file renewal_email.txt
```

**With `ANTHROPIC_API_KEY` set** in your environment, Claude reads the text and extracts title, category, due date, recurrence, and a one-sentence note. **Without it**, a deterministic fallback parser looks for an explicit date (ISO, `MM/DD/YYYY`, or "Month D, YYYY" formats) and infers the category from keywords (e.g. "IRB"/"REB" → IRB/Ethics, "grant"/"progress report" → Grant). Either way, the original pasted text is preserved in the database.

If no date can be found by either path, `capture` prints an error and exits with code 1 rather than guessing.

### Completing a deadline

```
python3 deadline_guardian.py complete --id 3
```

If that deadline has a recurrence rule, the next occurrence is automatically created with the correctly advanced due date — you never have to manually recreate an annual or semesterly commitment.

### Listing deadlines

```
python3 deadline_guardian.py list                    # human-readable, pending only
python3 deadline_guardian.py list --include-completed # include completed items
python3 deadline_guardian.py list --json              # machine-readable, for scripting
```

### Rendering the dashboard

```
python3 deadline_guardian.py render --output dashboard.html
```

Produces a single self-contained HTML file — no server, no external network calls when opened. It groups deadlines into **Overdue**, **Due This Week**, **Due This Month**, **Upcoming**, and **Completed**, with clickable category filter chips.

---

## Configuration

| Setting | Default | Description |
|---------|---------|--------------|
| `--db` (global flag, before the subcommand) | `data/deadlines.db` | Path to the SQLite database file. Set once and reuse across commands to keep working with the same data. |
| `ANTHROPIC_API_KEY` (environment variable) | not set | When set, `capture` uses Claude for extraction. When unset, the deterministic fallback parser is used automatically — the tool is fully functional either way. |
| `--output` (on `render`) | `dashboard.html` | Where the generated dashboard HTML is written. |

No configuration file is required — everything is a CLI flag or environment variable.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `capture` prints "Could not find a recognizable date in the supplied text" | Neither the fallback parser nor (if used) Claude could find an explicit date | Add an explicit date to the text, or use `add` manually |
| `add`/`capture` complain about an invalid category | A typo in `--category`, or Claude returned something unexpected (rare — it's clamped to `Other` automatically) | Use one of the exact category names listed above |
| Running the same commands twice shows a different database | You ran commands from different working directories, each creating its own `data/deadlines.db` | Always pass an explicit `--db /full/path/to/deadlines.db`, or always run from the same directory |
| `capture` silently uses the fallback parser even though `ANTHROPIC_API_KEY` is set | The API call failed (network issue, invalid key, rate limit) | This is by design — `capture` never hard-fails just because the AI path is unavailable. Check the key and network if you specifically need AI extraction |
| Dashboard shows no data after `render` | You ran `render` with a different `--db` than the one you added deadlines to | Check the `--db` path is consistent across `add`/`capture` and `render` |

---

## Known Limitations

- Relative dates like "in three weeks" or "next Friday" are not understood by the fallback parser — use an explicit date, or rely on Claude (which can sometimes resolve these, though this hasn't been extensively tested).
- There is no reminder/notification mechanism yet — you need to run `list` or open the dashboard to check status.
- Recurrence rules cover annual/semesterly/fixed-month-interval patterns; there is no semester-anchored ("every fall term") recurrence tied to an actual academic calendar.
- No calendar app integration (Google Calendar, Outlook) — this build's data sources don't include OAuth credentials for those services. See `FutureFeatures.md` for a planned `.ics` export as a lower-friction bridge.
