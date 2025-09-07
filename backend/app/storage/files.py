from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple


BASE_DIR = Path(os.getenv("DATA_DIR", "var/data")).resolve()


def ensure_base_dir() -> None:
    (BASE_DIR / "runs").mkdir(parents=True, exist_ok=True)


def run_dir(run_id: str) -> Path:
    return BASE_DIR / "runs" / run_id


def node_dir(run_id: str, tool: str) -> Path:
    p = run_dir(run_id) / tool
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_artifacts(run_id: str, tool: str, stdout: str | None, stderr: str | None) -> Tuple[str | None, str | None]:
    nd = node_dir(run_id, tool)
    stdout_path = None
    stderr_path = None
    if stdout is not None:
        stdout_path = str(nd / "stdout.txt")
        with open(stdout_path, "w", encoding="utf-8") as f:
            f.write(stdout)
    if stderr is not None:
        stderr_path = str(nd / "stderr.txt")
        with open(stderr_path, "w", encoding="utf-8") as f:
            f.write(stderr)
    return stdout_path, stderr_path


def read_text_or_none(path: str | None) -> str | None:
    if not path:
        return None


def pr_dir(run_id: str) -> Path:
    p = run_dir(run_id) / "pr"
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_text(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return str(path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None
