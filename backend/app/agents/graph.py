from __future__ import annotations

import asyncio
from typing import List
from ..models import ToolName, NodeResult
from ..tools import run_tool


async def run_best_of_n(prompt: str, tools: List[ToolName], timeout_seconds: int = 120) -> List[NodeResult]:
    # 並列に各ツールを実行し、結果を返す（スケルトン）
    tasks = [asyncio.create_task(run_tool(t, prompt, timeout_seconds=timeout_seconds)) for t in tools]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    return list(results)


async def iter_best_of_n(prompt: str, tools: List[ToolName], timeout_seconds: int = 120):
    """各ツールの結果を完了順に逐次返す非同期イテレータ。

    使用例:
        async for res in iter_best_of_n(prompt, tools):
            ...
    """
    tasks = [asyncio.create_task(run_tool(t, prompt, timeout_seconds=timeout_seconds)) for t in tools]
    for fut in asyncio.as_completed(tasks):
        res = await fut
        yield res
