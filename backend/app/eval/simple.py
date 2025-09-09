from __future__ import annotations

import math
import re
from typing import Dict, Any


def _tokens(s: str) -> list[str]:
    # Split on word characters for a lightweight, language-agnostic tokenization
    return re.findall(r"[\w\-]+", s.lower())


def evaluate_text(text: str | None, prompt: str | None = None) -> Dict[str, Any]:
    if not text:
        return {
            "lines": 0,
            "chars": 0,
            "code_blocks": 0,
            "diff_hunks": 0,
            "tests": 0,
            "vocab": 0,
            "ttr": 0.0,
            "avg_line_len": 0.0,
            "dup_lines": 0.0,
            "keyword_hits": 0,
            "keyword_cover": 0.0,
            "score": 0.0,
        }

    lines = text.count("\n") + 1
    chars = len(text)
    code_blocks = text.count("```") // 2
    diff_hunks = text.count("+++ ") + text.count("--- ")
    tests = sum(1 for kw in ("test_", "describe(", "it(") if kw in text)

    # Vocabulary and TTR
    toks = _tokens(text)
    total_tokens = len(toks)
    vocab = len(set(toks)) if total_tokens else 0
    ttr = (vocab / total_tokens) if total_tokens else 0.0

    # Average line length and duplicate line ratio
    avg_line_len = (chars / lines) if lines else 0.0
    unique_lines = len(set(text.splitlines())) if lines else 0
    dup_lines = (lines - unique_lines) / lines if lines and unique_lines >= 0 else 0.0

    # Prompt keyword coverage (very lightweight)
    keyword_hits = 0
    keyword_cover = 0.0
    if prompt:
        p_toks = [w for w in _tokens(prompt) if len(w) >= 4]
        p_set = set(p_toks)
        out_set = set(toks)
        if p_set:
            hits = p_set & out_set
            keyword_hits = len(hits)
            keyword_cover = keyword_hits / len(p_set)

    # Scoring (heuristic):
    # - Base information: log10(lines*chars)
    # - Bonus: code blocks, diff hints, tests
    # - Quality: moderate TTR, keyword coverage
    # - Penalty: excessive duplicate lines
    info = math.log(max(1, lines) * max(1, chars), 10)
    score = info
    score += 1.5 * code_blocks
    score += 1.0 * diff_hunks
    score += 2.0 * tests
    score += 1.2 * keyword_cover  # 0..1
    score += 0.8 * min(ttr, 1.0)  # cap TTR contribution
    score -= 1.0 * max(0.0, dup_lines)  # penalize duplication

    return {
        "lines": lines,
        "chars": chars,
        "code_blocks": code_blocks,
        "diff_hunks": diff_hunks,
        "tests": tests,
        "vocab": vocab,
        "ttr": round(ttr, 3),
        "avg_line_len": round(avg_line_len, 2),
        "dup_lines": round(dup_lines, 3),
        "keyword_hits": keyword_hits,
        "keyword_cover": round(keyword_cover, 3),
        "score": round(score, 3),
    }
