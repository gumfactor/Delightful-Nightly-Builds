# WL-20260609-002 Add linked idea briefs to the build-selection workflow

## Notes

Added a richer specification path for ambitious backlog ideas whose requirements do not fit safely in one table row.

## Key Points

- builds/ideas.md now has an Idea Brief column.
- Durable planning documents live under builds/idea-briefs/.
- Selected briefs must be read before scope and technology decisions are made.
- Build PRDs must document brief traceability, included capabilities, deferrals, and changed assumptions.

## Details

Created a detailed brief for Cross-Agent Project Activity Workstreams and linked it from backlog idea 4. Updated CLAUDE.md, STANDARDS.md, SETUP.md, and both normal and resume GitHub Actions prompts so the autonomous workflow reads linked briefs and may stage builds/ideas.md when selection changes it. The brief remains an input to, rather than a replacement for, the dated build PRD.

## Next Actions

- [ ] Use the traceability workflow when backlog idea 4 is selected.

## Metadata

- Date: 2026-06-09
- Category: Change
- Status: implemented
- Phase: idea-selection
- Owner:
- Tags: ideas;prd;agent-instructions;nightly-build-system
- Related paths: builds/ideas.md;builds/idea-briefs/README.md;builds/idea-briefs/cross-agent-project-activity-workstreams.md;CLAUDE.md;STANDARDS.md;SETUP.md;.github/workflows/nightly.yml
- Related entries: WL-20260609-001
- Teamwork project:
- Teamwork task:
- Teamwork URL:
