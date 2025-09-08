from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models import Run, RunStatus, ToolName, NodeResult
from .files import ensure_base_dir, write_artifacts, read_text_or_none, node_dir


class DB:
    def __init__(self, path: str = None) -> None:
        self.path = path or os.getenv("DB_PATH", "var/data/app.db")
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        self._init_schema()

    def _init_schema(self) -> None:
        with self._conn as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                  id TEXT PRIMARY KEY,
                  prompt TEXT NOT NULL,
                  tools_json TEXT NOT NULL,
                  status TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  ended_at TEXT,
                  timeout_seconds INTEGER,
                  best_tool TEXT,
                  best_score REAL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  run_id TEXT NOT NULL,
                  tool TEXT NOT NULL,
                  ok INTEGER NOT NULL,
                  stdout_path TEXT,
                  stderr_path TEXT,
                  exit_code INTEGER,
                  duration_ms INTEGER,
                  score REAL,
                  FOREIGN KEY (run_id) REFERENCES runs(id)
                )
                """
            )

    # Run operations
    def create_run(self, run_id: str, prompt: str, tools: List[ToolName], status: RunStatus, created_at: datetime, timeout_seconds: Optional[int]) -> None:
        with self._lock, self._conn as con:
            con.execute(
                "INSERT INTO runs(id, prompt, tools_json, status, created_at, timeout_seconds) VALUES (?,?,?,?,?,?)",
                (run_id, prompt, json.dumps([t.value for t in tools]), status.value, created_at.isoformat(), timeout_seconds),
            )

    def update_run_status(self, run_id: str, status: RunStatus, ended_at: Optional[datetime] = None) -> None:
        with self._lock, self._conn as con:
            con.execute(
                "UPDATE runs SET status=?, ended_at=? WHERE id=?",
                (status.value, ended_at.isoformat() if ended_at else None, run_id),
            )

    def insert_node_result(self, run_id: str, res: NodeResult) -> None:
        stdout_path, stderr_path = write_artifacts(run_id, res.tool.value, res.stdout, res.stderr)
        with self._lock, self._conn as con:
            con.execute(
                """
                INSERT INTO nodes(run_id, tool, ok, stdout_path, stderr_path, exit_code, duration_ms, score)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    run_id,
                    res.tool.value,
                    1 if res.ok else 0,
                    stdout_path,
                    stderr_path,
                    res.exit_code,
                    res.duration_ms,
                    res.score,
                ),
            )

    def update_run_best(self, run_id: str) -> None:
        with self._lock, self._conn as con:
            row = con.execute(
                "SELECT tool, MAX(score) as s FROM nodes WHERE run_id=?",
                (run_id,),
            ).fetchone()
            if row and row["s"] is not None:
                con.execute(
                    "UPDATE runs SET best_tool=?, best_score=? WHERE id=?",
                    (row["tool"], row["s"], run_id),
                )

    def get_run(self, run_id: str) -> Optional[Run]:
        with self._lock:
            cur = self._conn.cursor()
            row = cur.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if not row:
                return None
            runs_tools = [ToolName(t) for t in json.loads(row["tools_json"])]
            nodes_rows = cur.execute("SELECT * FROM nodes WHERE run_id=?", (run_id,)).fetchall()
        results: List[NodeResult] = []
        for nr in nodes_rows:
            # パスが欠損/不整合でも既定パスから復元を試みる
            stdout_p = nr["stdout_path"] or str(node_dir(run_id, nr["tool"]) / "stdout.txt")
            stderr_p = nr["stderr_path"] or str(node_dir(run_id, nr["tool"]) / "stderr.txt")
            results.append(
                NodeResult(
                    tool=ToolName(nr["tool"]),
                    ok=bool(nr["ok"]),
                    stdout=read_text_or_none(stdout_p),
                    stderr=read_text_or_none(stderr_p),
                    exit_code=nr["exit_code"],
                    duration_ms=nr["duration_ms"],
                    score=nr["score"],
                )
            )
        run = Run(
            id=row["id"],
            status=RunStatus(row["status"]),
            prompt=row["prompt"],
            tools=runs_tools,
            created_at=datetime.fromisoformat(row["created_at"]),
            ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
            results=results,
            best_tool=ToolName(row["best_tool"]) if row["best_tool"] else None,
            best_score=row["best_score"],
        )
        return run

    def list_runs(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows = self._conn.cursor().execute(
                "SELECT id, prompt, tools_json, status, created_at, ended_at FROM runs ORDER BY datetime(created_at) DESC"
            ).fetchall()
        items: List[Dict[str, Any]] = []
        for r in rows:
            items.append(
                {
                    "id": r["id"],
                    "prompt": r["prompt"],
                    "tools": json.loads(r["tools_json"]),
                    "status": r["status"],
                    "created_at": r["created_at"],
                    "ended_at": r["ended_at"],
                }
            )
        return items
