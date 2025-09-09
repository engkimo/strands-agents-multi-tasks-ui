from __future__ import annotations

import asyncio
from typing import List, Callable, Awaitable, Optional
from ..models import ToolName, NodeResult
from ..tools import run_tool
from opentelemetry import trace


async def run_best_of_n(
    prompt: str,
    tools: List[ToolName],
    timeout_seconds: int = 120,
    on_log: Optional[Callable[[ToolName, str, str], Awaitable[None]]] = None,
    tool_options: Optional[dict] = None,
    max_concurrency: Optional[int] = None,
) -> List[NodeResult]:
    # 並列に各ツールを実行し、結果を返す（スケルトン）
    tracer = trace.get_tracer("agents.graph")

    sem = asyncio.Semaphore(max_concurrency) if (max_concurrency and max_concurrency > 0) else None

    async def _run_one(t: ToolName):
        opts = tool_options.get(t) if tool_options else None
        with tracer.start_as_current_span("tool.run", attributes={
            "tool.name": t.value,
            "tool.timeout": (opts or {}).get("timeout_seconds", timeout_seconds),
            "run.prompt.size": len(prompt or ""),
        }) as span:
            async def _inner(kind: str, text: str):
                # Log events are truncated upstream if needed
                try:
                    span.add_event("log", {"kind": kind, "size": len(text)})
                except Exception:
                    pass
                if on_log is not None:
                    await on_log(t, kind, text)
            async def _go():
                return await run_tool(t, prompt, timeout_seconds=timeout_seconds, on_log=_inner, options=opts)
            if sem:
                async with sem:
                    res = await _go()
            else:
                res = await _go()
            # enrich span
            try:
                span.set_attribute("tool.exit_code", res.exit_code if res.exit_code is not None else -1)
                span.set_attribute("tool.ok", bool(res.ok))
                if res.duration_ms is not None:
                    span.set_attribute("tool.duration_ms", res.duration_ms)
                if res.score is not None:
                    span.set_attribute("tool.score", res.score)
            except Exception:
                pass
            return res

    tasks = [asyncio.create_task(_run_one(t)) for t in tools]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    return list(results)


async def iter_best_of_n(
    prompt: str,
    tools: List[ToolName],
    timeout_seconds: int = 120,
    on_log: Optional[Callable[[ToolName, str, str], Awaitable[None]]] = None,
    tool_options: Optional[dict] = None,
    max_concurrency: Optional[int] = None,
):
    """各ツールの結果を完了順に逐次返す非同期イテレータ。

    使用例:
        async for res in iter_best_of_n(prompt, tools):
            ...
    """
    tracer = trace.get_tracer("agents.graph")

    sem = asyncio.Semaphore(max_concurrency) if (max_concurrency and max_concurrency > 0) else None

    async def _run_one(t: ToolName):
        opts = tool_options.get(t) if tool_options else None
        with tracer.start_as_current_span("tool.run", attributes={
            "tool.name": t.value,
            "tool.timeout": (opts or {}).get("timeout_seconds", timeout_seconds),
            "run.prompt.size": len(prompt or ""),
        }) as span:
            async def _inner(kind: str, text: str):
                try:
                    span.add_event("log", {"kind": kind, "size": len(text)})
                except Exception:
                    pass
                if on_log is not None:
                    await on_log(t, kind, text)
            async def _go():
                return await run_tool(t, prompt, timeout_seconds=timeout_seconds, on_log=_inner, options=opts)
            if sem:
                async with sem:
                    res = await _go()
            else:
                res = await _go()
            try:
                span.set_attribute("tool.exit_code", res.exit_code if res.exit_code is not None else -1)
                span.set_attribute("tool.ok", bool(res.ok))
                if res.duration_ms is not None:
                    span.set_attribute("tool.duration_ms", res.duration_ms)
                if res.score is not None:
                    span.set_attribute("tool.score", res.score)
            except Exception:
                pass
            return res

    tasks = [asyncio.create_task(_run_one(t)) for t in tools]
    for fut in asyncio.as_completed(tasks):
        res = await fut
        yield res
