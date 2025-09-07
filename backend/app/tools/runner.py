from __future__ import annotations

import asyncio
import os
import shlex
import time
from typing import List, Optional

from ..models import ToolName, NodeResult


def _env_key(tool: ToolName, suffix: str) -> str:
    up = str(tool).split(".")[-1].upper()
    return f"TOOL_{up}_{suffix}"


def _default_cmd(tool: ToolName) -> List[str]:
    # デフォルトは echo による簡易出力（実CLI未設定時のフォールバック）
    return ["echo", f"[{tool}] simulated output"]


def _resolve_command(tool: ToolName) -> List[str]:
    cmd = os.getenv(_env_key(tool, "CMD"))
    if cmd:
        # スペース区切りの文字列を安全に分割
        return shlex.split(cmd)
    return _default_cmd(tool)


def _resolve_args(tool: ToolName) -> List[str]:
    args = os.getenv(_env_key(tool, "ARGS"))
    if not args:
        return []
    return shlex.split(args)


def _use_stdin(tool: ToolName) -> bool:
    v = os.getenv(_env_key(tool, "USE_STDIN"), "1").strip()
    return v not in ("0", "false", "False")


async def run_external_tool(tool: ToolName, prompt: str, timeout_seconds: int = 120) -> NodeResult:
    cmd = _resolve_command(tool)
    args = _resolve_args(tool)
    use_stdin = _use_stdin(tool)

    start = time.perf_counter()
    try:
        proc = await asyncio.create_subprocess_exec(
            *(cmd + args),
            stdin=asyncio.subprocess.PIPE if use_stdin else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=prompt.encode("utf-8") if use_stdin else None),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            duration_ms = int((time.perf_counter() - start) * 1000)
            return NodeResult(
                tool=tool,
                ok=False,
                stdout=None,
                stderr=f"timeout after {timeout_seconds}s",
                exit_code=None,
                duration_ms=duration_ms,
            )

        exit_code = await proc.wait()
        duration_ms = int((time.perf_counter() - start) * 1000)

        # 標準化: 末尾改行を1つに揃える
        out = stdout.decode("utf-8", errors="replace") if stdout else ""
        err = stderr.decode("utf-8", errors="replace") if stderr else ""
        out = out.rstrip("\n") + ("\n" if out else "")
        err = err.rstrip("\n") + ("\n" if err else "")

        return NodeResult(
            tool=tool,
            ok=(exit_code == 0),
            stdout=out or None,
            stderr=err or None,
            exit_code=exit_code,
            duration_ms=duration_ms,
        )
    except FileNotFoundError as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        return NodeResult(
            tool=tool,
            ok=False,
            stdout=None,
            stderr=f"command not found: {e}",
            exit_code=None,
            duration_ms=duration_ms,
        )

