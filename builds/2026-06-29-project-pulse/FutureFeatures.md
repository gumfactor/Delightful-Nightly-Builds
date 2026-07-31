# Future Features — Project Pulse

## 1. Weekly Digest Email

Generate a plain-text or HTML email summarizing the past week across all active projects — commit counts, new notes, staleness changes — and deliver it via SMTP or Mailgun. Would turn the dashboard into a push notification instead of a pull one, making stale projects impossible to miss.

## 2. Slack / Webhook Notifications for Stale Projects

Add a `notify` command that fires a webhook (Slack, Discord, ntfy) when any project crosses a staleness threshold (e.g. crosses from yellow to orange). Configurable per-project. Lets the tool act as an accountability system rather than a passive dashboard.

## 3. Arora Export / Claude Code Skill Integration

Package the `brief` command as a Claude Code skill (`.claude/skills/project-brief.md`) that injects the project context brief directly into the Claude session so it surfaces in the system prompt. Would make switching projects in Claude Code seamless — the AI already knows where you left off.

## 4. Multi-Source Activity: Pull Requests, Issues, and Releases

Extend GitHub sync beyond commits to include: PR opened/merged/closed, issues filed/closed, and new releases. Each maps to a `source="github"` activity with a different `event_type`. PRs and issues provide higher-signal context than individual commits and matter more for lab/research projects with collaborators.

## 5. Recurring Reminder Tasks

Add a `remind` command: `remind SLUG "Submit ethics application" --every 7d`. Stores recurring reminders in the database, injects them as activity entries on their due dates, and marks them orange/red in the dashboard when overdue. Bridges the gap between passive tracking and active task management.

## 6. Project Archiving and Re-activation Workflow

Add `archive SLUG` and `reactivate SLUG` commands with prompts that capture a closing note (archive) or resumption note (reactivate). Archives would appear in a separate dashboard section with a collapsed activity log and the AI-generated final brief. Lets the tool manage the full project lifecycle rather than just the active phase.

## 7. Brief History and Progress Comparison

Store generated briefs in the database with timestamps. Add a `history SLUG` command that prints past briefs chronologically so you can see how a project evolved. The AI prompt could be extended to reference the previous brief for a delta-summary: "since your last brief 3 days ago, the main changes are..."
