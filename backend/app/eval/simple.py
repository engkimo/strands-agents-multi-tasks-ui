from __future__ import annotations

import math
from typing import Dict, Any


def evaluate_text(text: str | None) -> Dict[str, Any]:
    if not text:
        return {"lines": 0, "chars": 0, "code_blocks": 0, "diff_hunks": 0, "tests": 0, "score": 0.0}
    lines = text.count("\n") + 1
    chars = len(text)
    code_blocks = text.count("```") // 2
    diff_hunks = text.count("+++ ") + text.count("--- ")
    tests = sum(1 for kw in ("test_", "describe(", "it(") if kw in text)
    # 簡易スコア: 情報量（log(行*文字)）+ コードブロック + 差分示唆 + テスト加点
    info = math.log(max(1, lines) * max(1, chars), 10)
    score = info + 1.5 * code_blocks + 1.0 * diff_hunks + 2.0 * tests
    return {
        "lines": lines,
        "chars": chars,
        "code_blocks": code_blocks,
        "diff_hunks": diff_hunks,
        "tests": tests,
        "score": round(score, 3),
    }

