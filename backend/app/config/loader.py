from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import os


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


def build_tool_options(prompt: str, tools: List[str], cfg: Dict[str, Any], base_environ: Optional[Dict[str, str]] = None) -> Dict[Any, Dict[str, Any]]:
    """Return per-tool execution options based on tools.yml.

    Options keys: use_stdin(bool), override_args(list[str]), timeout_seconds(int)
    """
    out: Dict[Any, Dict[str, Any]] = {}
    env_in = dict(base_environ or os.environ)
    tcfg = (cfg.get("tools", {}) or {})
    for name in tools:
        c = tcfg.get(name, {}) or {}
        use_stdin = bool(c.get("stdin", True))
        arg_template = (c.get("arg_template") or "").strip()
        override_args: List[str] | None = None
        if (not use_stdin) and arg_template:
            override_args = []
            # naive brace replacement
            override_args.extend([s for s in arg_template.replace("{text}", prompt).split() if s])
        limits = c.get("limits") or {}
        timeout = int(limits.get("timeout_seconds", 120))
        retries = int(limits.get("retries", 0))
        max_output = int(limits.get("max_output_bytes", 0)) or None
        safety = c.get("safety") or {}
        deny = [str(x).lower() for x in (safety.get("deny") or [])]
        # environment filtering: allow only listed keys + PATH + configured API keys
        allow = set(["PATH"]) | set([str(x) for x in (c.get("env_allow") or [])]) | set([str(x) for x in (c.get("env_keys") or [])])
        env_add = c.get("env_add") or {}
        env_out = {k: v for k, v in env_in.items() if k in allow}
        env_out.update({k: str(v) for k, v in env_add.items()})

        out[name] = {
            "use_stdin": use_stdin,
            "override_args": override_args,
            "timeout_seconds": timeout,
            "retries": retries,
            "max_output_bytes": max_output,
            "deny": deny,
            "env": env_out,
            "cwd": c.get("cwd"),
        }
    return out


def get_max_concurrency(cfg: Dict[str, Any]) -> Optional[int]:
    try:
        v = int(((cfg.get("default") or {}).get("concurrency")) or 0)
        return v if v > 0 else None
    except Exception:
        return None
