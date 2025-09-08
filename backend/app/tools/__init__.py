from __future__ import annotations

import os
from ..models import ToolName, NodeResult
from .runner import run_external_tool
from .demo import simulate_tool


async def run_tool(
    tool: ToolName,
    prompt: str,
    timeout_seconds: int = 120,
    on_log: callable | None = None,
) -> NodeResult:
    if os.getenv("DEMO_MODE", "0") not in ("0", "false", "False"):
        return await simulate_tool(tool, prompt, on_log=on_log)
    return await run_external_tool(tool, prompt, timeout_seconds=timeout_seconds, on_log=on_log)
