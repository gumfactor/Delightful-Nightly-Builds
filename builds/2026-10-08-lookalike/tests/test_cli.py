import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

from tests import helpers  # noqa: F401
from lookalike import cli, demo


def run(argv):
    buffer = io.StringIO()
    code = cli.main(argv, out=buffer)
    return code, buffer.getvalue()


class CliEndToEndTests(unittest.TestCase):
    def test_demo_produces_expected_clusters_and_keeps_chain_apart(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, text = run(["demo", "--out", tmp])
            self.assertEqual(code, 0)
            report = json.loads((Path(tmp) / "merge_report.json").read_text(encoding="utf-8"))
            members = sorted(sorted(c["members"]) for c in report["clusters"])
            self.assertEqual(members, [["1", "2"], ["4", "5"]])
            self.assertEqual(len(report["branch_pairs"]), 3)
            self.assertEqual(report["summary"]["output_rows"], 12)
            self.assertTrue((Path(tmp) / "review.html").exists())
            self.assertIn("14 rows in -> 12 rows out", text)

    def test_decisions_file_changes_outcome_on_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "in.csv"
            source.write_text(demo.sample_csv(), encoding="utf-8")
            decisions = Path(tmp) / "decisions.json"
            decisions.write_text(json.dumps({"same": [["1", "3"]], "different": [["4", "5"]]}), encoding="utf-8")
            code, _ = run(["scan", str(source), "--out", str(Path(tmp) / "o"), "--decisions", str(decisions)])
            self.assertEqual(code, 0)
            report = json.loads((Path(tmp) / "o" / "merge_report.json").read_text(encoding="utf-8"))
            members = sorted(sorted(c["members"]) for c in report["clusters"])
            self.assertEqual(members, [["1", "2", "3"]])

    def test_existing_directory_match_flags_batch_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp) / "existing.csv"
            existing.write_text("id,name,phone,website\n900,Acme Widgets Ltd,416-555-0100,acme.ca\n", encoding="utf-8")
            batch = Path(tmp) / "batch.csv"
            batch.write_text("name,phone,website\nAcme Widgets,(416) 555-0100,https://www.acme.ca\n", encoding="utf-8")
            code, _ = run(["scan", str(batch), "--existing", str(existing), "--out", str(Path(tmp) / "o")])
            self.assertEqual(code, 0)
            with (Path(tmp) / "o" / "clusters.csv").open(encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual({r["row_id"] for r in rows}, {"existing:900", "1"})

    def test_ai_flag_without_key_degrades_with_warning(self):
        import os
        saved = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / "in.csv"
                source.write_text(demo.sample_csv(), encoding="utf-8")
                code, text = run(["scan", str(source), "--out", str(Path(tmp) / "o"), "--ai"])
            self.assertEqual(code, 0)
            self.assertIn("ANTHROPIC_API_KEY is not set", text)
        finally:
            if saved is not None:
                os.environ["ANTHROPIC_API_KEY"] = saved

    def test_pipeline_with_stub_ai_embeds_verdicts_in_report(self):
        responses = {"content": [{"type": "text", "text": '{"verdict": "same", "reason": "shared phone"}'}]}
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "in.csv"
            source.write_text(demo.sample_csv(), encoding="utf-8")
            buffer = io.StringIO()
            cli.run_pipeline(source, Path(tmp) / "o", use_ai=True, transport=lambda payload: responses, out=buffer)
            report = json.loads((Path(tmp) / "o" / "merge_report.json").read_text(encoding="utf-8"))
            self.assertTrue(all(p["ai"]["verdict"] == "same" for p in report["review_pairs"]))
            self.assertIn("AI suggestion", (Path(tmp) / "o" / "review.html").read_text(encoding="utf-8"))

    def test_bad_inputs_return_error_code(self):
        self.assertEqual(run(["scan", "/nonexistent.csv"])[0], 2)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "in.csv"
            source.write_text(demo.sample_csv(), encoding="utf-8")
            bad = Path(tmp) / "d.json"
            bad.write_text("{not json", encoding="utf-8")
            self.assertEqual(run(["scan", str(source), "--decisions", str(bad), "--out", tmp])[0], 2)


if __name__ == "__main__":
    unittest.main()
