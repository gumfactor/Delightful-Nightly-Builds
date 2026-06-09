# Delightful Nightly Builds System Work Log

This folder is the canonical append-oriented record of meaningful changes to
the **parent nightly-build system**.

## Scope

Log changes to the machinery that selects, governs, runs, documents, or
maintains nightly builds, including:

- root instructions and policy files such as `CLAUDE.md`, `STANDARDS.md`,
  `PROFILE.md`, and `SETUP.md`;
- automation and agent configuration under `.github/`, `.claude/`, or
  `.agents/`;
- shared templates;
- `builds/index.md`, `builds/ideas.md`, and `builds/idea-briefs/`;
- repository-wide maintenance that changes how the system operates.

Do **not** create entries for the implementation, extension, rating, or review
of individual nightly builds under dated folders such as
`builds/YYYY-MM-DD-title/`. Those builds already carry their own `PRD.md`,
`WhyThis.md`, `BUILD_LOG.md`, and catalog entry.

If one change affects both the parent system and a dated build, record only the
system-level decision or mechanism here and link to the dated build as
evidence.

## Structure

- `worklog-index.csv`: filterable entry registry
- `records/YYYY/`: one Markdown record per entry
- `templates/worklog-template.md`: entry template

Add entries instead of rewriting history. Use categories, statuses, phases,
tags, related paths, and related entries for retrieval.
