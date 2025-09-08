from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _default_path() -> Path:
    here = Path(__file__).resolve().parent
    return here / "tools.yml"


def load_tools_config(path: Optional[str] = None) -> Dict[str, Any]:
    cfg_path = Path(path or os.getenv("TOOLS_CONFIG_PATH", str(_default_path()))).resolve()
    if not cfg_path.exists():
        return {"tools": {}, "selectors": [], "default": {"recommend": []}}
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def recommend_tools(prompt: str, cfg: Dict[str, Any]) -> Tuple[List[str], Optional[str]]:
    p = prompt or ""
    selectors = cfg.get("selectors", []) or []
    for sel in selectors:
        kws = sel.get("keywords", []) or []
        if any(kw for kw in kws if kw and kw.lower() in p.lower()):
            return list(sel.get("recommend", []) or []), sel.get("name")
    # default
    return list((cfg.get("default", {}) or {}).get("recommend", []) or []), None

