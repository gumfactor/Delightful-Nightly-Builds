# PRD — Renewal Radar

> **Build date:** 2026-08-22
> **Category:** I — Life Admin Helper
> **Complexity:** Ambitious
> **Day of week:** Saturday

---

## Goal

A CLI + dashboard that tracks every recurring "keep the lights on" renewal a solo technical founder juggles — domain registrations, SSL/TLS certificates, and manual admin renewals like business licenses, insurance, and software subscriptions — checking domains and certificates against live, no-auth network sources instead of relying on memory or a spreadsheet.

## User Story

As a solo founder and lab director running multiple live platforms (The Canada List, Kwyeter) alongside academic administration, I want a single place that automatically checks whether my domains and SSL certificates are close to expiring and reminds me about manually-tracked renewals (licenses, insurance, subscriptions), so that nothing lapses silently while I'm focused on research or product work.

## Scope

### In Scope
- `add-domain` — register a domain name to monitor, with an optional project label (e.g. "The Canada List", "Kwyeter")
- `sync` — for every monitored domain: perform a live RDAP lookup (via the IANA RDAP bootstrap registry, no auth) to find the domain's registration expiration date, and a live direct TLS handshake (Python stdlib `ssl`/`socket`, no external API) to read the certificate's expiration date; persist a dated snapshot per domain in local SQLite (same-day re-syncs upsert rather than duplicate, so a true multi-run history accumulates)
- `add-renewal` — add a manually-tracked recurring admin renewal (title, category [license/insurance/subscription/membership/certification/other], due date, recurrence [annual/monthly/every-N-months/one-time], optional project label)
- `complete` — mark a manual renewal instance done; automatically schedules the next occurrence for recurring items (leap-year- and month-length-safe date arithmetic), leaves one-time items completed
- `list` — terminal summary of every tracked item (domains, certs, manual renewals) grouped by urgency bucket: Overdue / Due This Week / Due This Month / Upcoming / Healthy / Unknown
- `render` — self-contained dark-mode HTML dashboard: hero stats, urgency-bucketed cards, a sortable/searchable table across all three source types (Domain / SSL / Manual), a per-domain expiration history line (native Canvas 2D, no CDN dependency), and an "Attention This Week" panel
- Optional Claude Haiku "This Week's Admin Briefing" — a short plain-English paragraph built only from the aggregate urgency-bucket counts and item titles/categories (never raw registration/cert payloads), with an unconditional deterministic-template fallback when `ANTHROPIC_API_KEY` is unset or the call fails
- Graceful per-item degradation: an RDAP or TLS failure for one domain (unsupported TLD, connection refused, timeout) is recorded as `unknown` for that check and never aborts the sync for other items

### Out of Scope
- Automatic renewal/payment of anything — this tool only observes and reminds, never takes action against a registrar, CA, or vendor
- Email/push notifications — output is the CLI and the rendered HTML dashboard only, opened manually
- WHOIS parsing (legacy, inconsistent text format) — RDAP is the modern, structured, standardized replacement and is used exclusively
- Certificate chain/trust validation, revocation checking, or any security audit of the cert beyond its expiration date
- Auto-discovery of domains from DNS zones, registrar accounts, or Canada List's own database — domains are added explicitly by the user

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** None
- **Dependencies:** stdlib only (`sqlite3`, `ssl`, `socket`, `urllib`, `json`, `argparse`, `datetime`); optional Anthropic API call via `urllib` (no `anthropic` package dependency, consistent with prior builds)
- **Runtime requirement:** `python3 renewal_radar.py <command> ...` — no install step; SQLite database file created on first run inside the build folder's `data/` directory

## Data Structure

SQLite database (`data/renewal_radar.db`, created on first run):

```sql
CREATE TABLE domains (
    id INTEGER PRIMARY KEY,
    domain TEXT NOT NULL UNIQUE,
    project_label TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE domain_snapshots (
    id INTEGER PRIMARY KEY,
    domain_id INTEGER NOT NULL REFERENCES domains(id),
    snapshot_date TEXT NOT NULL,        -- UTC date, YYYY-MM-DD; one row per domain per day (upsert)
    rdap_status TEXT NOT NULL,          -- 'ok' | 'unknown'
    rdap_expiration TEXT,               -- ISO date or NULL
    rdap_registrar TEXT,
    ssl_status TEXT NOT NULL,           -- 'ok' | 'unknown'
    ssl_expiration TEXT,                -- ISO date or NULL
    ssl_days_remaining INTEGER,
    UNIQUE(domain_id, snapshot_date)
);

CREATE TABLE manual_renewals (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,             -- license | insurance | subscription | membership | certification | other
    project_label TEXT,
    due_date TEXT NOT NULL,             -- ISO date
    recurrence TEXT NOT NULL,           -- 'one-time' | 'annual' | 'monthly' | 'every-N-months' (N stored in recurrence_n)
    recurrence_n INTEGER,               -- populated only for 'every-N-months'
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending' | 'done'
    created_at TEXT NOT NULL,
    completed_at TEXT
);
```

Urgency buckets are computed live from the latest snapshot / due date at `list`/`render` time (never stored), using fixed day thresholds: Overdue (< 0 days), Due This Week (0–7), Due This Month (8–30), Upcoming (31–90), Healthy (> 90), Unknown (no successful check yet).

## Folder Structure

```
builds/2026-08-22-renewal-radar/
├── PRD.md
├── WhyThis.md
├── BUILD_LOG.md
├── FutureFeatures.md
├── Manual.md
├── requirements.txt
├── renewal_radar.py          (CLI entry point, argparse subcommands)
├── src/
│   ├── __init__.py
│   ├── db.py                 (SQLite schema + CRUD)
│   ├── rdap.py                (IANA RDAP bootstrap lookup + domain expiration parsing)
│   ├── tls.py                  (direct TLS handshake cert expiration check)
│   ├── recurrence.py         (leap-year-safe next-occurrence date math)
│   ├── urgency.py             (urgency bucket classification)
│   ├── ai_briefing.py         (optional Claude Haiku call + deterministic fallback)
│   └── render.py              (self-contained HTML dashboard generator)
├── tests/
│   ├── test_db.py
│   ├── test_rdap.py
│   ├── test_tls.py
│   ├── test_recurrence.py
│   ├── test_urgency.py
│   ├── test_ai_briefing.py
│   ├── test_render.py
│   └── test_cli.py
└── data/                      (created at runtime; empty at commit time, contains .gitkeep)
```

## Testing Strategy

- **Framework:** pytest
- **Test file location:** `tests/test_*.py`
- **Run command:** `python -m pytest tests/ -v`
- **What will be tested:**
  - RDAP bootstrap TLD-to-server matching and expiration-event parsing across differently-shaped RDAP JSON responses (all network calls mocked via monkeypatched `urllib.request.urlopen`)
  - RDAP lookup failure (timeout, 404, malformed JSON, unsupported TLD) degrades to `unknown` rather than raising
  - TLS certificate expiration parsing from a mocked `ssl`/`socket` peer certificate, including the `notAfter` date-format parse
  - TLS lookup failure (connection refused, timeout, hostname mismatch) degrades to `unknown` rather than raising
  - Recurrence math: annual/monthly/every-N-months next-date computation, including a Feb 29 leap-year renewal advancing correctly in a non-leap year, and a 31-day-month due date advancing into a 30-day or 28/29-day month
  - `complete` on a one-time renewal marks it done with no next occurrence created; on a recurring renewal creates exactly one new pending row at the correct next date
  - Urgency bucket boundaries (exactly 0, 7, 8, 30, 31, 90, 91 days) classify into the correct bucket, and an item with no successful check classifies as Unknown
  - SQLite same-day domain sync upserts (two syncs on the same UTC date produce one snapshot row, not two)
  - AI briefing: with no `ANTHROPIC_API_KEY` set, zero network calls are made (asserted via a mocked `urlopen` call-count) and the deterministic template is returned; with a mocked successful API response, the AI text is used; on a mocked API failure, falls back to the deterministic template without raising
  - HTML render escapes/neutralizes a live script-injection payload placed in a domain's project label and a manual renewal's title (verified by asserting the raw payload string never appears unescaped in the generated HTML, and that all dynamic data reaches the page via an escaped JSON payload read with `textContent`, never `innerHTML`)
  - CLI argument handling: missing required argument, invalid category, invalid recurrence, and adding a duplicate domain each produce a clear error rather than a traceback

## Success Criteria

1. All tests pass (zero failures)
2. `sync` correctly separates domains into `ok` vs `unknown` RDAP/SSL status based on live (or, in this build container, mocked-for-tests / attempted-live) lookups, and never crashes the whole run on one domain's failure
3. `complete` on a recurring manual renewal always produces exactly one correctly-dated next occurrence, verified against leap-year and month-length edge cases
4. `render` produces a dashboard that opens directly in a browser, correctly buckets every tracked item by urgency, and is verified live in headless Chromium to render a script-injection payload as inert text
5. The AI briefing path makes zero network calls when no API key is set (verified in tests) and never blocks core functionality when the Anthropic API is unreachable
