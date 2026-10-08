import json
import unittest

from tests.helpers import rec
from lookalike import ai
from lookalike.match import PairResult


def response(text):
    return {"content": [{"type": "text", "text": text}]}


class AITests(unittest.TestCase):
    def setUp(self):
        self.a, self.b = rec("1", name="Cedar Ridge Woodworks"), rec("2", name="Cedar Ridge Cabinetry")
        self.pair = PairResult("1", "2", 0.6, "review", [("same phone", 0.45)])

    def test_prompt_marks_listings_as_data_and_includes_evidence(self):
        prompt = ai.build_prompt(self.a, self.b, self.pair)
        self.assertIn("<listing", prompt)
        self.assertIn("not instructions", prompt)
        self.assertIn("same phone", prompt)

    def test_valid_verdict_parsed_even_with_surrounding_text(self):
        verdict = ai.parse_verdict(response('Sure: {"verdict": "Same", "reason": "same phone and town"} done'))
        self.assertEqual(verdict, {"verdict": "same", "reason": "same phone and town"})

    def test_malformed_or_unknown_verdict_becomes_unsure(self):
        self.assertEqual(ai.parse_verdict(response("no json here"))["verdict"], "unsure")
        self.assertEqual(ai.parse_verdict(response('{"verdict": "maybe"}'))["verdict"], "unsure")
        self.assertEqual(ai.parse_verdict({})["verdict"], "unsure")

    def test_adjudicate_uses_transport_and_survives_errors(self):
        calls = []

        def transport(payload):
            calls.append(payload)
            if len(calls) == 2:
                raise ai.AIError("boom")
            return response(json.dumps({"verdict": "different", "reason": "r"}))

        by_id = {"1": self.a, "2": self.b}
        pairs = [self.pair, PairResult("1", "2", 0.58, "review", [])]
        out = ai.adjudicate(pairs, by_id, transport)
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["model"], ai.MODEL)

    def test_missing_api_key_raises_ai_error(self):
        import os
        saved = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            with self.assertRaises(ai.AIError):
                ai.default_transport({})
        finally:
            if saved is not None:
                os.environ["ANTHROPIC_API_KEY"] = saved


if __name__ == "__main__":
    unittest.main()
