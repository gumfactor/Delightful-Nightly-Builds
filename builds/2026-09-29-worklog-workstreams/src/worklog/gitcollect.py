"""Local Git collector: commits, branch membership, tags and working-tree state."""
import re
from typing import Optional

from .ledger import make_event, utc_now
from .project import Project, git, refs_from_branch, refs_from_text

RS, US = "\x1e", "\x1f"
LOG_FORMAT = f"{RS}%H{US}%an{US}%aI{US}%P{US}%s{US}%b{US}"
AGENT_TRAILER = re.compile(r"(?im)^co-authored-by:\s*(claude|codex|copilot|cursor|aider|gemini)\b")
GENERATED_BY = re.compile(r"(?i)generated with \[?(claude code|codex|copilot)")


def _agent_of(body: str) -> Optional[str]:
    match = AGENT_TRAILER.search(body) or GENERATED_BY.search(body)
    return match.group(1).lower().replace(" code", "") if match else None


def default_ref(project: Project) -> Optional[str]:
    """Ref used as the 'mainline' when deciding which commits live on side branches."""
    for candidate in (project.default_branch, f"origin/{project.default_branch}"):
        if git(project.root, "rev-parse", "--verify", "--quiet", candidate, check=False).strip():
            return candidate
    return None


def branch_membership(project: Project) -> dict[str, set[str]]:
    """Map commit sha -> non-default branches that carry it (via `default..branch`)."""
    base = default_ref(project)
    names = git(project.root, "for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes").split()
    membership: dict[str, set[str]] = {}
    for name in names:
        short = name.split("/", 1)[1] if name.startswith("origin/") else name
        if name in ("origin", "origin/HEAD") or short in (project.default_branch, "HEAD"):
            continue
        if project.config.branch_excluded(short):
            continue
        rev_range = [f"{base}..{name}"] if base else [name]
        shas = git(project.root, "rev-list", f"--max-count={project.config.max_commits}", *rev_range,
                   check=False).split()
        for sha in shas:
            membership.setdefault(sha, set()).add(short)
    return membership


def collect_commits(project: Project, since: Optional[str] = None) -> list[dict]:
    args = ["log", "--all", "--no-renames", "--numstat", f"--max-count={project.config.max_commits}",
            f"--pretty=format:{LOG_FORMAT}"]
    if since:
        args.append(f"--since={since}")
    output = git(project.root, *args, check=False)
    membership = branch_membership(project)
    events = []
    for chunk in output.split(RS):
        if not chunk.strip():
            continue
        fields = chunk.split(US, 6)
        if len(fields) < 7:
            continue
        sha, author, date, parents, subject, body, numstat = fields
        files, insertions, deletions = [], 0, 0
        for line in numstat.strip().splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            ins, dele, path = parts
            if project.config.path_excluded(path):
                continue
            files.append(path)
            insertions += int(ins) if ins.isdigit() else 0
            deletions += int(dele) if dele.isdigit() else 0
        branches = sorted(membership.get(sha, set()))
        keys = [f"sha:{sha}", *refs_from_text(subject), *refs_from_text(body)]
        for branch in branches:
            keys.append(f"branch:{branch}")
            keys.extend(refs_from_branch(branch))
        agent = _agent_of(body)
        events.append(make_event(
            ts=date, project_id=project.project_id, etype="commit", provider="git", ref=sha, summary=subject,
            actor_kind="agent" if agent else "human", actor_name=agent or author, status="completed",
            keys=keys, files=files,
            metadata={"parents": parents.split(), "insertions": insertions, "deletions": deletions,
                      "files_changed": len(files), "branches": branches, "reproduce": f"git show {sha}"}))
    return events


def collect_tags(project: Project) -> list[dict]:
    fmt = "%(refname:short)%09%(objectname)%09%(*objectname)%09%(creatordate:iso-strict)"
    events = []
    for line in git(project.root, "for-each-ref", f"--format={fmt}", "refs/tags", check=False).splitlines():
        parts = line.split("\t")
        if len(parts) != 4 or not parts[3]:
            continue
        name, obj, peeled, date = parts
        events.append(make_event(ts=date, project_id=project.project_id, etype="tag", provider="git",
                                 ref=name, summary=f"Tag {name}", keys=[f"sha:{peeled or obj}"],
                                 metadata={"reproduce": f"git show {name}"}))
    return events


def working_state(project: Project) -> dict:
    """Current observation of the checkout (not an event: it changes every minute)."""
    root = project.root
    head = git(root, "rev-parse", "--verify", "--quiet", "HEAD", check=False).strip() or None
    branch = git(root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False).strip() or None
    dirty, untracked = [], []
    entries = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all", check=False).split("\0")
    skip_next = False
    for entry in entries:
        if skip_next:
            skip_next = False
            continue
        if len(entry) < 4:
            continue
        code, path = entry[:2], entry[3:]
        if code[0] in "RC":
            skip_next = True
        if project.config.path_excluded(path):
            continue
        (untracked if code == "??" else dirty).append(path)
    fmt = "%(refname:short)%09%(objectname)%09%(upstream:short)%09%(upstream:track)"
    branches = {}
    for line in git(root, "for-each-ref", f"--format={fmt}", "refs/heads", check=False).splitlines():
        name, sha, upstream, track = (line.split("\t") + ["", "", "", ""])[:4]
        if not project.config.branch_excluded(name):
            branches[name] = {"sha": sha, "upstream": upstream or None, "track": track or None}
    return {"head": head, "branch": branch, "dirty": sorted(dirty), "untracked": sorted(untracked),
            "branches": branches, "default_branch": project.default_branch, "remote": project.remote,
            "captured_at": utc_now()}


def collect(project: Project, since: Optional[str] = None) -> tuple[list[dict], dict]:
    return collect_commits(project, since) + collect_tags(project), working_state(project)
