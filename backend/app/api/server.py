from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json

from ..models import Run, RunCreate, RunStatus, ToolName
from ..agents.graph import run_best_of_n, iter_best_of_n
from ..storage.sqlite import DB
from ..storage.files import ensure_base_dir, pr_dir, write_text, node_dir, read_text_or_none
from ..eval.simple import evaluate_text
from pydantic import BaseModel
from ..config.loader import load_tools_config, recommend_tools as _recommend_tools, build_tool_options, get_max_concurrency
from ..telemetry.otel import setup_otel
from opentelemetry import trace


app = FastAPI(title="Strands Agents Multi-Tasks Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup():
    ensure_base_dir()
    app.state.db = DB()
    app.state.tools_cfg = load_tools_config()
    app.state.log_queues: Dict[str, asyncio.Queue] = {}
    setup_otel()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/runs", response_model=Run)
async def create_run(req: RunCreate):
    if not req.tools:
        raise HTTPException(status_code=400, detail="tools is empty")
    run_id = str(uuid.uuid4())
    created_at = datetime.utcnow()
    db: DB = app.state.db
    db.create_run(run_id, req.prompt, req.tools, RunStatus.pending, created_at, req.timeout_seconds)
    run = db.get_run(run_id)

    # ensure a log queue for this run
    app.state.log_queues[run_id] = asyncio.Queue()

    tracer = trace.get_tracer("api.server")

    async def _worker():
        db.update_run_status(run_id, RunStatus.running)
        with tracer.start_as_current_span("run", attributes={
            "run.id": run_id,
            "run.tools": ",".join([t.value for t in req.tools]),
        }):
            try:
                tool_opts = build_tool_options(req.prompt, [t.value for t in req.tools], app.state.tools_cfg)
                tool_options_map = {ToolName(k): v for k, v in tool_opts.items()}
                maxc = get_max_concurrency(app.state.tools_cfg)
                async for res in iter_best_of_n(
                    req.prompt,
                    req.tools,
                    timeout_seconds=(req.timeout_seconds or 120),
                    on_log=_make_log_cb(run_id),
                    tool_options=tool_options_map,
                    max_concurrency=maxc,
                ):
                    metrics = evaluate_text(res.stdout, prompt=req.prompt)
                    res.score = metrics.get("score", 0.0)
                    db.insert_node_result(run_id, res)
                db.update_run_status(run_id, RunStatus.completed, ended_at=datetime.utcnow())
                db.update_run_best(run_id)
            except Exception:
                db.update_run_status(run_id, RunStatus.failed, ended_at=datetime.utcnow())

    asyncio.create_task(_worker())
    return run


@app.get("/runs")
async def list_runs():
    db: DB = app.state.db
    items = db.list_runs()
    return JSONResponse(items)


@app.get("/runs/{run_id}", response_model=Run)
async def get_run(run_id: str):
    db: DB = app.state.db
    run = db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return run


@app.get("/stream/runs/{run_id}")
async def stream_run(run_id: str):
    db: DB = app.state.db
    if not db.get_run(run_id):
        raise HTTPException(status_code=404, detail="run not found")

    async def event_gen():
        # 簡易ポーリングSSE（実装初期）
        last_status = None
        last_count = -1
        while True:
            run = db.get_run(run_id)
            if not run:
                break
            if run.status != last_status:
                last_status = run.status
                payload = json.dumps(run.model_dump(mode="json"))
                yield f"event: status\ndata: {payload}\n\n"
            # ノード結果の追加を逐次通知
            cur_count = len(run.results)
            if cur_count != last_count:
                last_count = cur_count
                payload = json.dumps(run.model_dump(mode="json"))
                yield f"event: node\ndata: {payload}\n\n"
            # log drain
            q = app.state.log_queues.get(run_id)
            if q is not None:
                while True:
                    try:
                        item = q.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                    else:
                        yield f"event: log\ndata: {json.dumps(item)}\n\n"
            if run.status in (RunStatus.completed, RunStatus.failed):
                break
            await asyncio.sleep(0.5)
        # 終了イベント
        final_run = db.get_run(run_id)
        payload = json.dumps(final_run.model_dump(mode="json"))
        yield f"event: done\ndata: {payload}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


class PackageRequest(BaseModel):
    tool: ToolName | None = None
    title: str | None = None


@app.post("/runs/{run_id}/package_pr")
async def package_pr(run_id: str, req: PackageRequest):
    db: DB = app.state.db
    run = db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    # pick tool
    tool = req.tool or run.best_tool
    if not tool:
        # fallback: first ok result
        ok = next((r for r in run.results if r.ok), None)
        if not ok:
            raise HTTPException(status_code=400, detail="no successful node to package")
        tool = ok.tool
    res = next((r for r in run.results if r.tool == tool), None)
    if not res:
        raise HTTPException(status_code=400, detail="selected tool result not found")
    # 最終的な出力はファイルを優先（DBに内容未格納でも復元可能）
    content = res.stdout or read_text_or_none(str(node_dir(run_id, tool.value) / "stdout.txt")) or ""
    metrics = evaluate_text(content, prompt=run.prompt)
    title = req.title or f"Proposal from {tool.value}"
    # Build files
    summary_md = (
        f"# {title}\n\n"
        f"- Tool: `{tool.value}`  \\n+        - Score: {res.score if res.score is not None else metrics.get('score', 0)}  \\n+        - Run: `{run_id}`  \\n+        - Prompt: `{run.prompt[:200]}`\n\n"
        "## Proposal\n\n" + content + "\n\n"
        "## Heuristics\n\n"
        f"- lines: {metrics.get('lines')}  chars: {metrics.get('chars')}  code_blocks: {metrics.get('code_blocks')}  diff_hunks: {metrics.get('diff_hunks')}  tests: {metrics.get('tests')}\n"
    )
    # Extract unified diff if any
    patch_text = ""
    if "--- " in content and "+++ " in content:
        patch_text = "\n".join(
            [line for line in content.splitlines() if line.startswith(("--- ", "+++ ", "@@", "+", "-", " "))]
        )
    review_md = (
        f"# Review (heuristic)\n\n"
        f"- Overall score: {res.score if res.score is not None else metrics.get('score', 0)}\n"
        + ("- Consider adding tests.\n" if metrics.get("tests", 0) == 0 else "")
        + ("- Provide code blocks for clarity.\n" if metrics.get("code_blocks", 0) == 0 else "")
    )

    # Safe summary_md (triple-quoted; avoids concatenation artifacts)
    summary_md2 = f"""# {title}

- Tool: `{tool.value}`
- Score: {res.score if res.score is not None else metrics.get('score', 0)}
- Run: `{run_id}`
- Prompt: `{run.prompt[:200]}`

## Proposal

{content}

## Heuristics

- lines: {metrics.get('lines')}  chars: {metrics.get('chars')}  code_blocks: {metrics.get('code_blocks')}  diff_hunks: {metrics.get('diff_hunks')}  tests: {metrics.get('tests')}
- vocab: {metrics.get('vocab')}  ttr: {metrics.get('ttr')}  avg_line_len: {metrics.get('avg_line_len')}
- keyword_hits: {metrics.get('keyword_hits')}  keyword_cover: {metrics.get('keyword_cover')}  dup_lines: {metrics.get('dup_lines')}
"""

    out = pr_dir(run_id)
    summary_path = write_text(out / "summary.md", summary_md2)
    review_path = write_text(out / "review.md", review_md)
    patch_path = None
    if patch_text:
        patch_path = write_text(out / "patch.txt", patch_text)

    return JSONResponse(
        {
            "run_id": run_id,
            "tool": tool.value,
            "dir": str(out),
            "files": {
                "summary": summary_path,
                "review": review_path,
                "patch": patch_path,
            },
            "content": {
                "summary_md": summary_md2,
                "review_md": review_md,
                "patch_text": patch_text or None,
            },
        }
    )


def _make_log_cb(run_id: str):
    async def _cb(tool: ToolName, kind: str, text: str):
        q: asyncio.Queue = app.state.log_queues.setdefault(run_id, asyncio.Queue())
        await q.put({"run_id": run_id, "tool": tool.value, "kind": kind, "text": text})
    return _cb


class RecommendRequest(BaseModel):
    prompt: str


@app.post("/recommend")
async def post_recommend(req: RecommendRequest):
    cfg = app.state.tools_cfg
    names, selector = _recommend_tools(req.prompt, cfg)
    valid = []
    for n in names:
        try:
            valid.append(ToolName(n))
        except Exception:
            continue
    return {"tools": [v.value for v in valid], "selector": selector}


@app.get("/config/tools")
async def get_tools_config():
    return app.state.tools_cfg


class AdoptRequest(BaseModel):
    tool: ToolName


@app.post("/runs/{run_id}/adopt", response_model=Run)
async def adopt_best(run_id: str, req: AdoptRequest):
    db: DB = app.state.db
    run = db.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    ok = db.adopt_best_tool(run_id, req.tool)
    if not ok:
        raise HTTPException(status_code=400, detail="node result for tool not found")
    return db.get_run(run_id)
