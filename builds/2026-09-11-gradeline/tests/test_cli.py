import json
import os

import pytest

from src import ai, cli, rubric as rubric_mod


@pytest.fixture
def rubric_path(tmp_path):
    path = tmp_path / "rubric.json"
    rubric_mod.write_starter_rubric(str(path))
    return str(path)


@pytest.fixture
def submissions_dir(tmp_path):
    folder = tmp_path / "subs"
    folder.mkdir()
    compliant_text = (
        "Introduction\n"
        "This is my thesis: chronic stress recalibrates the stress response. I argue this "
        "because the evidence is compelling.\n"
        "Discussion\n"
        "A study (Smith, 2019) found supporting evidence. Further research (Jones, 2020) "
        "found more evidence, and this finding was replicated.\n"
        "Conclusion\n"
        "This claim is supported by the study evidence discussed above and above and above.\n"
    )
    (folder / "alice.txt").write_text(compliant_text)
    (folder / "bob.txt").write_text(compliant_text)  # near-identical -> should trigger similarity
    (folder / "carol.txt").write_text("Introduction\nToo short, no citations, missing sections.\n")
    return str(folder)


def test_init_rubric_writes_valid_json(tmp_path):
    path = str(tmp_path / "r.json")
    exit_code = cli.main(["init-rubric", path])
    assert exit_code == 0
    rubric = rubric_mod.load_rubric(path)
    assert rubric.name


def test_grade_batch_creates_batch_and_flags_noncompliant(rubric_path, submissions_dir, tmp_path):
    db_path = str(tmp_path / "g.db")
    batch_id = cli.grade_batch(submissions_dir, rubric_path, db_path)
    assert batch_id == 1

    from src import storage

    conn = storage.connect(db_path)
    rows = storage.get_submissions(conn, batch_id)
    by_id = {r["identifier"]: r for r in rows}
    assert set(by_id) == {"alice", "bob", "carol"}
    carol_compliance = json.loads(by_id["carol"]["compliance_json"])
    assert carol_compliance["sections_ok"] is False
    assert carol_compliance["citations_ok"] is False
    alice_compliance = json.loads(by_id["alice"]["compliance_json"])
    assert alice_compliance["sections_ok"] is True
    conn.close()


def test_grade_batch_detects_similarity_pair(rubric_path, submissions_dir, tmp_path):
    db_path = str(tmp_path / "g.db")
    batch_id = cli.grade_batch(submissions_dir, rubric_path, db_path, threshold=0.75)

    from src import storage

    conn = storage.connect(db_path)
    pairs = storage.get_similarity_pairs(conn, batch_id)
    identifiers_flagged = set()
    id_to_name = {r["id"]: r["identifier"] for r in storage.get_submissions(conn, batch_id)}
    for p in pairs:
        identifiers_flagged.add(id_to_name[p["submission_a_id"]])
        identifiers_flagged.add(id_to_name[p["submission_b_id"]])
    assert identifiers_flagged == {"alice", "bob"}
    conn.close()


def test_grade_command_makes_zero_network_calls_without_api_key(
    rubric_path, submissions_dir, tmp_path, monkeypatch
):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def exploding_transport(url, payload):
        raise AssertionError("should never be called with no API key")

    db_path = str(tmp_path / "g.db")
    # use_ai True but no key present anywhere -> deterministic fallback path only
    batch_id = cli.grade_batch(
        submissions_dir, rubric_path, db_path, use_ai=True, transport=exploding_transport
    )
    assert batch_id == 1


def test_grade_command_with_ai_uses_transport_and_never_leaks_identifier(
    rubric_path, submissions_dir, tmp_path
):
    seen_payloads = []

    def fake_transport(url, payload):
        seen_payloads.append(payload)
        return json.dumps({"content": [{"text": "Grounded feedback paragraph."}]}).encode("utf-8")

    db_path = str(tmp_path / "g.db")
    cli.grade_batch(
        submissions_dir, rubric_path, db_path, use_ai=True, api_key="sk-fake", transport=fake_transport
    )
    assert len(seen_payloads) > 0
    for payload in seen_payloads:
        payload_str = json.dumps(payload)
        assert "alice" not in payload_str
        assert "bob" not in payload_str
        assert "carol" not in payload_str


def test_invalid_rubric_returns_error_exit_code(tmp_path, submissions_dir):
    bad_rubric = tmp_path / "bad.json"
    bad_rubric.write_text(json.dumps({"name": "Bad"}))
    db_path = str(tmp_path / "g.db")
    exit_code = cli.main(["grade", submissions_dir, "--rubric", str(bad_rubric), "--db", db_path])
    assert exit_code == 1


def test_list_command_shows_graded_batch(rubric_path, submissions_dir, tmp_path, capsys):
    db_path = str(tmp_path / "g.db")
    cli.grade_batch(submissions_dir, rubric_path, db_path)
    exit_code = cli.main(["list", "--db", db_path])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "#1" in out


def test_show_command_prints_summary(rubric_path, submissions_dir, tmp_path, capsys):
    db_path = str(tmp_path / "g.db")
    batch_id = cli.grade_batch(submissions_dir, rubric_path, db_path)
    exit_code = cli.main(["show", str(batch_id), "--db", db_path])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Submissions: 3" in out


def test_show_command_missing_batch_returns_error(tmp_path, rubric_path, submissions_dir, capsys):
    db_path = str(tmp_path / "g.db")
    cli.grade_batch(submissions_dir, rubric_path, db_path)
    exit_code = cli.main(["show", "999", "--db", db_path])
    assert exit_code == 1


def test_render_command_produces_html_file(rubric_path, submissions_dir, tmp_path):
    db_path = str(tmp_path / "g.db")
    batch_id = cli.grade_batch(submissions_dir, rubric_path, db_path)
    out_path = str(tmp_path / "report.html")
    exit_code = cli.main(["render", str(batch_id), "--db", db_path, "--out", out_path])
    assert exit_code == 0
    assert os.path.isfile(out_path)
    with open(out_path, encoding="utf-8") as f:
        html = f.read()
    assert "<!DOCTYPE html>" in html
    assert "alice" in html


def test_compare_command_prints_both_batches(rubric_path, submissions_dir, tmp_path, capsys):
    db_path = str(tmp_path / "g.db")
    batch_1 = cli.grade_batch(submissions_dir, rubric_path, db_path)
    batch_2 = cli.grade_batch(submissions_dir, rubric_path, db_path)
    exit_code = cli.main(["compare", str(batch_1), str(batch_2), "--db", db_path])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert f"batch #{batch_1}" in out
    assert f"#{batch_2}" in out


def test_grade_json_output_flag(rubric_path, submissions_dir, tmp_path, capsys):
    db_path = str(tmp_path / "g.db")
    exit_code = cli.main(["grade", submissions_dir, "--rubric", rubric_path, "--db", db_path, "--json"])
    out = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(out)
    assert len(parsed["submissions"]) == 3


def test_regrading_same_folder_creates_second_batch(rubric_path, submissions_dir, tmp_path):
    db_path = str(tmp_path / "g.db")
    batch_1 = cli.grade_batch(submissions_dir, rubric_path, db_path)
    batch_2 = cli.grade_batch(submissions_dir, rubric_path, db_path)
    assert batch_2 == batch_1 + 1
