# Future Features — Renewal Radar

> Ideas for extending this build. Claude generates these based on what was built.
> The user decides whether to pursue them in future builds or manually.

---

## Quick Wins (under 1 hour to add)

1. **`--days-ahead` filter for `list`** — a flag to only print items due within N days (e.g. `list --days-ahead 14`), useful for a quick "what needs attention right now" check without scrolling past Healthy items.
2. **Registrar name in the RDAP `Unknown` reason** — when RDAP succeeds but returns no expiration event, currently shown as generic "lookup unavailable"; surface the raw `rdap_registrar` if one was parsed, so a genuinely-unusual RDAP response is more diagnosable at a glance.
3. **CSV export of `list`** — a `--csv path.csv` flag on `list`, matching the terminal/JSON/CSV output pattern several prior builds (Ledger Lens, TrialScope) already established, for pasting into a spreadsheet or sharing.
4. **`remove-domain` / `edit-renewal` commands** — currently a domain or a manual renewal, once added, can only be completed or left as-is; a typo in a domain name or a renewal's due date has no correction path short of editing the SQLite file directly.

## Medium Effort (roughly one nightly build session)

5. **Certificate Authority (CA) and Subject Alternative Name (SAN) capture** — the live TLS handshake already retrieves the full peer certificate; today only `notAfter` is used. Storing the issuer and SAN list would let the dashboard flag a cert that's about to be replaced by a different CA (a real signal of an infrastructure change worth knowing about) or one missing a SAN the user expects.
6. **DNSSEC/DNS-health check alongside RDAP+TLS** — a third live, no-auth, no-credential check (a direct DNS query for the domain's NS/SOA records, or an HTTP HEAD to confirm the site actually resolves and responds) would round out "is this domain healthy" beyond just registration and cert expiration.
7. **Recurring `sync` via a Claude Code Routine** — package a Routine definition that runs `sync` + `render` on a weekly schedule and only surfaces a notification when something crosses into Due This Week or Overdue, turning this from a pull tool the user has to remember to run into a genuine pull-to-attention system, per CLAUDE.md's Routine/Skill/Hook guidance.

## Ambitious Extensions (multi-session effort)

8. **Auto-discovery of domains from The Canada List's own database** — rather than manually `add-domain`-ing each property, a future build could (with explicit, scoped read access) pull the list of domains The Canada List's own data pipeline already tracks and seed Renewal Radar's monitoring list from it automatically, closing the loop between the two projects.
9. **Historical trend alerting** — with enough accumulated `sync` history, detect a certificate that's being renewed later each cycle (shrinking margin over time) as an early-warning signal distinct from a simple "days remaining" threshold, similar in spirit to Waymark's/Impact Ledger's velocity-style analysis over accumulated snapshots.

---

## Possible Integration Points

- **Ingest Gate (2026-08-10)** — both target The Canada List's operational health; a shared "Canada List Infrastructure" view combining Ingest Gate's data-quality checks with Renewal Radar's domain/cert checks would give one place for "is the platform healthy" rather than two separate tools.
- **Waymark (2026-08-07)** — Waymark already mines this repo's own commit history for decision-worthy events; a future integration could log "Renewal Radar caught an expiring cert" as a decision-worthy event in Waymark's ledger, connecting operational monitoring to the project-history record.
- **Deadline Guardian (2026-07-17)** — deliberately kept separate (academic/research deadlines vs. technical/business infrastructure renewals), but both share the same recurrence-math and urgency-bucket shape; a shared library module between the two would reduce duplication if either is revisited.

---

## Known Limitations to Address

| Limitation | Suggested Fix |
|------------|---------------|
| RDAP lookups require the IANA bootstrap fetch to succeed over HTTPS, which this build container's egress proxy blocks (confirmed live — a `403`) | No fix needed for the user's own runtime, where this is a normal outbound HTTPS request; a future build could cache the bootstrap file locally with a documented refresh interval so a transient network blip doesn't block every domain's RDAP check in one `sync` run |
| `every-N-months` recurrence stores `recurrence_n` but the CLI's `add-renewal --recurrence-n` flag isn't validated against `--recurrence every-N-months` until it reaches `db.add_manual_renewal` — a mismatched flag combination produces a database-layer `ValueError` rather than an argparse-level error | Add a manual cross-field check in `cmd_add_renewal` before calling into `db` for a clearer, earlier CLI error message |
| The domain-expiration history chart only has data once `sync` has been run more than once — a single sync produces a single point, which is visually correct but not very informative | No action needed; this is inherent to any real accumulate-over-time chart (the same limitation every prior snapshot-based build in this catalog has on its first run) and resolves itself after a few days of use |
| RDAP registrar-name extraction assumes a `vcardArray` with an `fn` field in the standard position; some registries' RDAP responses omit registrar entity data entirely or structure it differently | Falls back gracefully to `None`/"lookup unavailable" today, which is correct behavior; a future pass could add a second extraction strategy (e.g. checking `publicIds` or a `legalRepresentative` role) for registries that structure this differently |
