import json
import os
import urllib.error
from unittest.mock import patch

import pytest

import main
from conftest import FIXTURES_DIR

VALID_CSV = os.path.join(FIXTURES_DIR, "businesses_valid.csv")


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "maple_press.db")


def test_generate_piece_gift_guide_full_pipeline(db_path):
    piece = main.generate_piece(
        csv_path=VALID_CSV,
        piece_type="gift_guide",
        tone="consumer",
        category="Skincare",
        db_path=db_path,
    )
    assert piece["piece_type"] == "gift_guide"
    assert len(piece["businesses"]) == 3
    body_text = piece["body_markdown"]
    assert "Northern Bloom Skincare" in body_text
    assert "Birchwood Skin Co" in body_text
    assert "Maple Grove Botanicals" in body_text
    # The foreign-verdict business in the same category is excluded by default.
    assert "GlobalGlow Cosmetics" not in body_text


def test_generate_piece_spotlight_requires_business_arg(db_path):
    with pytest.raises(ValueError, match="requires --business"):
        main.generate_piece(csv_path=VALID_CSV, piece_type="spotlight", tone="consumer", db_path=db_path)


def test_generate_piece_gift_guide_requires_category_arg(db_path):
    with pytest.raises(ValueError, match="requires --category"):
        main.generate_piece(csv_path=VALID_CSV, piece_type="gift_guide", tone="consumer", db_path=db_path)


def test_generate_piece_local_spotlight_requires_province_arg(db_path):
    with pytest.raises(ValueError, match="requires --province"):
        main.generate_piece(csv_path=VALID_CSV, piece_type="local_spotlight", tone="consumer", db_path=db_path)


def test_generate_piece_insufficient_businesses_raises(db_path):
    # Coffee has only 2 canadian-verdict businesses — not enough for gift_guide (needs 3).
    with pytest.raises(ValueError, match="at least 3"):
        main.generate_piece(
            csv_path=VALID_CSV, piece_type="gift_guide", tone="consumer",
            category="Coffee", db_path=db_path,
        )


def test_generate_piece_social_tone_rejected_for_swap_it(db_path):
    with pytest.raises(ValueError, match="not valid"):
        main.generate_piece(
            csv_path=VALID_CSV, piece_type="swap_it", tone="social",
            category="Coffee", db_path=db_path,
        )


def test_generate_piece_include_unverified_unlocks_home_goods_swap_it(db_path):
    # Home Goods has 1 canadian + 1 uncertain business — needs --include-unverified
    # to reach swap_it's minimum of 2.
    with pytest.raises(ValueError, match="at least 2"):
        main.generate_piece(
            csv_path=VALID_CSV, piece_type="swap_it", tone="consumer",
            category="Home Goods", db_path=db_path,
        )

    piece = main.generate_piece(
        csv_path=VALID_CSV, piece_type="swap_it", tone="consumer",
        category="Home Goods", include_unverified=True, db_path=db_path,
    )
    assert len(piece["businesses"]) == 2
    assert "Unverified" in piece["body_markdown"]


def test_generate_piece_novelty_changes_headline_on_repeat(db_path):
    first = main.generate_piece(
        csv_path=VALID_CSV, piece_type="swap_it", tone="consumer",
        category="Coffee", db_path=db_path,
    )
    second = main.generate_piece(
        csv_path=VALID_CSV, piece_type="swap_it", tone="consumer",
        category="Coffee", db_path=db_path,
    )
    assert first["headline"] != second["headline"]
    assert first["id"] != second["id"]


def test_generate_piece_ai_polish_no_key_zero_network_calls(db_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with patch("ai_polish.urllib.request.urlopen") as mock_urlopen:
        piece = main.generate_piece(
            csv_path=VALID_CSV, piece_type="spotlight", tone="consumer",
            business="Prairie Wool Co", ai_polish=True, db_path=db_path,
        )
    mock_urlopen.assert_not_called()
    assert piece["ai_polished"] is False
    assert "Prairie Wool Co" in piece["body_markdown"]


def test_cli_generate_json_output(db_path, capsys):
    exit_code = main.main([
        "generate", "--csv", VALID_CSV, "--type", "spotlight",
        "--tone", "consumer", "--business", "Prairie Wool Co",
        "--json", "--db", db_path,
    ])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["businesses"][0]["name"] == "Prairie Wool Co"


def test_cli_generate_invalid_business_reports_error(db_path, capsys):
    exit_code = main.main([
        "generate", "--csv", VALID_CSV, "--type", "spotlight",
        "--tone", "consumer", "--business", "Nonexistent Co", "--db", db_path,
    ])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Error" in captured.err


def test_cli_list_and_show_roundtrip(db_path, capsys):
    main.main([
        "generate", "--csv", VALID_CSV, "--type", "spotlight",
        "--tone", "consumer", "--business", "Prairie Wool Co", "--db", db_path,
    ])
    capsys.readouterr()

    exit_code = main.main(["list", "--db", db_path])
    assert exit_code == 0
    listed = capsys.readouterr().out
    assert "Prairie Wool Co" in listed or "#1" in listed

    exit_code = main.main(["show", "1", "--db", db_path])
    assert exit_code == 0
    shown = capsys.readouterr().out
    assert "Prairie Wool Co" in shown


def test_cli_export_markdown_writes_file(db_path, tmp_path):
    main.main([
        "generate", "--csv", VALID_CSV, "--type", "spotlight",
        "--tone", "consumer", "--business", "Prairie Wool Co", "--db", db_path,
    ])
    out_path = tmp_path / "piece.md"
    exit_code = main.main(["export", "1", "--format", "markdown", "--out", str(out_path), "--db", db_path])
    assert exit_code == 0
    content = out_path.read_text(encoding="utf-8")
    assert content.startswith("# ")
    assert "Prairie Wool Co" in content


def test_cli_render_writes_html_file(db_path, tmp_path):
    main.main([
        "generate", "--csv", VALID_CSV, "--type", "gift_guide",
        "--tone", "consumer", "--category", "Skincare", "--db", db_path,
    ])
    out_path = tmp_path / "library.html"
    exit_code = main.main(["render", "--out", str(out_path), "--db", db_path])
    assert exit_code == 0
    content = out_path.read_text(encoding="utf-8")
    assert content.startswith("<!doctype html>")
    assert "Northern Bloom Skincare" in content
