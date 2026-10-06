import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path

import helpers
from recurring.cli import main
from recurring.detect import detect
from recurring.forecast import to_ics, upcoming_charges
from recurring.models import Transaction
from recurring.report import render_html

TODAY = date(2026, 6, 10)


def series_for(rows):
    return detect(rows, as_of=TODAY)


class ForecastTests(unittest.TestCase):
    def test_monthly_charge_appears_twice_in_60_days(self):
        found = series_for(helpers.monthly("SPOTIFY", 12.99, start=date(2026, 1, 11), count=5))
        items = upcoming_charges(found, TODAY, 60)
        self.assertEqual([i.date for i in items], [date(2026, 6, 11), date(2026, 7, 11)])

    def test_lapsed_series_not_forecast(self):
        rows = helpers.monthly("OLD", 5.0, start=date(2025, 1, 1), count=5)
        self.assertEqual(upcoming_charges(series_for(rows), TODAY, 60), [])

    def test_window_boundary_inclusive_and_sorted(self):
        rows = helpers.monthly("A", 5.0, start=date(2026, 1, 20), count=5) + helpers.monthly("B", 9.0, start=date(2026, 1, 12), count=5)
        items = upcoming_charges(series_for(rows), TODAY, 9)
        self.assertEqual([i.merchant for i in items], ["B"])
        wide = upcoming_charges(series_for(rows), TODAY, 30)
        self.assertEqual([i.date for i in wide], sorted(i.date for i in wide))


class IcsTests(unittest.TestCase):
    def test_one_event_per_forecast_charge_with_crlf(self):
        found = series_for(helpers.monthly("SPOTIFY", 12.99, start=date(2026, 1, 11), count=5))
        items = upcoming_charges(found, TODAY, 60)
        ics = to_ics(items)
        self.assertEqual(ics.count("BEGIN:VEVENT"), len(items))
        self.assertEqual(ics.count("END:VEVENT"), len(items))
        self.assertTrue(ics.startswith("BEGIN:VCALENDAR\r\n"))
        self.assertIn("DTSTART;VALUE=DATE:20260611", ics)

    def test_commas_in_names_escaped(self):
        found = series_for(helpers.monthly("ACME, INC", 5.0, start=date(2026, 1, 11), count=5))
        self.assertIn("\\,", to_ics(upcoming_charges(found, TODAY, 40)))


class ReportTests(unittest.TestCase):
    def test_report_is_offline_single_file(self):
        found = series_for(helpers.monthly("SPOTIFY", 12.99, start=date(2026, 1, 11), count=5))
        html = render_html(found, upcoming_charges(found, TODAY), TODAY, 6)
        self.assertIn('name="viewport"', html)
        self.assertNotRegex(html, r'(?:src|href)=["\']https?://')
        self.assertNotIn("__DATA__", html)

    def test_hostile_description_cannot_break_out_of_script(self):
        evil = "</script><script>alert(1)</script>"
        rows = helpers.monthly(evil + " SHOP", 9.99, start=date(2026, 1, 11), count=5)
        found = detect(rows, as_of=TODAY)
        html = render_html(found, upcoming_charges(found, TODAY), TODAY, 6)
        self.assertNotIn("</script><script>alert", html)
        self.assertEqual(html.count("<script"), 2)

    def test_embedded_data_round_trips(self):
        found = series_for(helpers.monthly("SPOTIFY", 12.99, start=date(2026, 1, 11), count=5))
        html = render_html(found, [], TODAY, 6)
        blob = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S).group(1)
        self.assertEqual(json.loads(blob)["series"][0]["typical_amount"], 12.99)


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_demo_end_to_end_writes_all_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            html, ics, js = (Path(tmp) / n for n in ("r.html", "r.ics", "r.json"))
            code, out, _ = self.run_cli("--demo", "--out", str(html), "--ics", str(ics), "--json", str(js))
            self.assertEqual(code, 0)
            self.assertIn("recurring charges", out)
            data = json.loads(js.read_text())
            self.assertEqual(ics.read_text().count("BEGIN:VEVENT"), len(data["upcoming"]))
            self.assertTrue(any(s["status"] == "zombie" for s in data["series"]))
            self.assertTrue(html.read_text().startswith("<!doctype html>"))

    def test_real_csv_file_end_to_end(self):
        rows = "Date,Description,Amount\n" + "".join(
            f"2026-0{m}-05,SPOTIFY STOCKHOLM,-12.99\n" for m in range(1, 7)
        )
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "s.csv"
            csv_path.write_text(rows)
            code, out, _ = self.run_cli(str(csv_path), "--out", str(Path(tmp) / "o.html"), "--today", "2026-06-10")
            self.assertEqual(code, 0)
            self.assertIn("found 1 recurring", out)

    def test_no_input_is_usage_error(self):
        code, _, err = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("--demo", err)

    def test_bad_file_reports_error_not_traceback(self):
        code, _, err = self.run_cli("/no/such.csv")
        self.assertEqual(code, 1)
        self.assertIn("cannot read file", err)

    def test_bad_today_rejected(self):
        code, _, _ = self.run_cli("--demo", "--today", "tomorrow")
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
