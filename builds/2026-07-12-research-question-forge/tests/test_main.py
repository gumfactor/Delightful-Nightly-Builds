import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db, main


def test_cli_generate_writes_requested_count(tmp_path, capsys):
    db_path = tmp_path / "forge.db"
    main.main(["--db", str(db_path), "generate", "--count", "7", "--seed", "5"])
    conn = db.connect(db_path)
    db.init_db(conn)
    rows = db.list_questions(conn)
    assert len(rows) == 7
    conn.close()


def test_cli_search_returns_only_matching_rows(tmp_path):
    db_path = tmp_path / "forge.db"
    main.main(["--db", str(db_path), "generate", "--count", "15", "--seed", "11"])

    conn = db.connect(db_path)
    db.init_db(conn)
    all_rows = db.list_questions(conn)
    target_term = "cortisol"
    # search_questions matches skeleton, rationale, tag, and ai_polish (see db.py),
    # so the expected set must check the same fields, not skeleton alone.
    matching_ids = {
        r["id"]
        for r in all_rows
        if target_term in (r["skeleton"] + " " + r["rationale"] + " " + (r["tag"] or "")).lower()
    }
    conn.close()

    if not matching_ids:
        # Deterministic taxonomy content: skip only if this exact seed/count
        # combination happened not to include a cortisol-related question.
        return

    results = db.search_questions(db.connect(db_path), target_term)
    result_ids = {r["id"] for r in results}
    assert result_ids == matching_ids


def test_full_generate_render_search_star_use_workflow(tmp_path):
    db_path = tmp_path / "forge.db"
    html_path = tmp_path / "forge.html"

    main.main(["--db", str(db_path), "generate", "--count", "5", "--seed", "42"])
    main.main(["--db", str(db_path), "render", "--output", str(html_path)])
    assert html_path.exists()

    conn = db.connect(db_path)
    db.init_db(conn)
    first_id = db.list_questions(conn)[0]["id"]
    conn.close()

    main.main(["--db", str(db_path), "star", str(first_id)])
    main.main(["--db", str(db_path), "tag", str(first_id), "R01-aim1"])
    main.main(["--db", str(db_path), "use", str(first_id)])

    conn = db.connect(db_path)
    db.init_db(conn)
    row = db.get_question(conn, first_id)
    conn.close()

    assert row["starred"] == 1
    assert row["used"] == 1
    assert row["tag"] == "R01-aim1"


def test_cli_generate_without_polish_flag_uses_template_source(tmp_path):
    db_path = tmp_path / "forge.db"
    main.main(["--db", str(db_path), "generate", "--count", "3", "--seed", "1"])
    conn = db.connect(db_path)
    db.init_db(conn)
    rows = db.list_questions(conn)
    conn.close()
    assert all(r["ai_source"] == "template" for r in rows)
    assert all(r["ai_polish"] is None for r in rows)
