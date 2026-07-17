# Future Features — Deadline Guardian

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--warn-days` reminder threshold on `list`** — a CLI flag that returns a non-zero exit code if anything is overdue or due within N days, so this can be wired into a shell profile or cron job as a "you have deadlines" check without opening the dashboard.
2. **Snooze/postpone command** — `complete --id X --postpone-days N` variant that shifts a deadline's due date forward without marking it done, for the common case of a genuine short administrative delay (e.g. a portal outage pushing an IRB deadline back a week).
3. **CSV export** — a `list --csv` output mode alongside the existing `--json`, for pasting into a spreadsheet or sharing with a co-PI or lab manager.
4. **Search flag** — `list --search "IRB"` to filter by keyword across title/notes/source_text.

## Medium Effort (roughly one nightly build session)

5. **`ics` calendar file export** — generate a standard `.ics` file from the current deadline list so it can be imported into any calendar app (Google Calendar, Outlook, Apple Calendar) without needing OAuth credentials this build container doesn't have. This is the natural bridge to "real" calendar integration without the auth complexity.
6. **Batch capture from an mbox/email export** — extend `capture` to accept an exported `.mbox` or a folder of `.eml` files and run extraction across all of them in one pass, deduping by (title, due_date) so re-running on an updated export doesn't create duplicates. This would make the AI-extraction path dramatically more useful for someone with a backlog of unprocessed renewal emails.
7. **Recurring-deadline "series" view** — right now, completing a recurring deadline creates a fresh row with no link back to its predecessor. A `--series-id` grouping column would let the dashboard show "this is the 4th consecutive on-time renewal" style continuity, which is genuinely motivating for compliance-style recurring tasks.

## Ambitious Extensions (multi-session effort)

8. **Two-way sync with the 2026-07-10 Worklog build** — Worklog already correlates Git/GitHub/agent-checkpoint activity into workstreams; Deadline Guardian's admin deadlines are a natural fourth signal type ("this workstream has a grant report due in 12 days") that Worklog's dashboard could surface alongside code activity.
9. **Lightweight local daemon + OS notification** — a background process (launched manually, not auto-installed) that checks the SQLite file daily and fires a native desktop notification for anything crossing into the "due this week" bucket, without needing any cloud infrastructure or a persisting server.

---

## Possible Integration Points

- **Worklog (2026-07-10)** — see Ambitious Extension #8 above; both tools already use a local SQLite event/ledger pattern, so the data models are compatible.
- **AgentLint (2026-07-16)** — not a direct integration, but the same principle: a stale calibration note in a project's own instructions is exactly the kind of "recurring administrative fact that silently goes out of date" this build's category targets, just for personal admin instead of AI-instruction files.
- **Connectome (2026-07-11)** — if Deadline Guardian's `notes`/`source_text` fields grew richer over time, they could become another note source Connectome indexes, surfacing links between an admin deadline and related research notes.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| The fallback date parser only recognizes a handful of explicit date formats (ISO, slash, "Month D, YYYY", "D Month YYYY") — relative phrases like "in three weeks" or "next Friday" are not understood | Add a small relative-date grammar to `extraction.py`, anchored to the capture command's invocation date |
| `capture --file` and `--db`/`--output` paths are trusted CLI-supplied paths with no sandboxing — appropriate for a single-user local tool, but would need hardening before any multi-user or server deployment | Document explicitly in Manual.md (done); would need a path allow-list if ever exposed beyond single-user local use |
| No reminder/notification mechanism — the user must remember to run `list` or open the dashboard | See Ambitious Extension #9 (local daemon) or Medium Effort #5 (.ics export into an existing calendar app that already has reminders) |
| Recurrence is limited to none/annual/semesterly/every-N-months — doesn't cover more irregular academic patterns like "every fall term" tied to a specific semester start date rather than a fixed month offset | Add a semester-anchored recurrence type once a canonical semester-start-date source is available |
| The AI extraction prompt is a single fixed template with no few-shot examples, so its accuracy on unusual formats is untested beyond the mocked unit tests | Once the user runs this with a real API key, log actual vs. corrected fields to build a small eval set and refine the prompt |
