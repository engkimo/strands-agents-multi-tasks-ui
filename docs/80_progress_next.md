# 進捗まとめ（現在地）と次アクション

最終更新: 2025-09-07

## 要約（直近の到達点）
- UI: React Flow によるグラフ表示、ノードホバー時にライブログ（SSE: log）/最終stdoutを下部にプレビュー
- 実行: 並列（Best-of-N）+ 逐次保存、PRパッケージ（summary/review/patch）生成
- 推奨: tools.yml + /recommend による推奨ツール選択（Runs画面から反映）
- 評価: 軽量メトリクス拡張（vocab/TTR/平均行長/重複行率/キーワード包含率）をスコアに反映
- ベスト: 自動選定 + 手動採用（/runs/{id}/adopt）、一覧にベストバッジ表示
- プロファイル: tools.yml で stdin/arg_template/timeout/retries/max_output_bytes/deny を適用
- テレメトリ: OpenTelemetry で run/tool span と log イベントを記録（OTLP or Console）
- テスト: loader/evaluator/runner をunittestでスモーク

## 現在の実装スコープ（MVPスケルトン達成）
- Backend（FastAPI）
  - エンドポイント: `GET /health`, `POST /runs`, `GET /runs`, `GET /runs/{id}`, `GET /stream/runs/{id}`（SSE: status/node/done）
  - 並列実行: Best-of-N（各ツールを非同期に並列実行）と逐次保存（完了順にDBへ反映）
  - 実CLI呼び出し: 非同期subprocess（STDIN可/タイムアウト/exit_code/STDOUT/STDERR収集、改行正規化）
  - 永続化: SQLite（`var/data/app.db`）+ ファイル保存（`var/data/runs/<run_id>/<tool>/stdout.txt|stderr.txt`）
  - CORS許可、SSEでJSONイベント配信
  - PRパッケージ: `POST /runs/{id}/package_pr`（summary/review/patch 生成）
  - スーパーバイザー: `POST /recommend`（tools.yml に基づく推奨ツール選択）、`GET /config/tools`
- UI（Vite + React）
  - Runs一覧/Run詳細（SSE購読）
  - 簡易グラフビュー（fan-out/fan-in、ノード状態: pending/running/success/error）
  - 差分ビュー（N出力→任意2選択、行/単語粒度、空白/大小無視、Markdown表示、コピー）
  - リトライUI（全ツール/失敗のみ/単一ツール再実行）
  - デモ強化: 「デモ実行（3ツール一括）」ボタン、簡易チュートリアル表示
  - 推奨選択: 「推奨ツール選択」ボタンで `/recommend` の結果を反映
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

## 次アクション（優先順・最新版）
1. ノード出力の逐次ストリーミング（実装済み・最初版）
   - Backend: `event: log` を追加、ランIDごとのキューでノードの行ログを配信
   - UI: Run詳細でライブログを受信し、React Flowのノードホバー時に下部パネルへ表示
2. ベスト選択の保存と履歴（実装：初版）
   - UI: 「この結果を採用」ボタンで `best_tool` を保存。Runs一覧にベストのバッジを表示
   - Backend/DB: `POST /runs/{id}/adopt`（手動採用）で `runs.best_tool/best_score` を更新
3. 評価メトリクス拡張（実装：初版）
   - 文字数/行数/コード/差分/テストに加え、語彙規模（vocab）/TTR/平均行長/重複行率/キーワード包含率を算出
   - スコアへ反映し、PRサマリにも値を出力。将来はUIで内訳可視化やモデル採点・ルーブリックへ拡張
4. CLIテンプレ/プロファイル（拡張）
   - 環境変数ホワイトリスト、作業ディレクトリ、並列度、deny強化（正規表現/ホワイトリスト）
5. OpenTelemetry 連携（実装：初版）
   - Run/NodeをSpanとして計測（tool/timeout/prompt.size/ok/exit_code/duration_ms/score）
   - エクスポート: OTLP（`OTEL_EXPORTER_OTLP_ENDPOINT`）未設定時はConsole出力
   - 将来: Grafana/Langfuse等への統合、メトリクス拡張（カウンタ/ヒストグラム）
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
