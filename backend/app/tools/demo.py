from __future__ import annotations

import asyncio
import random
from ..models import ToolName, NodeResult


async def simulate_tool(tool: ToolName, prompt: str, on_log: callable | None = None) -> NodeResult:
    # バラつきを持たせて逐次完了させる
    # stream a few lines as logs
    for i in range(3):
        await asyncio.sleep(0.05 + random.random() * 0.15)
        if on_log is not None:
            await on_log("stdout", f"{tool.value}: processing chunk {i+1}\n")
    title = f"Demo: {tool.value} proposals for: {prompt.strip()}"
    body = ""
    if tool == ToolName.claude_code:
        body = (
            f"# {title}\n\n"
            "1. Lightweight CLI orchestrator with YAML presets\n"
            "2. Repo-aware code change suggester (semantic diffs)\n"
            "3. Test-first refactor assistant\n"
            "4. Spec-to-stub generator\n"
            "5. Inline doc improver\n\n"
            "```python\n"
            "def suggest():\n    return ['cli', 'semantic-diff', 'tdd']\n"
            "```\n"
        )
    elif tool == ToolName.codex_cli:
        body = (
            f"# {title}\n\n"
            "- Generate code patches as unified diffs\n"
            "- Emphasize compilation + tests\n\n"
            "--- a/app.py\n+++ b/app.py\n@@\n-print('hello')\n+print('hello world')\n"
        )
    elif tool == ToolName.gemini_cli:
        body = (
            f"# {title}\n\n"
            "Ideas:\n"
            "- Multi-agent brainstorm canvas\n"
            "- Prompt library with ratings\n"
            "- Cost/latency dashboard\n\n"
            "```markdown\n## Checklist\n- [ ] UI\n- [ ] API\n- [ ] Eval\n```\n"
        )
    else:  # spec_kit
        body = (
            f"# {title}\n\n"
            "spec: feature/demo\n"
            "acceptance:\n  - show graph\n  - diff outputs\n  - select best\n"
        )

    # 疑似スコア: 内容長とコード/差分/チェックリストの有無
    score = 1.0 + 0.002 * len(body)
    if "```" in body:
        score += 1.2
    if "+++" in body or "---" in body:
        score += 0.8
    return NodeResult(tool=tool, ok=True, stdout=body, stderr=None, exit_code=0, duration_ms=int(100 + random.random() * 400), score=round(score, 3))
