Strands Agents Multi‑Tasks UI
=============================

LLM系CLI（Claude Code / Codex CLI / Gemini CLI / Spec Kit）を並列実行し、入出力・差分・評価をUIで比較するローカルツールです。デモモードで最短デモが可能。

Quick Start（Docker）
---------------------
1) `cp .env.example .env`（既定で DEMO_MODE=1）
2) `docker compose -f docker-compose.dev.yml up --build`
3) ブラウザ: `http://localhost:5173`

使い方（UI）
------------
- 新規実行: プロンプト入力 → ツール（2〜4）選択 → 実行
- Run詳細: グラフ（状態/時間/score）→ 結果（stdout/stderr）→ 差分（行/単語・空白/大小無視・Markdown）→ ベスト表示
- PRパッケージ: 「PRパッケージ作成（左を採用）」で summary/review/patch をローカル保存＆プレビュー

ネイティブ起動（任意）
----------------------
- Backend: `cd backend && pip install -r requirements.txt && uvicorn app.api.server:app --reload`
- UI: `cd ui && npm install && npm run dev`

実CLIで動かす
--------------
- `.env` で `DEMO_MODE=0` に変更
- 例: `TOOL_CLAUDE_CODE_CMD="claude"` / `TOOL_CLAUDE_CODE_ARGS="--mode code"` / `TOOL_CLAUDE_CODE_USE_STDIN=1`（他ツールも同様）

APIワンライナー（fish）
------------------------
- Run作成→ID表示: `set -l RUN_ID (curl -s -X POST http://localhost:8000/runs -H 'Content-Type: application/json' -d '{\"prompt\":\"アイデアを5つ\",\"tools\":[\"claude_code\",\"codex_cli\",\"gemini_cli\",\"spec_kit\"]}' | jq -r .id); echo $RUN_ID`
- 進捗SSE: `curl -N http://localhost:8000/stream/runs/$RUN_ID`
- 詳細: `curl -s http://localhost:8000/runs/$RUN_ID | jq .`
- PRパッケージ: `curl -s -X POST http://localhost:8000/runs/$RUN_ID/package_pr -H 'Content-Type: application/json' -d '{\"tool\":\"claude_code\",\"title\":\"Demo PR\"}' | jq .`

トラブルシュート
----------------
- 出力が空: `.env` の DEMO_MODE=1 を確認 → `docker compose -f docker-compose.dev.yml up -d --build backend`
- ポート競合: 8000/5173 が空いているか確認
- 実CLI: `TOOL_*` 設定と PATH/権限を確認

実装サマリ
----------
- 並列実行 + 逐次保存、SSE `status`/`node`/`done`
- 評価とベスト: 簡易スコア → best_tool/best_score
- DEMO_MODE: 擬似出力（見栄えの良い提案/コード/差分）
- PRパッケージ: `POST /runs/{id}/package_pr`（summary/review/patch生成）
- 永続化: SQLite + ファイル

Docs
----
- `docs/70_demo_playbook.md`, `docs/75_demo_run.md`, `docs/80_progress_next.md`, `docs/85_pr_coderabbit.md`
