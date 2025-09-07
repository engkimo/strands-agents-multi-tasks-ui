# WBS（実装タスク分解 / 1名・約4週間）

## 全体方針
- Primary: 個人開発者向け。ローカル Web UI。
- MVPの必須体験: 同一入力を4 CLI（Claude Code / Codex CLI / Gemini CLI / Spec Kit）に並列実行し、差分をUIで比較・採用。
- ランタイム: Strands Agents ベース（Graph/Swarm）。データはSQLite + ファイル。

## マイルストーン
- W1: ラッパー/実行基盤/保存層の骨格、単発実行（1 CLI）
- W2: 並列実行（Best-of-N）+ Graphビュー最小、ログ/STDOUT表示
- W3: 履歴/再実行/差分ビュー、エラー/リトライ、安定化
- W4: UX/パフォーマンス、簡易メトリクス、デモ整備

## 依存/前提
- Python 3.11+, Node 20+, Docker（dev用）。
- 環境変数: `CLAUDE_API_KEY`/`OPENAI_API_KEY`/`GEMINI_API_KEY` 等（各CLI要件に合わせて命名）。
- 各CLIはローカル実行可能であること（パス/権限）。

## リポジトリ構成（案）
- `backend/`
  - `app/api/server.py`（FastAPI + SSE/WebSocket）
  - `app/agents/graph.py`（Best-of-N DAG/Swarm）
  - `app/tools/{claude_code,codex_cli,gemini_cli,spec_kit}.py`（CLIラッパー）
  - `app/storage/{sqlite.py,files.py}`（メタ/アーティファクト保存）
  - `app/models.py`（Run/Node/Artifact/MetricのPydantic）
  - `app/telemetry/otel.py`（OTel初期化）
- `ui/`（Vite + React）
  - `src/pages/{Runs,RunDetail}.tsx`、`components/{Graph,NodePanel,DiffView}.tsx`
- `scripts/`（dev起動/デモ用シェル）
- `.env.example`（APIキー/設定）

## コンポーネント別タスク

1) Tool Adapters（CLIラッパー）
- 標準I/F: `@tool async def run_cli(name, args:list[str], input:str|None, cwd:str|None, timeout:int=120)`
- 実装: `asyncio.create_subprocess_exec` でSTDOUT/STDERR/exit_code/elapsedを取得
- サニタイズ: 引数/パス検証、タイムアウト/キャンセル
- 成果物保存: STDOUT/ERRをファイル化（artifact）、要約メタを返却
- 各CLIの薄いラッパーを4つ用意（スイッチ or 個別関数）

2) Orchestration（Strands Agents）
- Best-of-N DAG: Fan-out（4ノード）→ Fan-in（集約）→ Diff生成ノード
- リトライ/バックオフ、早期終了（すべて失敗時）
- フィルタ: 選択したCLIのみノード生成

3) Storage（SQLite + Files）
- テーブル: `runs, nodes, artifacts, metrics, traces`
- ランID配下に`runs/<id>/{node}/`でファイル保存
- API層と疎結合なRepositoryの用意

4) API Backend（FastAPI）
- `POST /runs`: 実行開始（入力、選択ツール）
- `GET /runs`: 一覧、`GET /runs/{id}`: 詳細
- `GET /runs/{id}/nodes`/`/artifacts`
- `GET /stream/runs/{id}`: 状態更新SSE（Run/Node/Logイベント）

5) UI（React + Vite）
- Runs一覧: ステータス、開始/終了、成功率
- Run詳細: グラフビュー（簡易DAG）、ノード選択→I/O/ログ/時間
- DiffView: 4出力のテキスト差分（並列/サイドバイサイド切替）
- ストリーム更新: SSE購読、トースト/バッジ更新

6) Diff Viewer
- ライブラリ: `diff-match-patch` or `diff`（JS）
- プレーンテキスト/Markdown優先、コードはシンタックス強調
- 差分のハイライトとコピー、採用ボタン

7) Telemetry（OTel）
- Span: Run/Node単位で開始/終了/属性（tool/latency/exit_code）
- Export: コンソール or ローカルファイル（MVP）

8) 設定/セキュリティ
- `.env`ロード、APIキーのUI入力（任意）
- 危険コマンド遮断（ワイルドカード削除、相対パス制限）

9) Packaging/Dev
- `docker-compose.dev.yml`（backend/ui/sqlite用Volume）
- Makefile or npm/yarn scripts（dev/start/build）

10) QA/Docs
- E2Eスモーク（並列実行→Diff表示）
- デモ手順: `docs/bounce_ideas_off_of_someone_with_AI.md` に沿って確認
- 既知の制約/回避策の記録

## 受入基準（MVP）
- 4 CLIのうち選択したn本を同一入力で並列実行できる
- 各ノードのI/O/ログ/時間/エラーがUIで閲覧できる
- 完了後、出力を差分表示し、1つを採用として保存できる
- 履歴から再実行し、結果を比較できる

## リスクと対策
- CLIの出力形式ばらつき: 標準化フィルタ/正規化（末尾改行/色コード除去）
- APIレート制限: タイムアウト/再試行/バックオフ、入力キャッシュ
- 長文差分のUX: 折りたたみ/検索/フィルタを用意
- Windows対応: MVP後に検討（path/PTY周り差異）

