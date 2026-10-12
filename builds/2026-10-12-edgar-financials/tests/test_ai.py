import os
import unittest
from unittest import mock

from edgar_fin import ai
from edgar_fin.extract import extract_company

from helpers import DEMO_COMPANIES


def companies():
    return [extract_company(s["payload"], t, s["cik"], 5) for t, s in DEMO_COMPANIES.items()]


class AiTests(unittest.TestCase):
    def test_prompt_contains_figures_for_each_company(self):
        prompt = ai.build_prompt(companies())
        for ticker in DEMO_COMPANIES:
            self.assertIn(ticker, prompt)
        self.assertIn("revenue CAGR 12.0%", prompt)
        self.assertIn("do not invent numbers", prompt)

    def test_missing_key_raises_without_calling_transport(self):
        transport = mock.Mock()
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ai.AiError, "ANTHROPIC_API_KEY"):
                ai.commentary(companies(), transport=transport)
        transport.assert_not_called()

    def test_successful_call_sends_key_and_returns_text(self):
        transport = mock.Mock(return_value={"content": [{"type": "text", "text": "Fine."}]})
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "k-test"}, clear=True):
            text = ai.commentary(companies(), transport=transport)
        self.assertEqual(text, "Fine.")
        _, headers, body = transport.call_args.args
        self.assertEqual(headers["x-api-key"], "k-test")
        self.assertEqual(body["messages"][0]["role"], "user")

    def test_empty_reply_is_an_error(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "k"}, clear=True):
            with self.assertRaises(ai.AiError):
                ai.commentary(companies(), transport=lambda *a: {"content": []})

    def test_money_formatting(self):
        self.assertEqual(ai._money(2.5e9), "$2.50B")
        self.assertEqual(ai._money(None), "n/a")


if __name__ == "__main__":
    unittest.main()
