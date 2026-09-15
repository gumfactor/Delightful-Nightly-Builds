import os

import pytest

from src import cli


def _fake_fetch(tickers, period="9mo"):
    n = 40
    return {
        ticker: [
            ("2026-01-%02d" % (i + 1) if i < 31 else "2026-02-%02d" % (i - 30), 100.0 + (0.3 * i if ticker == tickers[1] else 0.0))
            for i in range(n)
        ]
        for ticker in tickers
    }


def _fake_ai(snapshots, transitions):
    return "mocked commentary"


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_build_arg_parser_defaults():
    parser = cli.build_arg_parser()
    args = parser.parse_args([])
    assert args.benchmark == "SPY"
    assert args.sectors is None
    assert args.period == "9mo"
    assert args.ratio_window == 10
    assert args.momentum_window == 10
    assert args.tail_length == 10
    assert args.no_ai is False
    assert args.output == "rotation_radar.html"


def test_build_arg_parser_overrides():
    parser = cli.build_arg_parser()
    args = parser.parse_args(["--benchmark", "QQQ", "--sectors", "XLK", "XLF", "--no-ai"])
    assert args.benchmark == "QQQ"
    assert args.sectors == ["XLK", "XLF"]
    assert args.no_ai is True


def test_run_end_to_end_writes_html_and_db(workdir):
    parser = cli.build_arg_parser()
    args = parser.parse_args(["--sectors", "XLK", "XLF", "--output", "out.html", "--db-path", "test.db"])

    result = cli.run(args, fetch_fn=_fake_fetch, ai_fn=_fake_ai)

    assert os.path.exists(result["html_path"])
    assert os.path.exists(result["db_path"])
    assert os.path.exists(result["csv_path"])
    assert set(result["snapshots"].keys()) == {"XLK", "XLF"}
    assert result["commentary"] == "mocked commentary"

    with open(result["html_path"], encoding="utf-8") as f:
        html_text = f.read()
    assert "XLK" in html_text and "XLF" in html_text


def test_run_no_ai_flag_skips_ai_function(workdir):
    parser = cli.build_arg_parser()
    args = parser.parse_args(["--sectors", "XLK", "XLF", "--no-ai", "--output", "out.html", "--db-path", "test.db"])

    def fail_if_called(snapshots, transitions):
        raise AssertionError("ai_fn should not be called when --no-ai is set")

    result = cli.run(args, fetch_fn=_fake_fetch, ai_fn=fail_if_called)
    assert "first recorded run" in result["commentary"] or "Leading" in result["commentary"] or "Improving" in result["commentary"]


def test_run_second_invocation_detects_quadrant_history(workdir):
    parser = cli.build_arg_parser()
    args = parser.parse_args(["--sectors", "XLK", "XLF", "--output", "out.html", "--db-path", "test.db"])

    first = cli.run(args, fetch_fn=_fake_fetch, ai_fn=_fake_ai)
    second = cli.run(args, fetch_fn=_fake_fetch, ai_fn=_fake_ai)

    assert first["run_id"] != second["run_id"]
    # Same input data both times -> quadrants should be identical -> no transitions changed.
    assert all(not t.changed for t in second["transitions"])


def test_main_returns_zero_on_success(workdir, monkeypatch):
    monkeypatch.setattr(cli, "run", lambda args: {
        "run_id": 1, "html_path": "out.html", "csv_path": "out_history.csv", "db_path": "d.db",
        "snapshots": {"XLK": object()}, "transitions": [], "commentary": "ok",
    })
    exit_code = cli.main(["--output", "out.html"])
    assert exit_code == 0


def test_main_returns_one_on_failure(workdir, monkeypatch):
    def raise_error(args):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli, "run", raise_error)
    exit_code = cli.main([])
    assert exit_code == 1
