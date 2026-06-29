import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure src/ is importable regardless of working directory
sys.path.insert(0, str(Path(__file__).parent))

import database as db
import github_sync as gh
import briefer
import dashboard as dash

_BUILD_ROOT = Path(__file__).parent.parent
DEFAULT_DB = str(_BUILD_ROOT / "data" / "projects.db")
DEFAULT_OUTPUT = str(_BUILD_ROOT / "dashboard.html")

_PROJECT_COLORS = [
    "#4a9eff", "#3fb950", "#d29922", "#f0883e",
    "#a371f7", "#f85149", "#58a6ff", "#56d364",
]


def _pick_color(db_path: str) -> str:
    existing = db.list_projects(db_path, status="all")
    return _PROJECT_COLORS[len(existing) % len(_PROJECT_COLORS)]


def cmd_add(args: argparse.Namespace, db_path: str) -> None:
    db.init_db(db_path)
    repos = args.repos or []
    color = _pick_color(db_path)
    try:
        proj_id = db.add_project(
            db_path=db_path,
            name=args.name,
            description=args.desc or "",
            proj_type=args.type,
            github_repos=repos,
            color=color,
        )
        slug = db.slugify(args.name)
        print(f"Added project '{args.name}' (slug: {slug}, id: {proj_id})")
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args: argparse.Namespace, db_path: str) -> None:
    db.init_db(db_path)
    status = getattr(args, "status", "active")
    projects = db.list_projects(db_path, status=status)
    if not projects:
        print(f"No {status} projects.")
        return
    for p in projects:
        repos_str = ", ".join(p.get("github_repos") or []) or "(no repos)"
        last_at = db.get_last_activity_date(db_path, p["id"])
        last_str = last_at[:10] if last_at else "never"
        print(f"  [{p['id']}] {p['name']} ({p['type']}) — last: {last_str} — {repos_str}")


def cmd_log(args: argparse.Namespace, db_path: str) -> None:
    db.init_db(db_path)
    project = db.get_project(db_path, args.slug)
    if not project:
        print(f"Project '{args.slug}' not found.", file=sys.stderr)
        sys.exit(1)
    result = db.log_activity(
        db_path=db_path,
        project_id=project["id"],
        source="manual",
        event_type="note",
        title=args.note,
    )
    if result is not None:
        print(f"Logged note for '{project['name']}'")
    else:
        print("Note already exists (duplicate — skipped)")


def cmd_sync(args: argparse.Namespace, db_path: str) -> None:
    db.init_db(db_path)
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("GITHUB_TOKEN not set — skipping GitHub sync.", file=sys.stderr)
        sys.exit(1)

    slug = getattr(args, "slug", None)
    if slug:
        project = db.get_project(db_path, slug)
        if not project:
            print(f"Project '{slug}' not found.", file=sys.stderr)
            sys.exit(1)
        projects = [project]
    else:
        projects = db.list_projects(db_path, status="active")

    total = 0
    for p in projects:
        if not p.get("github_repos"):
            print(f"  {p['name']}: no GitHub repos configured, skipping")
            continue
        count = gh.sync_project(db_path, p, token)
        print(f"  {p['name']}: +{count} new commits")
        total += count
    print(f"Sync complete: {total} new activities")


def cmd_brief(args: argparse.Namespace, db_path: str) -> None:
    db.init_db(db_path)
    project = db.get_project(db_path, args.slug)
    if not project:
        print(f"Project '{args.slug}' not found.", file=sys.stderr)
        sys.exit(1)
    activities = db.get_recent_activity(db_path, project["id"], days=30)
    text = briefer.generate_brief(project, activities)
    print(f"\n=== Context Brief: {project['name']} ===\n")
    print(text)
    print()


def cmd_dashboard(args: argparse.Namespace, db_path: str) -> None:
    db.init_db(db_path)
    projects = db.list_projects(db_path, status="active")
    all_activity = db.get_all_recent_activity(db_path, days=30)

    project_activities = {}
    last_activity_map = {}
    for p in projects:
        project_activities[p["slug"]] = db.get_recent_activity(db_path, p["id"], days=30)
        last_activity_map[p["id"]] = db.get_last_activity_date(db_path, p["id"])

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html_content = dash.render_dashboard(
        projects=projects,
        all_activity=all_activity,
        project_activities=project_activities,
        last_activity_map=last_activity_map,
        generated_at=generated_at,
    )

    output_path = getattr(args, "output", None) or DEFAULT_OUTPUT
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Dashboard written to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="project-pulse",
        description="Multi-project context manager — track activity, sync GitHub, generate AI briefs",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a project")
    p_add.add_argument("name", help="Project display name")
    p_add.add_argument("--desc", default="", help="Short description")
    p_add.add_argument(
        "--type", default="code",
        choices=["lab", "code", "writing", "business", "personal"],
        help="Project type (default: code)",
    )
    p_add.add_argument("--repos", nargs="*", default=[], metavar="OWNER/REPO",
                       help="GitHub repos to track")
    p_add.add_argument("--db", default=DEFAULT_DB, help=argparse.SUPPRESS)

    p_list = sub.add_parser("list", help="List projects")
    p_list.add_argument(
        "--status", default="active",
        choices=["active", "paused", "archived", "all"],
        help="Filter by status (default: active)",
    )
    p_list.add_argument("--db", default=DEFAULT_DB, help=argparse.SUPPRESS)

    p_log = sub.add_parser("log", help="Add a manual activity note")
    p_log.add_argument("slug", help="Project slug")
    p_log.add_argument("note", help="Note text")
    p_log.add_argument("--db", default=DEFAULT_DB, help=argparse.SUPPRESS)

    p_sync = sub.add_parser("sync", help="Pull GitHub commits (requires GITHUB_TOKEN)")
    p_sync.add_argument("slug", nargs="?", help="Project slug (omit to sync all active)")
    p_sync.add_argument("--db", default=DEFAULT_DB, help=argparse.SUPPRESS)

    p_brief = sub.add_parser("brief", help="Generate AI context brief (requires ANTHROPIC_API_KEY)")
    p_brief.add_argument("slug", help="Project slug")
    p_brief.add_argument("--db", default=DEFAULT_DB, help=argparse.SUPPRESS)

    p_dash = sub.add_parser("dashboard", help="Generate HTML dashboard")
    p_dash.add_argument("--output", default=None, help="Output path (default: dashboard.html)")
    p_dash.add_argument("--db", default=DEFAULT_DB, help=argparse.SUPPRESS)

    args = parser.parse_args()
    db_path = getattr(args, "db", DEFAULT_DB)

    dispatch = {
        "add": cmd_add,
        "list": cmd_list,
        "log": cmd_log,
        "sync": cmd_sync,
        "brief": cmd_brief,
        "dashboard": cmd_dashboard,
    }
    dispatch[args.command](args, db_path)


if __name__ == "__main__":
    main()
