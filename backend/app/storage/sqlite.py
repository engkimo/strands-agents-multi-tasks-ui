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
                "SELECT id, prompt, tools_json, status, created_at, ended_at, best_tool, best_score FROM runs ORDER BY datetime(created_at) DESC"
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
                    "best_tool": r["best_tool"],
                    "best_score": r["best_score"],
                }
            )
        return items

    def adopt_best_tool(self, run_id: str, tool: ToolName) -> bool:
        with self._lock:
            cur = self._conn.cursor()
            node = cur.execute(
                "SELECT score FROM nodes WHERE run_id=? AND tool=? ORDER BY id DESC LIMIT 1",
                (run_id, tool.value),
            ).fetchone()
            if not node:
                return False
            score = node["score"] if "score" in node.keys() else node[0]
            cur.execute(
                "UPDATE runs SET best_tool=?, best_score=? WHERE id=?",
                (tool.value, score, run_id),
            )
            return True

    def metrics_summary(self) -> Dict[str, Any]:
        """Return lightweight aggregate metrics for dashboard cards.

        Includes overall counts and per-tool aggregates.
        """
        with self._lock:
            cur = self._conn.cursor()
            total_runs = cur.execute("SELECT COUNT(*) AS c FROM runs").fetchone()[0]
            row_nodes = cur.execute(
                "SELECT COUNT(*) AS c, SUM(ok) AS ok FROM nodes"
            ).fetchone()
            total_nodes = row_nodes["c"] if "c" in row_nodes.keys() else row_nodes[0]
            ok_nodes = row_nodes["ok"] if "ok" in row_nodes.keys() else row_nodes[1]
            ok_nodes = int(ok_nodes or 0)
            fail_nodes = int((total_nodes or 0) - ok_nodes)
            row_avg_all = cur.execute(
                "SELECT AVG(duration_ms) AS a FROM nodes WHERE duration_ms IS NOT NULL"
            ).fetchone()
            avg_duration_ms_all = row_avg_all["a"] if "a" in row_avg_all.keys() else row_avg_all[0]
            row_avg_ok = cur.execute(
                "SELECT AVG(duration_ms) AS a FROM nodes WHERE ok=1 AND duration_ms IS NOT NULL"
            ).fetchone()
            avg_duration_ms_ok = row_avg_ok["a"] if "a" in row_avg_ok.keys() else row_avg_ok[0]

            per_tool: Dict[str, Any] = {}
            for r in cur.execute(
                """
                SELECT tool,
                       COUNT(*) AS cnt,
                       SUM(ok) AS ok_cnt,
                       AVG(duration_ms) AS avg_ms,
                       AVG(score) AS avg_score
                  FROM nodes
                 GROUP BY tool
                """
            ).fetchall():
                tool = r["tool"] if "tool" in r.keys() else r[0]
                cnt = r["cnt"] if "cnt" in r.keys() else r[1]
                ok_cnt = r["ok_cnt"] if "ok_cnt" in r.keys() else r[2]
                avg_ms = r["avg_ms"] if "avg_ms" in r.keys() else r[3]
                avg_score = r["avg_score"] if "avg_score" in r.keys() else r[4]
                per_tool[tool] = {
                    "count": int(cnt or 0),
                    "ok": int(ok_cnt or 0),
                    "fail": int((cnt or 0) - (ok_cnt or 0)),
                    "avg_duration_ms": float(avg_ms) if avg_ms is not None else None,
                    "avg_score": float(avg_score) if avg_score is not None else None,
                }

        return {
            "total_runs": int(total_runs or 0),
            "total_nodes": int(total_nodes or 0),
            "ok_nodes": ok_nodes,
            "fail_nodes": fail_nodes,
            "avg_duration_ms": float(avg_duration_ms_all) if avg_duration_ms_all is not None else None,
            "avg_duration_ms_ok": float(avg_duration_ms_ok) if avg_duration_ms_ok is not None else None,
            "per_tool": per_tool,
        }
