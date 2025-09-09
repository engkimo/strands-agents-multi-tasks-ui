# 進捗まとめ（現在地）と次アクション

最終更新: 2025-09-09

## 要約（直近の到達点）
- UI: React Flow によるグラフ表示、ノードホバー時にライブログ（SSE: log）/最終stdoutを下部にプレビュー
- 実行: 並列（Best-of-N）+ 逐次保存、PRパッケージ（summary/review/patch）生成
- 推奨: tools.yml + /recommend による推奨ツール選択（Runs画面から反映）
- 評価: 軽量メトリクス拡張（vocab/TTR/平均行長/重複行率/キーワード包含率）をスコアに反映
- ベスト: 自動選定 + 手動採用（/runs/{id}/adopt）、一覧にベストバッジ表示
- プロファイル: tools.yml で stdin/arg_template/timeout/retries/max_output_bytes/deny を適用
- テレメトリ: OpenTelemetry で run/tool span と log イベントを記録（OTLP or Console）
- テスト: loader/evaluator/runner をunittestでスモーク
- メトリクス: `GET /metrics/summary` を追加、Runs 画面にダッシュボードカード（総Runs/成功率/平均時間）を表示
- エラーバッジ: Run詳細で timeout / not found / 非ゼロ終了 などの種別を表示
- ツール: UI のツール選択肢に `spec_kit` を追加（環境未設定時は echo フォールバック）

### 変更履歴（直近の差分）
- Backend: `backend/app/tools/__init__.py` に `import asyncio` 追加（リトライのバックオフ修正）
- Backend: `DB.metrics_summary()` を実装し `GET /metrics/summary` を追加
- UI: Runs にメトリクスカード、Run詳細にエラー種別バッジ、`spec_kit` を選択肢に追加

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
  - 逐次ログ（`log` イベント）をツール別に配信
 - `GET /metrics/summary`（集計）
  - 総Runs/ノード総数/成功数・失敗数/平均時間（全体・OK）/ツール別集計

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
- 逐次ログのUX: 長大ログの整形/検索/フィルタは未実装（初版）
- DiffのN-way比較（現状は任意2出力の比較）
- OTel メトリクス（カウンタ/ヒストグラム）と外部ダッシュボード連携は最小限
- 入力サニタイズ/安全装備の粒度向上（正規表現deny/ホワイトリスト強化）
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
 
## 次アクション（更新 2025-09-09）
1. メトリクス拡張（UI/集計）
   - Runs にツール別ブレークダウン（成功率/平均時間/平均スコア）を追加表示
   - `/metrics/summary` に期間フィルタ/ツール指定などの引数を拡張
2. グラフノードのエラーバッジ
   - GraphFlow 上のツールノードに timeout/exit コードなどのバッジを表示
3. トークン/コストの可視化
   - CLI から取得可能なメタのパース/概算計測と UI への表示
4. Graph/Swarm の拡張土台
   - 条件分岐/ループ/共有コンテキストの設計と可視化（MVP後の拡張）
5. セキュリティ強化
   - deny の正規表現化/ホワイトリスト、プロセス分離（将来的に container/sandbox）
6. テスト/安定性
   - `pip install -r backend/requirements.txt` 後、unittest/E2E を拡充
   - 長時間実行/ログ肥大/部分失敗の復帰シナリオ検証
7. Windows検証
   - パス/プロセス/改行差異を確認しREADMEに注意書き
