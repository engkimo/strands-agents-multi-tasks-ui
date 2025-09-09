# 開発サマリ（これまで）と次アクション（短縮版）

本ドキュメントは、直近の到達点と最小限の操作手順、主要設定、今後の優先課題を1枚にまとめたサマリです。詳細は各ドキュメント（プレイブック/進捗/スーパーバイザー等）を参照してください。

## 到達点（機能サマリ）
- UI
  - React Flow によるワークフロー表示（Input → 各ツール → Merge）
  - ノードにホバーでライログ（SSE: `log`）＋最終stdoutを下部にプレビュー
  - 差分ビュー（任意2出力、行/単語、空白/大小無視、Markdown切替、コピー）
  - デモ実行（3ツール一括）ボタン、簡易チュートリアル表示
  - 推奨ツール選択ボタン（/recommend の結果を反映）
  - ベスト採用ボタン（この結果を採用 → `best_tool` 保存）＋一覧にバッジ表示
- 実行/バックエンド
  - 並列実行（Best-of-N）＋逐次保存（完了順）
  - 逐次ログ配信（SSE `log`）/ ステータス（`status`/`node`/`done`）
  - PRパッケージ（`summary.md`/`review.md`/`patch.txt`）生成
  - 評価メトリクス拡張（vocab/TTR/平均行長/重複行率/キーワード包含率 など）→ スコア反映
  - OpenTelemetry 計測（run/tool span、log イベント、OTLP or Console）
- スーパーバイザー / プロファイル
  - tools.yml で stdin/arg_template/timeout/retries/max_output_bytes/deny/env_allow/env_add/cwd を適用
  - /recommend によりプロンプト内容から推奨ツール選択、`default.concurrency` で同時実行数を制御
- テスト
  - unittest（loader/evaluator/runner のスモーク）

## 使い方（最短）
- 起動（Docker）
  - `cp .env.example .env`（既定 `DEMO_MODE=1`）
  - `docker compose -f docker-compose.dev.yml up --build`
  - UI: `http://localhost:5173` / API: `http://localhost:8000`
- デモ
  - Runs → 「デモ実行（3ツール一括）」で実行
  - Run詳細: グラフで状態、ノードにホバーでログ、差分/スコア/ベスト/PRパッケージを確認

## 主要エンドポイント
- `POST /runs`（実行作成）、`GET /runs` / `/runs/{id}`（一覧/詳細）
- `GET /stream/runs/{id}`（SSE: status/node/log/done）
- `POST /runs/{id}/package_pr`（PRパッケージ生成）
- `POST /runs/{id}/adopt`（ベスト採用）
- `POST /recommend`（推奨ツール）、`GET /config/tools`（tools.yml 内容）

## tools.yml（要点）
- ツール別設定
  - `stdin` / `arg_template`（`{text}` 置換）、`limits.timeout_seconds/retries/max_output_bytes`
  - `safety.deny`（簡易deny）、`env_allow/env_add`（環境変数）、`cwd`（作業ディレクトリ）
- 既定設定
  - `default.recommend`（推奨順）、`default.concurrency`（同時実行数、0は無制限）

## .env（要点）
- デモ: `DEMO_MODE=1`
- 実CLI: `DEMO_MODE=0` + `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GOOGLE_API_KEY or GEMINI_API_KEY`
- OTel（任意）: `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`

## 既知の制約（抜粋）
- 逐次ログは初版（長大ログの整形/検索は今後）
- Diffは2出力比較に限定（N出力切替/同時表示は将来）
- Windows差分（PATH/改行/echo挙動等）は要検証

## 次アクション（提案順）
1. Windows 注意書きと互換検証（README Known Issues 追記）
2. E2E の拡張（並列/再試行/deny/トリム/逐次ログの統合確認）
3. tools.yml の拡張（envホワイトリストの厳密化、正規表現deny、作業ディレクトリごとの隔離）
4. OTel メトリクス強化（カウンタ/ヒストグラム、実行時間分布など）
5. UI磨き（配色アクセシビリティ、DiffのN出力切替、エラートースト）

参考: `docs/70_demo_playbook.md`, `docs/75_demo_run.md`, `docs/80_progress_next.md`, `docs/90_supervisor.md`
