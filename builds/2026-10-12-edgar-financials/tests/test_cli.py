import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from edgar_fin.cli import run

from helpers import DEMO_COMPANIES, FakeSec, no_sleep

ENV = {"EDGAR_USER_AGENT": "Test Suite test@example.com"}


def invoke(argv, **kwargs):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.dict(os.environ, ENV, clear=True):
        code = run(argv, sleep=no_sleep, out=out, err=err, **kwargs)
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def test_end_to_end_writes_all_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = FakeSec(DEMO_COMPANIES)
            code, out, _ = invoke(["nwnd", "FBRK", "--out", tmp], fetch=fake)
            names = {p.name for p in Path(tmp).iterdir()}
        self.assertEqual(code, 0)
        self.assertTrue({"report.html", "financials_long.csv", "summary.csv",
                         "NWND_financials.csv", "FBRK_financials.csv"} <= names)
        self.assertIn("report.html", out)

    def test_second_run_uses_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = FakeSec(DEMO_COMPANIES)
            invoke(["NWND", "--out", tmp], fetch=fake)
            calls = len(fake.requests)
            invoke(["NWND", "--out", tmp], fetch=fake)
        self.assertEqual(len(fake.requests), calls)

    def test_bad_ticker_is_reported_but_others_succeed(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = invoke(["NWND", "ZZZZ", "--out", tmp], fetch=FakeSec(DEMO_COMPANIES))
            html_text = (Path(tmp) / "report.html").read_text()
        self.assertEqual(code, 3)
        self.assertIn("Unknown ticker 'ZZZZ'", err)
        self.assertIn("Unknown ticker", html_text)

    def test_all_bad_tickers_exits_nonzero_without_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, _ = invoke(["ZZZZ", "--out", tmp], fetch=FakeSec(DEMO_COMPANIES))
            self.assertFalse((Path(tmp) / "report.html").exists())
        self.assertEqual(code, 1)

    def test_no_tickers_is_usage_error(self):
        code, _, err = invoke([])
        self.assertEqual(code, 2)
        self.assertIn("at least one ticker", err)

    def test_missing_user_agent_is_reported(self):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {}, clear=True):
            code = run(["NWND"], out=out, err=err)
        self.assertEqual(code, 2)
        self.assertIn("EDGAR_USER_AGENT", err.getvalue())

    def test_years_out_of_range(self):
        code, _, _ = invoke(["NWND", "--years", "0"])
        self.assertEqual(code, 2)

    def test_demo_mode_needs_no_network_or_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.dict(os.environ, {}, clear=True):
                code = run(["--demo", "--out", tmp], out=out, err=err)
            page = (Path(tmp) / "report.html").read_text()
        self.assertEqual(code, 0)
        self.assertIn("synthetic", page)

    def test_ai_flag_without_key_degrades_to_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = invoke(["NWND", "--ai", "--out", tmp], fetch=FakeSec(DEMO_COMPANIES))
            page = (Path(tmp) / "report.html").read_text()
        self.assertEqual(code, 0)
        self.assertIn("ANTHROPIC_API_KEY", err)
        self.assertIn("ANTHROPIC_API_KEY", page)

    def test_ai_flag_with_key_embeds_commentary(self):
        transport = mock.Mock(return_value={"content": [{"type": "text", "text": "Northwind leads."}]})
        with tempfile.TemporaryDirectory() as tmp:
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.dict(os.environ, {**ENV, "ANTHROPIC_API_KEY": "k"}, clear=True):
                code = run(["NWND", "--ai", "--out", tmp], fetch=FakeSec(DEMO_COMPANIES),
                           ai_transport=transport, sleep=no_sleep, out=out, err=err)
            page = (Path(tmp) / "report.html").read_text()
        self.assertEqual(code, 0)
        self.assertIn("Northwind leads.", page)


if __name__ == "__main__":
    unittest.main()
