## Strands Agents Multi‑Tasks UI

<img width="1339" height="798" alt="image" src="https://github.com/user-attachments/assets/f823722a-258b-445b-85db-b558092da3b8" />


=============================

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![UI: React](https://img.shields.io/badge/UI-React%2018-61DAFB.svg)](#)
[![Backend: FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](#)
[![Graph: ReactFlow](https://img.shields.io/badge/Graph-React%20Flow-ff0072.svg)](#)
[![Streaming: SSE](https://img.shields.io/badge/Streaming-SSE-orange.svg)](#)

Run multiple LLM CLIs (Claude Code / Codex CLI / Gemini CLI) in parallel, and compare their I/O, diffs, and lightweight scores in a local UI. A demo mode produces visually rich outputs so you can showcase quickly. Spec Kit is currently excluded from the workflow.

Quick Start (Docker)
--------------------
1) `cp .env.example .env` (defaults to `DEMO_MODE=1`)
2) `docker compose -f docker-compose.dev.yml up --build`
3) Open UI: `http://localhost:5173` (API: `http://localhost:8000`)

How to Use (UI)
---------------
- New run: enter a prompt → select tools (2–3) → Run
- Run detail: React Flow graph (state/time/score, hover to preview logs) → per‑node I/O → Diff (line/word, ignore space/case, Markdown) → Best tool
- PR packaging: “Create PR package (adopt left)” to preview `summary.md` / `review.md` / `patch.txt`
- One‑click demo: “デモ実行（3ツール一括）” runs a showcase with a preset prompt

Native Dev (optional)
---------------------
- Backend: `cd backend && pip install -r requirements.txt && uvicorn app.api.server:app --reload`
- UI: `cd ui && npm install && npm run dev`

Real CLIs (instead of demo)
---------------------------
1) Set `DEMO_MODE=0` in `.env`
2) Provide API keys in your shell (recommended) or `.env`:
   - `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY` or `GEMINI_API_KEY`
3) Start as usual. Command/arg preferences will move to profiles (`tools.yml`) over time; `.env` should mainly hold secrets.

API One‑liners (fish)
---------------------
- Create run → show ID:
  - `set -l RUN_ID (curl -s -X POST http://localhost:8000/runs -H 'Content-Type: application/json' -d '{\"prompt\":\"Five ideas for dev tools\",\"tools\":[\"claude_code\",\"codex_cli\",\"gemini_cli\"]}' | jq -r .id); echo $RUN_ID`
- Stream progress (SSE): `curl -N http://localhost:8000/stream/runs/$RUN_ID`
- Fetch detail: `curl -s http://localhost:8000/runs/$RUN_ID | jq .`
- PR package: `curl -s -X POST http://localhost:8000/runs/$RUN_ID/package_pr -H 'Content-Type: application/json' -d '{\"tool\":\"claude_code\",\"title\":\"Demo PR\"}' | jq .`

Troubleshooting
---------------
- Empty output: ensure `DEMO_MODE=1` (demo) or real keys are exported, then `docker compose -f docker-compose.dev.yml up -d --build backend`
- Port conflict: ensure 8000/5173 are free
- Real CLI in Docker: use native backend or a custom image that bundles your CLIs

What’s Implemented
------------------
- Parallel runs + per‑node persistence, SSE: `status` / `node` / `log` / `done`
- Lightweight evaluation → `best_tool` / `best_score`
- Demo mode with rich outputs and simulated progress logs
- PR packaging: `POST /runs/{id}/package_pr` → `summary.md` / `review.md` / `patch.txt`
- React Flow graph with live log preview on hover

Docs
----
- `docs/70_demo_playbook.md`, `docs/75_demo_run.md`, `docs/80_progress_next.md`, `docs/85_pr_coderabbit.md`, `docs/90_supervisor.md`

.env Guidance
-------------
- Minimal (demo): `DEMO_MODE=1`, `DB_PATH`, `DATA_DIR`, `VITE_API_BASE`
- Real CLIs: mainly provide API keys; the supervisor (`tools.yml`) will guide tool choice
  - `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY` / `GEMINI_API_KEY`
- Command overrides (temporary): `TOOL_*_CMD/ARGS/USE_STDIN` exist but will move to profiles

Note: the dev Docker image does not include vendor CLIs. For real runs, use native backend or build a custom image.
