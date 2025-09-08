# デモプレイブック: AI とブレストでアイデア発散/収束

本プレイブックは、`docs/bounce_ideas_off_of_someone_with_AI.txt` の内容をもとに、デモで実演する体験を簡潔に再構成したものです。実装の受入基準にも直結します。

## 目的
- 同一プロンプトを 4 CLI（Claude Code / Codex CLI / Gemini CLI / Spec Kit）に並列投入し、出力の差分を UI で可視化して“ベスト”を選定する。

## 対象と前提
- 対象: 個人開発者（Primary）
- 形態: ローカル Web UI（バックエンド: FastAPI、実行: 非同期/並列）
- ツール: Claude Code / Codex CLI / Gemini CLI（任意に選択可能。Spec Kit は今回除外）
- 依存: Python/Node/Docker が導入済み。API キー等は設定済み。

## 入力例（プロンプト）
> 副業向けの新しい開発者ツールのアイデアを5つ

## シナリオ手順
1) ツールの選択: 4 CLI のうち実行対象をチェック（2〜4 任意）
2) プロンプト入力: 上記の例または任意のテーマを入力
2a) 推奨選択: 「推奨ツール選択」ボタンでプロンプトに基づく推奨セットを反映（任意）
3) 実行: Best-of-N で並列実行を開始（DAG に 2〜4 ノードが展開）
4) 観察: React Flow グラフで各ノードの状態（待機→実行→完了）と実行時間を表示。ノードにマウスを重ねると、そのタスクのログ（stdout 抜粋）を画面下に表示
5) 詳細: ノードを選択し、I/O（入力/出力）とログ（STDOUT/STDERR）を確認
6) 比較: 差分ビューで各出力を横並び比較（並列/サイドバイサイド切替）
7) 採用: ベストな出力を 1 つ選択し、履歴に保存（再実行可能）
8) （任意）PRパッケージ: 差分ビュー直下のボタンで summary/review/patch を生成・プレビュー

## 期待結果
- 並列実行の可視化（グラフ）と、各ノードの I/O/ログ/実行時間の表示
- 2 つ以上の出力を差分ビューで比較し、差異がハイライトされる
- 採用した出力が履歴へ保存され、再実行時に差分比較できる

## ハンズオン（クイックデモ）
- 前提: `cp .env.example .env`
- 起動（Docker 推奨）: `docker compose -f docker-compose.dev.yml up --build`
- ブラウザ: `http://localhost:5173`
- 操作: 「新規実行」にプロンプトを入力 → ツールを2〜4選択 → 実行
- 確認: Run詳細でグラフ/ログ/差分/スコア/ベストが逐次更新される（SSE）

ネイティブでの起動（任意）
- Backend: `cd backend && pip install -r requirements.txt && uvicorn app.api.server:app --reload`
- UI: `cd ui && npm install && npm run dev`

CLIの実コマンド設定（例）
- `.env` に以下例を追記（未設定時は `echo` でフォールバック）
  - `TOOL_CLAUDE_CODE_CMD="claude"`, `TOOL_CLAUDE_CODE_ARGS="--mode code"`, `TOOL_CLAUDE_CODE_USE_STDIN=1`
  - `TOOL_CODEX_CLI_CMD="codex"`, `TOOL_CODEX_CLI_ARGS="--json"`, `TOOL_CODEX_CLI_USE_STDIN=1`
  - `TOOL_GEMINI_CLI_CMD="gemini"`, `TOOL_GEMINI_CLI_ARGS="--model 1.5-pro"`, `TOOL_GEMINI_CLI_USE_STDIN=1`
  - `TOOL_SPEC_KIT_CMD="spec-kit"`, `TOOL_SPEC_KIT_ARGS=""`, `TOOL_SPEC_KIT_USE_STDIN=1`

## 受入基準（MVP）
- 複数 CLI を同一入力で並列実行できる（最低 2、最大 4）
- 各ノードの I/O/ログ/時間/終了コードが UI で閲覧できる
- 差分ビューで少なくとも 2 出力の差分が明確に可視化される
- 採用ボタンで出力を保存し、履歴から再実行・再比較できる

## 計測（デモ/KPI）
- 実行成功率、平均/95p レイテンシ、比較実行率、採用率
- ノード失敗率、リトライ成功率（失敗時）

## リスク/回避策
- CLI 出力のばらつき: 改行/色コード/余分ヘッダの正規化フィルタを適用
- レート制限/失敗: タイムアウト/再試行/指数バックオフ、（必要に応じて）キャッシュ
- 長文差分の可読性: 折りたたみ/検索/フィルタを用意

## 参考
- 原文ログ（全文）: `docs/bounce_ideas_off_of_someone_with_AI.txt`
- 要件/PRD/MVP: `docs/10_prd.md`, `docs/40_mvp.md`
