# 進捗まとめ（現在地）と次アクション

最終更新: 2025-09-07

## 現在の実装スコープ（MVPスケルトン達成）
- Backend（FastAPI）
  - エンドポイント: `GET /health`, `POST /runs`, `GET /runs`, `GET /runs/{id}`, `GET /stream/runs/{id}`（SSE: status/node/done）
  - 並列実行: Best-of-N（各ツールを非同期に並列実行）と逐次保存（完了順にDBへ反映）
  - 実CLI呼び出し: 非同期subprocess（STDIN可/タイムアウト/exit_code/STDOUT/STDERR収集、改行正規化）
  - 永続化: SQLite（`var/data/app.db`）+ ファイル保存（`var/data/runs/<run_id>/<tool>/stdout.txt|stderr.txt`）
  - CORS許可、SSEでJSONイベント配信
- UI（Vite + React）
  - Runs一覧/Run詳細（SSE購読）
  - 簡易グラフビュー（fan-out/fan-in、ノード状態: pending/running/success/error）
  - 差分ビュー（N出力→任意2選択、行/単語粒度、空白/大小無視、Markdown表示、コピー）
  - リトライUI（全ツール/失敗のみ/単一ツール再実行）
- DevOps
  - `.env.example`、Docker（dev）: `docker-compose.dev.yml` で backend/ui 起動
  - 起動: Backend=`uvicorn`（ホットリロード）、UI=`vite`（0.0.0.0 公開）

## API 概要
- `POST /runs`
  - 入力: `{ "prompt": str, "tools": ["claude_code"|"codex_cli"|"gemini_cli"|"spec_kit"], "timeout_seconds"?: int }`
  - 返却: `Run`（id, status=pending, created_at ...）
- `GET /runs` / `GET /runs/{id}`
  - 一覧/詳細（詳細は nodes 結果を含む）
- `GET /stream/runs/{id}`（SSE）
  - `status`/`node`/`done` イベントで `Run` のJSONを配信（nodeは結果数の増加で送信）

## 設定（環境変数）
- DB/保存先: `DB_PATH=var/data/app.db`, `DATA_DIR=var/data`
- ツール実行（未設定時は `echo` フォールバック）
  - `TOOL_CLAUDE_CODE_CMD`, `TOOL_CLAUDE_CODE_ARGS`, `TOOL_CLAUDE_CODE_USE_STDIN=1`
  - `TOOL_CODEX_CLI_CMD`,  `TOOL_CODEX_CLI_ARGS`,  `TOOL_CODEX_CLI_USE_STDIN=1`
  - `TOOL_GEMINI_CLI_CMD`, `TOOL_GEMINI_CLI_ARGS`, `TOOL_GEMINI_CLI_USE_STDIN=1`
  - `TOOL_SPEC_KIT_CMD`,  `TOOL_SPEC_KIT_ARGS`,  `TOOL_SPEC_KIT_USE_STDIN=1`
- UI: `VITE_API_BASE=http://localhost:8000`

## ローカル起動手順（2通り）
- Docker（推奨）
  - `cp .env.example .env`
  - `docker compose -f docker-compose.dev.yml up --build`
  - UI: `http://localhost:5173` / API: `http://localhost:8000`
- ネイティブ
  - Backend: `cd backend && pip install -r requirements.txt && uvicorn app.api.server:app --reload`
  - UI: `cd ui && npm install && npm run dev`

## 既知の制約/未実装
- ノードのSTDOUT逐次ストリーム（現状は完了単位）
- DiffのN-way比較（現状は任意2出力の比較）
- 評価指標/スコアリング（順位付け、ベスト自動選択）
- OTelのSpan/Metric連携は骨組み未実装（TODO）
- 入力サニタイズ/安全装備の粒度向上（引数テンプレ/ホワイトリスト）
- Windowsのパス/PTY差異検証

## 次アクション（優先順）
1. ノード出力の逐次ストリーミング
   - Backend: subprocessのSTDOUT/STDERRを行バッファで逐次SSE送信（`event: log` with node context）
   - UI: ノードパネルのライブログ表示（折りたたみ/検索）
2. ベスト選択の保存と履歴
   - UI: 「採用」ボタン→Runにbest_ofフィールド保存、一覧でフィルタ/バッジ表示
   - Backend/DB: runsに`best_tool`/`best_artifact`等を追加
3. 簡易評価メトリクス
   - 文字数/固有語彙数/キーワード包含率/重複率などの軽量指標を算出しUI表示
   - MVP後にモデル採点やルーブリックへ拡張
4. CLIテンプレ/プロファイル
   - STDIN非対応CLIに対する引数テンプレ（`--prompt="{text}"` 等）をプロファイル化
   - .env ではなく `tools.yml` 等で複数設定を切替
5. OpenTelemetry 連携
   - Run/NodeをSpanとして計測（tool, latency, exit_code属性）
   - ローカルエクスポータ→将来Grafana/Langfuse等へ
6. テスト/安定性
   - ユニット（runner/DB）+ E2E（echoモック）で基本動作をカバー
   - タイムアウト/キャンセル/失敗時の復帰を検証
7. UI磨き込み
   - グラフのレイアウト/色覚配慮、DiffのN出力切替、Markdownの見栄え
   - エラー時のトースト/ガイド
8. Windows検証
   - パス/プロセス/改行差異を確認しREADMEに注意書き

---
- 参照: `docs/10_prd.md`, `docs/40_mvp.md`, `docs/70_demo_playbook.md`
- 競合対比: Difyに対し「CLI横断・並列比較・透明なI/O/コスト可視化」を強調

