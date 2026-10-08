import tempfile
import unittest
from pathlib import Path

from tests import helpers  # noqa: F401
from lookalike import schema


class SchemaTests(unittest.TestCase):
    def test_header_aliases_and_extra_columns(self):
        records, _h, _w = schema.parse_records("Business Name,URL,Tel,Notes2\nAcme Ltd,acme.ca,416-555-0100,keep me\n")
        self.assertEqual(records[0].fields["name"], "Acme Ltd")
        self.assertEqual(records[0].domain, "acme.ca")
        self.assertEqual(records[0].phone, "4165550100")
        self.assertEqual(records[0].extra, {"Notes2": "keep me"})

    def test_missing_name_column_is_an_error(self):
        with self.assertRaises(schema.IntakeError):
            schema.parse_records("url,phone\nacme.ca,416-555-0100\n")

    def test_empty_file_is_an_error(self):
        with self.assertRaises(schema.IntakeError):
            schema.parse_records("")

    def test_bom_crlf_quoted_newline(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "in.csv"
            path.write_bytes('﻿id,name,description\r\n7,"Acme, Inc.","line1\nline2"\r\n'.encode("utf-8"))
            records, _h, _w = schema.read_records(path)
        self.assertEqual(records[0].id, "7")
        self.assertEqual(records[0].fields["name"], "Acme, Inc.")
        self.assertIn("line2", records[0].fields["description"])

    def test_cp1252_file_decodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "in.csv"
            path.write_bytes("name\nBoulangerie Dubé\n".encode("cp1252"))
            records, _h, _w = schema.read_records(path)
        self.assertEqual(records[0].fields["name"], "Boulangerie Dubé")

    def test_blank_rows_skipped_nameless_row_warned_duplicate_ids_renumbered(self):
        text = "id,name,phone\n1,A Co,\n,,\n2,,416-555-0100\n1,B Co,\n"
        records, _h, warnings = schema.parse_records(text)
        self.assertEqual(len(records), 2)
        self.assertEqual(len({r.id for r in records}), 2)
        self.assertTrue(any("no business name" in w for w in warnings))
        self.assertTrue(any("duplicate id" in w for w in warnings))

    def test_missing_file_is_intake_error(self):
        with self.assertRaises(schema.IntakeError):
            schema.read_records(Path("/nonexistent/file.csv"))


if __name__ == "__main__":
    unittest.main()
