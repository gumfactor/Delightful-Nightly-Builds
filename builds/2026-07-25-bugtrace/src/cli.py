"""argparse CLI wiring for BugTrace."""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import classify, fix_detector, github_client, local_git, report_html, report_text, store
from .ai_classify import classify_batch


def _months_ago_iso(months):
    now = datetime.now(timezone.utc)
    approx_days = int(months * 30.4375)
    return (now - timedelta(days=approx_days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _collect_targets(args):
    targets = []
    if args.repo_path:
        for p in args.repo_path.split(","):
            p = p.strip()
            if p:
                targets.append(("local", p))
    if args.repos:
        for r in args.repos.split(","):
            r = r.strip()
            if r:
                targets.append(("github", r))
    if args.all:
        token = args.token or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise SystemExit("--all requires GITHUB_TOKEN to be set in the environment.")
        for full_name in github_client.list_user_repos(token):
            targets.append(("github", full_name))
    return targets


def _gather_local(target, since_iso, limit):
    since_arg = None
    if since_iso:
        since_arg = since_iso.split("T")[0]
    commits = local_git.get_local_fix_commits(target, since=since_arg, limit=limit)
    gathered = []
    for c in commits:
        if not fix_detector.is_fix_commit(c["message"]):
            continue
        diff = local_git.get_local_commit_diff(target, c["sha"])
        gathered.append(
            {
                "repo": target,
                "sha": c["sha"],
                "message": c["message"],
                "date": c["date"],
                "raw_diff": diff,
                "changed_files": [],
            }
        )
    return gathered


def _gather_github(target, token, since_iso, limit):
    commits = github_client.list_fix_candidate_commits(token, target, since_iso=since_iso, limit=limit)
    gathered = []
    for c in commits:
        message = c.get("commit", {}).get("message", "")
        if not fix_detector.is_fix_commit(message):
            continue
        sha = c["sha"]
        detail = github_client.get_commit_detail(token, target, sha)
        files = detail.get("files", []) or []
        diff = "\n".join(f.get("patch", "") for f in files if f.get("patch"))
        changed_files = [f.get("filename", "") for f in files]
        date = c.get("commit", {}).get("author", {}).get("date", "")
        gathered.append(
            {
                "repo": target,
                "sha": sha,
                "message": message,
                "date": date,
                "raw_diff": diff,
                "changed_files": changed_files,
            }
        )
    return gathered


def cmd_sync(args):
    from .redact import redact_secrets

    conn = store.init_db(args.db)
    since_iso = _months_ago_iso(args.since_months) if args.since_months else None
    targets = _collect_targets(args)
    if not targets:
        raise SystemExit("No sync targets specified. Use --repo-path, --repos, or --all.")

    token = args.token or os.environ.get("GITHUB_TOKEN")
    new_fix_commits = []

    for kind, target in targets:
        try:
            if kind == "local":
                gathered = _gather_local(target, since_iso, args.limit_per_repo)
            else:
                if not token:
                    print(f"Skipping {target}: GITHUB_TOKEN not set.", file=sys.stderr)
                    continue
                gathered = _gather_github(target, token, since_iso, args.limit_per_repo)
        except (local_git.LocalGitError, github_client.GitHubAPIError) as exc:
            print(f"Skipping {target}: {exc}", file=sys.stderr)
            continue

        for item in gathered:
            if store.is_known(conn, item["repo"], item["sha"]):
                continue
            item["diff_excerpt"] = redact_secrets(item["raw_diff"])[:4000]
            new_fix_commits.append(item)

    if args.ai:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        batch = new_fix_commits[: args.ai_limit]
        rest = new_fix_commits[args.ai_limit :]
        ai_input = [
            {"sha": c["sha"], "message": c["message"], "diff_excerpt": c["diff_excerpt"], "changed_files": c["changed_files"]}
            for c in batch
        ]
        ai_results = classify_batch(api_key, ai_input)
        for c in batch:
            r = ai_results[c["sha"]]
            store.upsert_fix(
                conn, c["repo"], c["sha"], c["message"], c["date"], r["category"], r["source"], r["explanation"], c["diff_excerpt"]
            )
        for c in rest:
            category, explanation = classify.keyword_classify(c["message"], c["diff_excerpt"], c["changed_files"])
            store.upsert_fix(conn, c["repo"], c["sha"], c["message"], c["date"], category, "keyword", explanation, c["diff_excerpt"])
    else:
        for c in new_fix_commits:
            category, explanation = classify.keyword_classify(c["message"], c["diff_excerpt"], c["changed_files"])
            store.upsert_fix(conn, c["repo"], c["sha"], c["message"], c["date"], category, "keyword", explanation, c["diff_excerpt"])

    print(f"Synced {len(new_fix_commits)} new fix commit(s) across {len(targets)} target(s).")


def cmd_report(args):
    conn = store.init_db(args.db)
    if args.format == "text":
        print(report_text.render_text(conn))
        return

    if args.format == "json":
        data = {
            "counts": store.category_counts(conn),
            "monthly": store.monthly_counts(conn),
            "repos": store.repo_counts(conn),
            "fixes": store.get_all_fixes(conn),
        }
        payload = json.dumps(data, indent=2)
        if args.out and args.out != "-":
            Path(args.out).write_text(payload)
            print(f"Wrote {args.out}")
        else:
            print(payload)
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY") if args.ai else None
    html = report_html.render_html(conn, ai_api_key=api_key)
    Path(args.out).write_text(html)
    print(f"Wrote {args.out}")


def cmd_show(args):
    conn = store.init_db(args.db)
    fixes = [f for f in store.get_all_fixes(conn) if f["category"] == args.category]
    if not fixes:
        print(f"No fix commits found for category '{args.category}'.")
        return
    for f in fixes:
        first_line = f["message"].splitlines()[0] if f["message"] else ""
        print(f"{f['sha'][:8]}  {f['repo']:<30} {f['author_date'][:10]}  {first_line}")


def build_parser():
    parser = argparse.ArgumentParser(prog="bugtrace", description="Mine your own bug-fix commit history for recurring patterns.")
    sub = parser.add_subparsers(dest="command", required=True)

    sync_p = sub.add_parser("sync", help="Fetch and classify new fix commits.")
    sync_p.add_argument("--repo-path", help="Comma-separated local git repo path(s); no token required.")
    sync_p.add_argument("--repos", help="Comma-separated owner/repo GitHub targets.")
    sync_p.add_argument("--all", action="store_true", help="Fetch all repos owned by the GITHUB_TOKEN user.")
    sync_p.add_argument("--token", help="GitHub token override (defaults to GITHUB_TOKEN env var).")
    sync_p.add_argument("--since-months", type=float, default=12, help="Only consider commits from the last N months.")
    sync_p.add_argument("--limit-per-repo", type=int, default=500, help="Max commits to scan per repo.")
    sync_p.add_argument("--ai", action="store_true", help="Use Claude Haiku for classification (falls back to keyword rules).")
    sync_p.add_argument("--ai-limit", type=int, default=40, help="Max new commits to send to the AI classifier per run.")
    sync_p.add_argument("--db", default="bugtrace.db", help="SQLite database path.")
    sync_p.set_defaults(func=cmd_sync)

    report_p = sub.add_parser("report", help="Render the accumulated fix-commit report.")
    report_p.add_argument("--db", default="bugtrace.db", help="SQLite database path.")
    report_p.add_argument("--out", default="bugtrace_report.html", help="Output file path (or '-' for stdout with --format json).")
    report_p.add_argument("--format", choices=["html", "json", "text"], default="html")
    report_p.add_argument("--ai", action="store_true", help="Use Claude Haiku to write the coaching paragraph (HTML only).")
    report_p.set_defaults(func=cmd_report)

    show_p = sub.add_parser("show", help="List fix commits for a single category.")
    show_p.add_argument("category", choices=classify.TAXONOMY)
    show_p.add_argument("--db", default="bugtrace.db", help="SQLite database path.")
    show_p.set_defaults(func=cmd_show)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
