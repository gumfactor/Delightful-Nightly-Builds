# WL-20260609-001 Adopt a system-scoped work log

## Notes

Created a durable log for changes to the parent nightly-build setup. The scope is intentionally narrower than the repository: it covers selection logic, agent instructions, automation, standards, templates, backlog infrastructure, and repository-wide maintenance.

## Key Points

- Log parent-system changes, not the contents or review of individual nightly builds.
- Dated builds retain their own PRD, rationale, build log, and catalog history.
- When a change spans both levels, record only the system-level mechanism here.

## Details

The Work Log README defines explicit inclusion and exclusion rules. Included examples are CLAUDE.md, STANDARDS.md, SETUP.md, workflow and agent configuration, templates, builds/index.md, builds/ideas.md, and builds/idea-briefs/. Dated folders matching builds/YYYY-MM-DD-title/ are excluded except as linked evidence for a parent-system decision.

## Next Actions

- None.

## Metadata

- Date: 2026-06-09
- Category: Decision
- Status: approved
- Phase: system-governance
- Owner:
- Tags: governance;worklog;nightly-build-system
- Related paths: Work Log/README.md;Work Log/worklog-index.csv
- Related entries:
- Teamwork project:
- Teamwork task:
- Teamwork URL:
