# Manual — Renewal Radar

> **Version:** 1.0 (built 2026-08-22)
> **Complexity:** Ambitious

---

## What This Is

Renewal Radar keeps track of everything that quietly needs to be renewed before it lapses: domain registrations, SSL/TLS certificates for the sites you run, and manually-tracked admin renewals like business licenses, insurance, and professional memberships. Domain and certificate checks are genuinely live — no manual data entry, no guessing — using the free, public RDAP protocol (the modern, structured replacement for WHOIS) and a direct TLS handshake to read each certificate's real expiration date off the wire. Manual renewals get correct recurrence math (annual, monthly, every-N-months) so completing one automatically schedules the next occurrence at the right date, leap years and short months included. Everything renders into one dashboard, bucketed by urgency, so you can see at a glance what needs attention this week.

---

## Quick Start

1. `cd` into this build folder.
2. Register the domains you want monitored: `python3 renewal_radar.py add-domain --domain yourdomain.com --project "The Canada List"`
3. Add any manual renewals you want tracked: `python3 renewal_radar.py add-renewal --title "Business License" --category license --due-date 2027-01-15 --recurrence annual`
4. Run `python3 renewal_radar.py sync` to check every domain's registration + certificate status live.
5. Run `python3 renewal_radar.py render` and open `data/dashboard.html` in a browser.

---

## How to Use It

### Adding a domain to monitor

```
python3 renewal_radar.py add-domain --domain example.com --project "Kwyeter"
```

`--project` is optional — use it to group domains/renewals by which of your projects they belong to. Domain names are normalized to lowercase; adding the same domain twice returns a clear error rather than a silent duplicate.

### Syncing

```
python3 renewal_radar.py sync
```

For every monitored domain, this performs two live, no-credential checks:

- **RDAP** — looks up the domain's registration expiration date and registrar via the official IANA RDAP bootstrap registry. This is a normal outbound HTTPS request; it works from your own machine even though this build's own container environment blocked it during development (documented in `BUILD_LOG.md`).
- **TLS** — connects directly to the domain on port 443 and reads the live certificate's expiration date, exactly like a browser does.

One domain's failure (unsupported TLD, offline site, network hiccup) never stops the rest of the sync — it's recorded as `Unknown` and the run continues. Run `sync` as often as you like; a second sync on the same UTC day updates that day's snapshot rather than creating a duplicate, so your history stays one row per domain per day.

### Adding a manual renewal

```
python3 renewal_radar.py add-renewal \
  --title "Cottage Insurance" \
  --category insurance \
  --due-date 2027-06-01 \
  --recurrence annual \
  --project "Cottage"
```

- `--category` — one of `license`, `insurance`, `subscription`, `membership`, `certification`, `other`.
- `--recurrence` — one of `one-time`, `annual`, `monthly`, `every-N-months` (pair `every-N-months` with `--recurrence-n 3` for a quarterly renewal, for example).

### Completing a renewal

```
python3 renewal_radar.py complete --id 3
```

Marks that renewal done. If it's recurring, a new pending row is created at the correctly-computed next due date (a Feb 29 annual renewal correctly lands on Feb 28 in a non-leap year, and a Jan 31 monthly renewal correctly lands on the last day of February rather than overflowing into March). One-time renewals are simply marked done with no follow-up row. Find an item's `--id` from the `list` command's output or the rendered dashboard's table.

### Viewing the terminal summary

```
python3 renewal_radar.py list
```

Groups everything currently tracked — domains, certificates, and pending manual renewals — into urgency buckets: **Overdue**, **Due This Week**, **Due This Month**, **Upcoming**, **Healthy**, and **Unknown** (no successful check yet).

### Rendering the dashboard

```
python3 renewal_radar.py render
```

Writes `data/dashboard.html` — open it directly in any browser (double-click it, or `open`/`xdg-open`). It includes hero stats per urgency bucket, an "Attention This Week" panel, a per-domain certificate-expiration history chart (fills in as you run `sync` over time), and a searchable/sortable table of everything tracked. Pass `--output somewhere/else.html` to write it elsewhere.

### Optional AI Admin Briefing

If you export `ANTHROPIC_API_KEY` before running `render`, the dashboard's "Admin Briefing" panel is written by Claude Haiku instead of the built-in template — a short, prioritized summary of what needs attention. Only aggregate urgency-bucket counts and item titles/categories are ever sent; no RDAP/TLS payloads, registrar account details, or other personal data. With no key set (or if the API call fails for any reason), the deterministic template is used automatically — the tool is fully functional either way.

```
export ANTHROPIC_API_KEY=sk-ant-...
python3 renewal_radar.py render
```

---

## Configuration

No configuration file — everything is set via CLI flags. The SQLite database lives at `data/renewal_radar.db` by default; pass `--db path/to/other.db` to any command to use a different one (useful for keeping separate databases per project, for example).

| Setting | Default | Description |
|---------|---------|-------------|
| `--db` | `data/renewal_radar.db` | Path to the SQLite database |
| `ANTHROPIC_API_KEY` (env var) | unset | Enables the AI-written admin briefing; deterministic template used when unset |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `sync` reports RDAP `unknown` for every domain | Outbound HTTPS to `data.iana.org` is blocked (e.g. a restrictive network/proxy) | Check your network's outbound HTTPS policy; this is a normal public HTTPS endpoint with no auth required |
| `sync` reports SSL `unknown` for a specific domain | The domain doesn't serve HTTPS on port 443, is offline, or the hostname doesn't match its certificate | Confirm the site is actually live at `https://<domain>` in a browser |
| `add-domain` says the domain is already being monitored | You already added it | Use `list` to see everything currently tracked instead of re-adding |
| A recurring renewal's next date looks off by a day | Check the original `--due-date` was entered as `YYYY-MM-DD`; the recurrence math is exact but depends on that input being correct | Re-check the source due date; there is no `edit-renewal` command yet (see `FutureFeatures.md`) |
| `render` produces a dashboard with an empty domain history chart | No `sync` has been run yet, or only once | Run `sync` at least once (ideally on a couple of different days) to populate history |

---

## Known Limitations

- RDAP and TLS checks require outbound network access from wherever you run this tool; both are free and require no API key or account.
- There is no `remove-domain` or `edit-renewal` command yet — correcting a mistaken entry currently requires editing the SQLite database directly (see `FutureFeatures.md`).
- The AI briefing (when enabled) requires your own `ANTHROPIC_API_KEY`; it is never bundled with this build.
- This tool only observes and reminds — it never renews, pays, or takes any action against a registrar, certificate authority, or vendor on your behalf.
