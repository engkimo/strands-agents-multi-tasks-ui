import unittest
import asyncio

from app.tools.runner import run_external_tool
from app.models import ToolName


class RunnerTests(unittest.IsolatedAsyncioTestCase):
    async def test_deny_blocks_execution(self):
        # Default command resolves to `echo`, so denying 'echo' should block
        res = await run_external_tool(ToolName.claude_code, "hello", deny=["echo"])
        self.assertFalse(res.ok)
        self.assertIn("blocked", res.stderr or "")

    async def test_max_output_truncation(self):
        # Use default echo and cap output to a small number
        res = await run_external_tool(ToolName.codex_cli, "x" * 1000, max_output_bytes=10)
        out = res.stdout or ""
        self.assertIn("[truncated]", out)


if __name__ == "__main__":
    unittest.main()

