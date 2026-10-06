import tempfile
import unittest
from datetime import date
from pathlib import Path

import helpers  # noqa: F401
from recurring.models import Transaction
from recurring.parsers import ParseError, dedupe, parse_amount, parse_date, parse_file, parse_text

RBC = (
    "Account Type,Account Number,Transaction Date,Cheque Number,Description 1,Description 2,CAD$,USD$\n"
    'Visa,4500123412341234,1/15/2026,,NETFLIX.COM,866-579-7172,-23.99,\n'
    'Visa,4500123412341234,1/16/2026,,PAYMENT THANK YOU,,500.00,\n'
)
TD = "01/15/2026,SPOTIFY STOCKHOLM,12.99,,1500.00\n01/20/2026,PAYROLL DEPOSIT,,2000.00,3500.00\n"
CIBC = "2026-01-15,GITHUB SAN FRANCISCO CA,5.45,,4500********1234\n"
SCOTIA = "Date,Amount,Type,Description\n2026-01-15,-85.00,Debit,ROGERS WIRELESS\n2026-01-16,1200.00,Credit,PAYROLL\n"
BMO_PREAMBLE = (
    "Following data is valid as of 2026-02-01\n\n"
    "Transaction Date,Description,Amount\n20260115,GOODLIFE FITNESS,-14.97\n"
)
DEBIT_CREDIT = "Date,Description,Debit,Credit,Balance\n2026-01-15,TORONTO HYDRO,92.10,,100\n2026-01-16,REFUND,,20.00,120\n"


class ParseValueTests(unittest.TestCase):
    def test_amount_formats(self):
        self.assertEqual(parse_amount("$1,234.50"), 1234.5)
        self.assertEqual(parse_amount("(12.00)"), -12.0)
        self.assertEqual(parse_amount("12.00-"), -12.0)
        self.assertEqual(parse_amount("12.00CR"), -12.0)
        self.assertIsNone(parse_amount("abc"))
        self.assertIsNone(parse_amount(""))

    def test_date_formats(self):
        self.assertEqual(parse_date("2026-01-15"), date(2026, 1, 15))
        self.assertEqual(parse_date("1/15/2026"), date(2026, 1, 15))
        self.assertEqual(parse_date("20260115"), date(2026, 1, 15))
        self.assertIsNone(parse_date("not a date"))


class ParseBankTests(unittest.TestCase):
    def test_rbc_signed_amounts_keep_only_purchases(self):
        txns = parse_text(RBC)
        self.assertEqual(len(txns), 1)
        self.assertEqual(txns[0].amount, 23.99)
        self.assertIn("NETFLIX.COM", txns[0].description)

    def test_td_headerless_ignores_deposits(self):
        txns = parse_text(TD)
        self.assertEqual([t.amount for t in txns], [12.99])
        self.assertEqual(txns[0].date, date(2026, 1, 15))

    def test_cibc_iso_headerless(self):
        self.assertEqual(parse_text(CIBC)[0].amount, 5.45)

    def test_scotiabank_header_signed(self):
        txns = parse_text(SCOTIA)
        self.assertEqual([t.amount for t in txns], [85.0])

    def test_bmo_preamble_and_compact_dates(self):
        txns = parse_text(BMO_PREAMBLE)
        self.assertEqual(txns[0].date, date(2026, 1, 15))
        self.assertEqual(txns[0].amount, 14.97)

    def test_debit_credit_columns(self):
        txns = parse_text(DEBIT_CREDIT)
        self.assertEqual([t.amount for t in txns], [92.10])

    def test_bom_and_semicolon_ok(self):
        txns = parse_text("﻿Date;Description;Amount\n2026-01-15;ROGERS;-85.00\n")
        self.assertEqual(len(txns), 1)


class ParseErrorTests(unittest.TestCase):
    def test_empty_file(self):
        with self.assertRaises(ParseError):
            parse_text("   \n")

    def test_unrecognised_columns_explains_expected_format(self):
        with self.assertRaises(ParseError) as ctx:
            parse_text("foo,bar\n1,2\n")
        self.assertIn("Expected columns", str(ctx.exception))

    def test_missing_file(self):
        with self.assertRaises(ParseError):
            parse_file("/nonexistent/statement.csv")

    def test_latin1_file_decodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s.csv"
            path.write_bytes("Date,Description,Amount\n2026-01-15,CAF\xc9 NERO,-4.50\n".encode("latin-1"))
            self.assertEqual(len(parse_file(path)), 1)


class DedupeTests(unittest.TestCase):
    def test_overlapping_exports_deduplicated_across_files(self):
        a = Transaction(date(2026, 1, 1), "X", 5.0, "a.csv")
        b = Transaction(date(2026, 1, 1), "X", 5.0, "b.csv")
        self.assertEqual(dedupe([a, b]), [a])

    def test_same_day_repeat_inside_one_file_is_kept(self):
        a = Transaction(date(2026, 1, 1), "X", 5.0, "a.csv")
        self.assertEqual(len(dedupe([a, a])), 2)


if __name__ == "__main__":
    unittest.main()
