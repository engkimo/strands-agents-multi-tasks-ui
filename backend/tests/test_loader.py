import unittest

from app.config.loader import recommend_tools, build_tool_options


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.cfg = {
            "tools": {
                "claude_code": {"stdin": True, "limits": {"timeout_seconds": 90}},
                "codex_cli": {"stdin": False, "arg_template": "--prompt {text}", "limits": {"timeout_seconds": 60}},
            },
            "selectors": [
                {"name": "ideation", "keywords": ["ideas", "アイデア"], "recommend": ["claude_code"]}
            ],
            "default": {"recommend": ["codex_cli", "claude_code"]},
        }

    def test_recommend_by_keyword(self):
        tools, sel = recommend_tools("Give me 3 ideas", self.cfg)
        self.assertEqual(tools, ["claude_code"])  # ideation wins
        self.assertEqual(sel, "ideation")

    def test_recommend_default(self):
        tools, sel = recommend_tools("unknown task", self.cfg)
        self.assertEqual(tools, ["codex_cli", "claude_code"])  # default list
        self.assertIsNone(sel)

    def test_build_tool_options(self):
        opts = build_tool_options("say hello", ["claude_code", "codex_cli"], self.cfg)
        # claude_code uses stdin
        self.assertTrue(opts["claude_code"]["use_stdin"])  # True
        # codex_cli uses args and template applied
        self.assertFalse(opts["codex_cli"]["use_stdin"])  # False
        self.assertIn("--prompt", opts["codex_cli"]["override_args"])  # arg present
        self.assertIn("hello", " ".join(opts["codex_cli"]["override_args"]))


if __name__ == "__main__":
    unittest.main()

