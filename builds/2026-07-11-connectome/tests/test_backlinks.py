import os
import subprocess
import tempfile

import backlinks
import linking


def test_format_block_uses_filename_stem_with_title_alias():
    block = backlinks.format_block([("note-a.md", "Note A Title", ["workflow", "context"])])
    assert "[[note-a|Note A Title]]" in block
    assert "shared: workflow, context" in block
    assert block.startswith(backlinks.BLOCK_START)
    assert block.endswith(backlinks.BLOCK_END)


def test_format_block_omits_alias_when_title_matches_stem():
    block = backlinks.format_block([("plain.md", "plain", [])])
    assert "[[plain]]" in block
    assert "|" not in block.split("\n")[-2]


def test_find_block_locates_existing_delimiters():
    body = f"intro\n\n{backlinks.BLOCK_START}\nstuff\n{backlinks.BLOCK_END}\n\noutro"
    found = backlinks.find_block(body)
    assert found is not None
    start, end = found
    assert body[start:start + len(backlinks.BLOCK_START)] == backlinks.BLOCK_START
    assert body[end - len(backlinks.BLOCK_END):end] == backlinks.BLOCK_END


def test_find_block_returns_none_when_absent():
    assert backlinks.find_block("just some note text") is None


def test_apply_block_appends_to_body_with_no_trailing_newline():
    body = "# My Note\nsome content"
    block = "<!-- connectome:links:start -->\nlinks\n<!-- connectome:links:end -->"
    result = backlinks.apply_block(body, block)
    assert result == "# My Note\nsome content\n\n" + block + "\n"


def test_apply_block_inserts_into_empty_body():
    result = backlinks.apply_block("", "BLOCK")
    assert result == "BLOCK\n"


def test_apply_block_replaces_existing_block_leaving_rest_untouched():
    old_block = f"{backlinks.BLOCK_START}\nold links\n{backlinks.BLOCK_END}"
    body = f"# Title\n\nmy actual content\n\n{old_block}\n"
    new_block = f"{backlinks.BLOCK_START}\nnew links\n{backlinks.BLOCK_END}"
    result = backlinks.apply_block(body, new_block)
    assert "my actual content" in result
    assert "old links" not in result
    assert "new links" in result


def test_apply_block_is_idempotent_on_repeated_runs():
    body = "# Title\n\ncontent"
    block = f"{backlinks.BLOCK_START}\nlinks\n{backlinks.BLOCK_END}"
    once = backlinks.apply_block(body, block)
    twice = backlinks.apply_block(once, block)
    assert once == twice


def test_apply_block_removes_block_when_no_longer_related_to_anything():
    old_block = f"{backlinks.BLOCK_START}\nsome links\n{backlinks.BLOCK_END}"
    body = f"# Title\n\ncontent\n\n{old_block}\n"
    result = backlinks.apply_block(body, None)
    assert backlinks.BLOCK_START not in result
    assert "content" in result


def test_apply_block_removing_absent_block_is_a_no_op():
    body = "# Title\n\ncontent\n"
    assert backlinks.apply_block(body, None) == body


def test_plan_backlinks_marks_unrelated_note_unchanged():
    notes = [
        {"id": 1, "path": "a.md", "title": "A", "body": "alone"},
        {"id": 2, "path": "b.md", "title": "B", "body": "also alone"},
    ]
    plans = backlinks.plan_backlinks(notes, all_links=[], top_n=5)
    assert all(plan["changed"] is False for plan in plans)


def test_plan_backlinks_inserts_block_for_related_notes():
    notes = [
        {"id": 1, "path": "a.md", "title": "A", "body": "content about workflows"},
        {"id": 2, "path": "b.md", "title": "B", "body": "content about workflows too"},
    ]
    links = [linking.Link(1, 2, 0.5, ["workflow"])]
    plans = backlinks.plan_backlinks(notes, links, top_n=5)
    plan_a = next(p for p in plans if p["path"] == "a.md")
    assert plan_a["changed"] is True
    assert "[[b|B]]" in plan_a["new_body"]


def test_plan_backlinks_second_pass_on_already_written_body_is_a_no_op():
    notes = [
        {"id": 1, "path": "a.md", "title": "A", "body": "content about workflows"},
        {"id": 2, "path": "b.md", "title": "B", "body": "content about workflows too"},
    ]
    links = [linking.Link(1, 2, 0.5, ["workflow"])]
    first_pass = backlinks.plan_backlinks(notes, links, top_n=5)
    updated_notes = [
        {**note, "body": next(p["new_body"] for p in first_pass if p["path"] == note["path"])}
        for note in notes
    ]
    second_pass = backlinks.plan_backlinks(updated_notes, links, top_n=5)
    assert all(plan["changed"] is False for plan in second_pass)


def test_diff_text_reports_no_change_message_when_bodies_are_equal():
    assert "no textual change" in backlinks.diff_text("a.md", "same", "same")


def test_diff_text_produces_unified_diff_headers():
    text = backlinks.diff_text("a.md", "old\n", "new\n")
    assert "a/a.md" in text
    assert "b/a.md" in text


def test_is_git_repo_true_inside_initialized_repo():
    with tempfile.TemporaryDirectory() as tmp_dir:
        subprocess.run(["git", "init", "-q", tmp_dir], check=True)
        assert backlinks.is_git_repo(tmp_dir) is True


def test_is_git_repo_false_for_plain_directory():
    with tempfile.TemporaryDirectory() as tmp_dir:
        assert backlinks.is_git_repo(tmp_dir) is False


def test_is_git_repo_false_for_nonexistent_path():
    assert backlinks.is_git_repo("/no/such/path/at/all") is False


def _git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_git_baseline_problem_flags_non_git_directory():
    with tempfile.TemporaryDirectory() as tmp_dir:
        assert backlinks.git_baseline_problem(tmp_dir) is not None


def test_git_baseline_problem_flags_repo_with_no_commits():
    with tempfile.TemporaryDirectory() as tmp_dir:
        _git("init", "-q", tmp_dir, cwd=tmp_dir)
        problem = backlinks.git_baseline_problem(tmp_dir)
        assert problem is not None
        assert "no commits" in problem


def test_git_baseline_problem_flags_dirty_working_tree():
    with tempfile.TemporaryDirectory() as tmp_dir:
        _git("init", "-q", ".", cwd=tmp_dir)
        with open(os.path.join(tmp_dir, "a.md"), "w", encoding="utf-8") as f:
            f.write("committed content")
        _git("add", "-A", cwd=tmp_dir)
        _git("-c", "user.email=t@example.com", "-c", "user.name=T", "commit", "-q", "-m", "init", cwd=tmp_dir)
        with open(os.path.join(tmp_dir, "a.md"), "a", encoding="utf-8") as f:
            f.write("\nuncommitted change")
        problem = backlinks.git_baseline_problem(tmp_dir)
        assert problem is not None
        assert "uncommitted" in problem


def test_git_baseline_problem_none_for_clean_committed_repo():
    with tempfile.TemporaryDirectory() as tmp_dir:
        _git("init", "-q", ".", cwd=tmp_dir)
        with open(os.path.join(tmp_dir, "a.md"), "w", encoding="utf-8") as f:
            f.write("committed content")
        _git("add", "-A", cwd=tmp_dir)
        _git("-c", "user.email=t@example.com", "-c", "user.name=T", "commit", "-q", "-m", "init", cwd=tmp_dir)
        assert backlinks.git_baseline_problem(tmp_dir) is None


def test_write_plans_writes_only_changed_plans():
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "a.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("original")
        plan = {"path": "a.md", "old_body": "original", "new_body": "updated"}
        written, stale = backlinks.write_plans(tmp_dir, [plan])
        assert written == ["a.md"]
        assert stale == []
        with open(path, encoding="utf-8") as f:
            assert f.read() == "updated"


def test_write_plans_skips_note_that_changed_on_disk_since_indexing():
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "a.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("edited by the user after indexing")
        plan = {"path": "a.md", "old_body": "stale indexed content", "new_body": "would overwrite"}
        written, stale = backlinks.write_plans(tmp_dir, [plan])
        assert written == []
        assert stale == ["a.md"]
        with open(path, encoding="utf-8") as f:
            assert f.read() == "edited by the user after indexing"
