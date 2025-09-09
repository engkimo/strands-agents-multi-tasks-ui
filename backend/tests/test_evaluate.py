import unittest

from app.eval.simple import evaluate_text


class EvalTests(unittest.TestCase):
    def test_empty(self):
        m = evaluate_text(None)
        self.assertEqual(m["score"], 0.0)

    def test_basic_metrics(self):
        txt = """# Title\n\nSome text here.\n\n```python\nprint('hi')\n```\n"""
        m = evaluate_text(txt, prompt="print code")
        self.assertGreater(m["lines"], 0)
        self.assertGreater(m["chars"], 0)
        self.assertGreaterEqual(m["code_blocks"], 1)
        self.assertGreaterEqual(m["vocab"], 2)
        self.assertGreater(m["score"], 0)


if __name__ == "__main__":
    unittest.main()

