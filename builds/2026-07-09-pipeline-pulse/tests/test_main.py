from datetime import date
from pathlib import Path

import git_inspector
import main as main_module

FIXTURE = str(Path(__file__).parent.parent / "sample_index.md")


def test_build_dashboard_end_to_end_with_fixture(monkeypatch, tmp_path):
    """Full pipeline: catalog parsing -> git reconciliation -> stats -> HTML,
    with git_inspector's repo-facing calls stubbed out (no real subprocess)."""
    monkeypatch.setattr(git_inspector, "detect_default_branch", lambda cwd, runner=None: "main")
    monkeypatch.setattr(git_inspector, "detect_owner_repo", lambda cwd, runner=None: ("acme", "widgets"))
    monkeypatch.setattr(
        git_inspector,
        "list_build_folders_at_ref",
        lambda cwd, ref, runner=None: {"2026-06-06-sample-one", "2026-06-07-sample-two"},
    )
    monkeypatch.setattr(git_inspector, "list_remote_branches", lambda cwd, default, runner=None: ["origin/claude/x"])
    monkeypatch.setattr(
        git_inspector,
        "build_folder_branch_map",
        lambda cwd, default, branches, runner=None: {"2026-06-08-sample-three": "origin/claude/x"},
    )
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    html, summary = main_module.build_dashboard(
        repo_path=str(tmp_path),
        index_path=FIXTURE,
        owner=None,
        repo=None,
        use_ai=False,
        today=date(2026, 7, 9),
    )

    assert summary["total"] == 3
    assert summary["merged_count"] == 2
    # Sample Three is "discarded" in the fixture, so it's excluded from backlog
    # (never expected to merge), leaving zero actionable backlog.
    assert summary["backlog_count"] == 0
    assert "acme/widgets" in html
    assert "Sample One" in html


def test_main_cli_writes_output_file(monkeypatch, tmp_path):
    monkeypatch.setattr(git_inspector, "find_repo_root", lambda start, runner=None: str(tmp_path))
    monkeypatch.setattr(git_inspector, "detect_default_branch", lambda cwd, runner=None: "main")
    monkeypatch.setattr(git_inspector, "detect_owner_repo", lambda cwd, runner=None: None)
    monkeypatch.setattr(git_inspector, "list_build_folders_at_ref", lambda cwd, ref, runner=None: set())
    monkeypatch.setattr(git_inspector, "list_remote_branches", lambda cwd, default, runner=None: [])
    monkeypatch.setattr(git_inspector, "build_folder_branch_map", lambda cwd, default, branches, runner=None: {})
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    output_path = tmp_path / "out" / "dashboard.html"
    exit_code = main_module.main(
        ["--repo-path", str(tmp_path), "--index-path", FIXTURE, "--output", str(output_path), "--no-ai"]
    )

    assert exit_code == 0
    assert output_path.is_file()
    assert "Pipeline Pulse" in output_path.read_text(encoding="utf-8")


def test_main_cli_returns_error_code_for_missing_index(monkeypatch, tmp_path):
    monkeypatch.setattr(git_inspector, "find_repo_root", lambda start, runner=None: str(tmp_path))
    exit_code = main_module.main(
        ["--repo-path", str(tmp_path), "--index-path", "/nonexistent/index.md", "--no-ai"]
    )
    assert exit_code == 1
