from __future__ import annotations

import asyncio
from typing import List, Callable, Awaitable, Optional
from ..models import ToolName, NodeResult
from ..tools import run_tool


async def run_best_of_n(
    prompt: str,
    tools: List[ToolName],
    timeout_seconds: int = 120,
    on_log: Optional[Callable[[ToolName, str, str], Awaitable[None]]] = None,
) -> List[NodeResult]:
    # 並列に各ツールを実行し、結果を返す（スケルトン）
    def _cb_for(tool: ToolName):
        if on_log is None:
            return None
        async def _inner(kind: str, text: str):
            await on_log(tool, kind, text)
        return _inner

    tasks = [
        asyncio.create_task(run_tool(t, prompt, timeout_seconds=timeout_seconds, on_log=_cb_for(t)))
        for t in tools
    ]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    return list(results)


async def iter_best_of_n(
    prompt: str,
    tools: List[ToolName],
    timeout_seconds: int = 120,
    on_log: Optional[Callable[[ToolName, str, str], Awaitable[None]]] = None,
):
    """各ツールの結果を完了順に逐次返す非同期イテレータ。

    使用例:
        async for res in iter_best_of_n(prompt, tools):
            ...
    """
    def _cb_for(tool: ToolName):
        if on_log is None:
            return None
        async def _inner(kind: str, text: str):
            await on_log(tool, kind, text)
        return _inner

    tasks = [
        asyncio.create_task(run_tool(t, prompt, timeout_seconds=timeout_seconds, on_log=_cb_for(t)))
        for t in tools
    ]
    for fut in asyncio.as_completed(tasks):
        res = await fut
        yield res
