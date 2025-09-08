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


async def run_external_tool(
    tool: ToolName,
    prompt: str,
    timeout_seconds: int = 120,
    on_log: callable | None = None,  # async(kind:str, text:str)
) -> NodeResult:
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

        # write stdin if needed
        if use_stdin and proc.stdin:
            try:
                proc.stdin.write(prompt.encode("utf-8"))
                await proc.stdin.drain()
            finally:
                proc.stdin.close()

        out_buf: list[str] = []
        err_buf: list[str] = []

        async def _pump(reader: asyncio.StreamReader, kind: str, buf: list[str]):
            while True:
                line = await reader.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace")
                buf.append(text)
                if on_log is not None:
                    try:
                        await on_log(kind, text)
                    except Exception:
                        # ignore log callback errors
                        pass

        try:
            await asyncio.wait_for(
                asyncio.gather(
                    _pump(proc.stdout, "stdout", out_buf),
                    _pump(proc.stderr, "stderr", err_buf),
                ),
                timeout=timeout_seconds,
            )
            exit_code = await proc.wait()
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            duration_ms = int((time.perf_counter() - start) * 1000)
            return NodeResult(
                tool=tool,
                ok=False,
                stdout="".join(out_buf) or None,
                stderr=("".join(err_buf) + f"timeout after {timeout_seconds}s\n"),
                exit_code=None,
                duration_ms=duration_ms,
            )
        duration_ms = int((time.perf_counter() - start) * 1000)

        # 標準化: 末尾改行を1つに揃える
        out = ("".join(out_buf)) if out_buf else ""
        err = ("".join(err_buf)) if err_buf else ""
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
