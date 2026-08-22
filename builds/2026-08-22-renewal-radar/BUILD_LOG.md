# Build Log — Renewal Radar

> **Date:** 2026-08-22
> This is a live log. Claude appends entries throughout the build session.
> Entries are written in plain prose. Timestamps are UTC where available.

---

## Log

### [08:09 UTC] Session Start

- Read CLAUDE.md, PROFILE.md, STANDARDS.md.
- Step 0: checked `builds/` for the most recent dated folder (2026-06-18-regex-dojo, local checkout) — its `BUILD_LOG.md` ends with "Build complete. Success criteria reviewed. All tests passing." — done, no resume needed.
- Synced `builds/index.md` and `builds/ideas.md` from the most recent open PR branch (`claude/cool-sagan-w0k5dx`, PR #77, build #77 dated 2026-08-20) per Step 1 — local `main`/working branch was ~9 build-nights behind.
- Day of year 234 → `category_index = (234-1) % 9 = 8` → Category I — Life Admin Helper.
- `builds/ideas.md` held zero pending Category I rows → lottery skipped, went straight to fresh idea generation (Step 2d).
- Reviewed last 10 builds and all 5 prior Category I builds for topic diversity; no investment/finance saturation in the last 10. Chose Renewal Radar (domain/SSL/manual admin renewal tracker) over a habit log and a generic checklist tracker — full reasoning in `WhyThis.md`.
- Build folder created: `builds/2026-08-22-renewal-radar/`.

### [08:30 UTC] PRD Written

- Goal: live RDAP + TLS-based domain/certificate expiration tracker plus manually-tracked recurring admin renewals, rendered as a dashboard.
- Scope: `add-domain`, `sync`, `add-renewal`, `complete`, `list`, `render`, optional Claude Haiku weekly briefing.
- Notable constraints/decisions: stdlib-only Python (no `anthropic` package — direct `urllib` POST, matching prior builds' convention); RDAP via the official IANA bootstrap registry rather than a third-party proxy, so no single external service is a hard dependency; WHOIS explicitly out of scope in favor of RDAP (structured, standardized, no text parsing).

### [08:45 UTC] Build Phase — Core Modules

- `src/db.py`: SQLite schema + CRUD for domains, per-day domain snapshots (upsert on `(domain_id, snapshot_date)` so repeat same-day syncs never duplicate), and manual renewals with category/recurrence validation.
- `src/recurrence.py`: leap-year- and month-length-safe next-occurrence date math (`_add_months` clamps the target day to the destination month's actual length rather than overflowing).
- `src/urgency.py`: pure function mapping days-remaining to a fixed urgency bucket, with `None` → `Unknown`.
- `src/rdap.py`: fetches the official IANA RDAP bootstrap registry (`https://data.iana.org/rdap/dns.json`) to resolve a domain's TLD to its authoritative RDAP server(s), queries `{server}/domain/{name}`, and parses the `expiration` event + registrar vcard out of the RDAP JSON. Every failure mode (unsupported TLD, bootstrap fetch failure, query failure, malformed JSON) degrades to `status: 'unknown'` with a message rather than raising, so one bad domain never aborts a `sync` run. `urlopen` and an optional pre-fetched `bootstrap` map are both injectable for testing.
- `src/tls.py`: live TLS handshake (stdlib `ssl` + `socket`, no external API) to read a host's certificate `notAfter` field directly off the wire — genuinely the same signal a browser's own certificate warning uses. Same never-raises/degrade-to-unknown contract as RDAP.
- `src/ai_briefing.py`: optional Claude Haiku "This Week's Admin Briefing", built only from aggregate urgency-bucket counts and item titles/categories (never raw RDAP/TLS payloads or registrar account details); unconditional deterministic-template fallback, matching the `direct urllib POST, claude-haiku-4-5-20251001` convention confirmed by reading the already-merged 2026-08-13 Macro Kitchen build's `ai_notes.py` on its own PR branch (each nightly build's own PR branch only carries its own diff off `main`, so this was fetched directly rather than assumed).
- `src/render.py` / `src/items.py`: `items.py` builds the single unified list of tracked items (domain registration, SSL cert, manual renewal) shared by both `list` and `render` so the two views can never disagree; `render.py` emits a self-contained dark-mode HTML dashboard with all dynamic data delivered via a `<script type="application/json">` payload (`</` escaped to `<\/` to prevent a hostile title from prematurely closing the script tag) read back with `JSON.parse(el.textContent)`, and every DOM node built with `createElement`/`textContent` — no `innerHTML` anywhere.
- `renewal_radar.py`: argparse CLI wiring `add-domain`, `sync`, `add-renewal`, `complete`, `list`, `render` together.

### [09:05 UTC] Tests Written and Run

Tests: 67 passed, 0 failed. (`/root/.local/bin/pytest tests/ -v` from the build directory — the container's default `python3` had no `pytest` installed and `pip install` was denied by the session's permission mode, so the pre-existing `pytest` binary at `/root/.local/bin/pytest`, a `uv tool install`, was used instead; it runs the same stdlib-only test suite against the same Python 3.11.)

Coverage highlights: RDAP TLD-to-server resolution and expiration-event parsing across multiple mocked response shapes; RDAP/TLS failure modes (timeout, connection refused, DNS failure, malformed data, unsupported TLD) all degrade to `unknown` rather than raising; recurrence math across a Feb 29 → non-leap-year annual renewal and a Jan 31 → February monthly renewal; urgency bucket boundaries at every threshold (7/8/30/31/90/91 days); same-day snapshot upsert; AI briefing's zero-network-calls guarantee with no API key (asserted via a call-count-incrementing fake `urlopen` that raises if ever invoked); a live script-injection payload (`</script><script>alert(1)</script>`) in a render title verified to survive the JSON round-trip intact as inert text and never appear as a raw closing tag in the HTML; full CLI flows (add/sync/complete/list/render) including argparse's built-in rejection of an invalid `--category`.

### [09:15 UTC] Manual End-to-End Verification

Ran the real CLI against the live `data/renewal_radar.db` (not a test double): `add-domain` for two real public domains (`anthropic.com`, `example.com`), three `add-renewal` entries (annual, annual, one-time), then `sync`.

- **RDAP**: failed with `403 Forbidden` from this build container's egress proxy fetching `data.iana.org` — the expected, documented build-container network constraint (CLAUDE.md §2f), not a design flaw. Degraded to `unknown` for both domains exactly as designed, and the run completed without aborting.
- **TLS**: succeeded live. A direct socket TLS handshake to port 443 is not routed through the container's HTTP egress proxy, so `anthropic.com` and `example.com`'s real certificate expiration dates were read genuinely live (`anthropic.com` → 2026-09-19, 28 days out at the time of the run) — real signal, not a mock, even inside this constrained container. Documented here since it's a meaningfully different result from most prior builds' "blocked in-container, works for the user" story.
- `complete` on the annual renewal correctly scheduled the next occurrence at `due_date + 1 year`; `complete` on the one-time renewal created no next occurrence; `complete --id 99` on a nonexistent id printed a clear error and returned exit code 1.
- `list` correctly bucketed every item (Due This Week / Due This Month / Healthy / Unknown) matching the live data.
- `render` (with no `ANTHROPIC_API_KEY` set) produced the dashboard using the deterministic briefing template.
- Live headless-Chromium QA (Playwright, `/opt/pw-browsers/chromium`, installed to a scratch directory outside the build folder): zero dialogs, zero page errors, zero console errors, and no injected `window` global after loading the dashboard with a manual renewal titled `</script><script>alert(1)</script>` — the payload rendered as plain visible text in the table, never executed. Search filter, column sort, and the domain-history dropdown were all exercised live and worked correctly. A 390×844 mobile-viewport screenshot confirmed no page-level horizontal scroll (the items table scrolls independently inside its own `overflow-x: auto` wrapper).
- The manually-created `data/renewal_radar.db` and `data/dashboard.html` from this verification pass are excluded from the commit via `.gitignore` (only `data/.gitkeep` ships) — they were QA artifacts, not part of the delivered build.

Build complete. Success criteria reviewed. All tests passing.

