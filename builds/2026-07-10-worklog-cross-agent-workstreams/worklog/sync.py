"""Orchestrates collection -> ledger write -> correlation for a sync run."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from . import util
from .correlate import CorrelationInput, resolve_workstream
from .git_collector import collect_branches, collect_commits, collect_tags
from .github_collector import collect_github_activity
from .ledger import Event, Ledger
from .project import ProjectState, discover_project


@dataclass
class SyncResult:
    project: ProjectState
    new_commit_events: int = 0
    new_branch_events: int = 0
    new_tag_events: int = 0
    new_github_events: int = 0
    github_skipped_reason: str = ""
    total_new_events: int = 0
    warnings: list = field(default_factory=list)


def default_data_dir(repo_root: str) -> str:
    return os.path.join(repo_root, ".worklog")


def run_sync(repo_path: str, data_dir: str | None = None, use_github: bool = True) -> SyncResult:
    project = discover_project(repo_path)
    resolved_data_dir = data_dir or default_data_dir(project.repo_root)

    with Ledger(resolved_data_dir) as ledger:
        result = SyncResult(project=project)

        # 1. GitHub issues/PRs first, so their workstream anchors exist before commits
        #    that reference them are correlated.
        if use_github and project.github_owner_repo:
            owner, repo = project.github_owner_repo
            gh_result = collect_github_activity(owner, repo)
            if gh_result.skipped:
                result.github_skipped_reason = gh_result.reason
            else:
                for item in gh_result.items:
                    source_ref = f"{item.kind}:{item.number}"
                    event_id = util.event_id(project.project_id, "github", source_ref, f"github_{item.kind}")
                    status = "merged" if item.merged else item.state
                    issue_refs = [n for n in util.extract_issue_refs(item.body) if n != item.number]
                    event = Event(
                        id=event_id,
                        project_id=project.project_id,
                        timestamp=item.updated_at or util.utc_now_iso(),
                        type=f"github_{item.kind}",
                        actor_kind="human",
                        actor_name="github",
                        summary=item.title,
                        status=status,
                        source_provider="github",
                        source_ref=source_ref,
                        source_url=item.url,
                        metadata={"number": item.number, "issue_refs": issue_refs},
                    )
                    inserted = ledger.upsert_event(event)
                    if inserted:
                        result.new_github_events += 1
                        params = CorrelationInput(
                            timestamp=event.timestamp,
                            issue_refs=issue_refs or None,
                            self_anchor_number=item.number if not issue_refs else None,
                            fallback_title=item.title,
                        )
                        workstream_id, correlation = resolve_workstream(ledger, project.project_id, params)
                        ledger.set_event_workstream(event.id, workstream_id, correlation)
        elif use_github and not project.github_owner_repo:
            result.github_skipped_reason = "origin remote is not a GitHub repository; git-only mode"
        elif not use_github:
            result.github_skipped_reason = "GitHub collection disabled for this sync (--no-github)"

        # 2. Commits
        commits = collect_commits(project.repo_root, project.branch)
        for commit in commits:
            event_id = util.event_id(project.project_id, "git", commit.sha, "commit")
            issue_refs = util.extract_issue_refs(commit.subject)
            event = Event(
                id=event_id,
                project_id=project.project_id,
                timestamp=commit.timestamp,
                type="commit",
                actor_kind="human",
                actor_name=commit.author_name,
                summary=commit.subject,
                status="completed",
                source_provider="git",
                source_ref=commit.sha,
                metadata={
                    "branch": commit.branch,
                    "files": commit.files,
                    "author_email": commit.author_email,
                    "issue_refs": issue_refs,
                },
            )
            inserted = ledger.upsert_event(event)
            if inserted:
                result.new_commit_events += 1
                params = CorrelationInput(
                    timestamp=event.timestamp,
                    issue_refs=issue_refs or None,
                    branch=commit.branch,
                    files=commit.files or None,
                    fallback_title=commit.subject,
                )
                workstream_id, correlation = resolve_workstream(ledger, project.project_id, params)
                ledger.set_event_workstream(event.id, workstream_id, correlation)

        # 3. Branches
        for branch_info in collect_branches(project.repo_root):
            source_ref = branch_info.name
            event_id = util.event_id(project.project_id, "git", source_ref, "branch")
            event = Event(
                id=event_id,
                project_id=project.project_id,
                timestamp=util.utc_now_iso(),
                type="branch",
                actor_kind="human",
                actor_name="git",
                summary=f"Branch {branch_info.name}",
                status="active",
                source_provider="git",
                source_ref=source_ref,
                metadata={"upstream": branch_info.upstream, "head_sha": branch_info.head_sha},
            )
            if ledger.upsert_event(event):
                result.new_branch_events += 1

        # 4. Tags
        for tag_info in collect_tags(project.repo_root):
            event_id = util.event_id(project.project_id, "git", tag_info.name, "tag")
            event = Event(
                id=event_id,
                project_id=project.project_id,
                timestamp=util.utc_now_iso(),
                type="tag",
                actor_kind="human",
                actor_name="git",
                summary=f"Tag {tag_info.name}",
                status="completed",
                source_provider="git",
                source_ref=tag_info.name,
                metadata={"sha": tag_info.sha},
            )
            if ledger.upsert_event(event):
                result.new_tag_events += 1

        result.total_new_events = (
            result.new_commit_events
            + result.new_branch_events
            + result.new_tag_events
            + result.new_github_events
        )

        # Record sync state for staleness detection by `resume`.
        ledger.set_state(project.project_id, "last_sync_head", project.head_sha)
        ledger.set_state(project.project_id, "last_sync_branch", project.branch)
        ledger.set_state(project.project_id, "last_sync_at", util.utc_now_iso())
        ledger.set_state(project.project_id, "last_sync_dirty_files", project.dirty_files)
        ledger.set_state(project.project_id, "last_sync_untracked_files", project.untracked_files)

        return result
