from __future__ import annotations

import os
import asyncio
from ..models import ToolName, NodeResult
from .runner import run_external_tool
from .demo import simulate_tool


async def run_tool(
    tool: ToolName,
    prompt: str,
    timeout_seconds: int = 120,
    on_log: callable | None = None,
    options: dict | None = None,
) -> NodeResult:
    if os.getenv("DEMO_MODE", "0") not in ("0", "false", "False"):
        return await simulate_tool(tool, prompt, on_log=on_log)
    opts = options or {}
    retries = int(opts.get("retries", 0) or 0)
    delay = 0.5
    last: NodeResult | None = None
    for attempt in range(retries + 1):
        last = await run_external_tool(
            tool,
            prompt,
            timeout_seconds=opts.get("timeout_seconds", timeout_seconds),
            on_log=on_log,
            override_args=opts.get("override_args"),
            override_use_stdin=opts.get("use_stdin"),
            max_output_bytes=opts.get("max_output_bytes"),
            deny=opts.get("deny"),
            env=opts.get("env"),
            cwd=opts.get("cwd"),
        )
        if last.ok:
            break
        if attempt < retries:
            try:
                await asyncio.sleep(delay)
            except Exception:
                pass
            delay = min(delay * 2, 3.0)
    return last
