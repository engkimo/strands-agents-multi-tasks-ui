# デモ実行手順（API/ブラウザ）

## 1) 前提設定
- `.env.example` をコピーして `.env` を作成
- デモ用: `.env` の `DEMO_MODE=1` でツール出力を擬似生成（UI差分が分かりやすい）
- 実CLIで動かす場合は `DEMO_MODE=0` にし、各 CLI の実行コマンドを設定

## 2) 起動
- Docker: `docker compose -f docker-compose.dev.yml up --build`
- ネイティブ（任意）
  - Backend: `cd backend && pip install -r requirements.txt && uvicorn app.api.server:app --reload`
  - UI: `cd ui && npm install && npm run dev`

## 3) ブラウザデモ
- UI: `http://localhost:5173`
- 新規実行 → プロンプト入力 → ツール選択（2〜4）→ 実行
- Run詳細で以下を確認
  - グラフ: ノード状態（pending/running/success/error）
  - ノード詳細: I/O・ログ・実行時間・スコア
  - 差分: 行/単語、空白/大小無視、Markdown表示
  - ベスト: best_tool/best_score の表示
  - 再実行: 全ツール / 失敗のみ / 単一ツール

## 4) APIデモ（任意、`curl`）
- 実行作成
```
RUN=$(curl -s -X POST http://localhost:8000/runs \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"アイデアを5つ","tools":["claude_code","codex_cli","gemini_cli"]}')
RUN_ID=$(echo "$RUN" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
echo $RUN_ID
```
- 進捗SSE（終了で抜ける場合は `Ctrl+C`）
```
curl -N http://localhost:8000/stream/runs/$RUN_ID
```
- 詳細取得
```
curl -s http://localhost:8000/runs/$RUN_ID | jq .
```

## 5) トラブルシュート
- ポート競合: `8000/5173` を使用中でないか確認
- CLI 未設定: `.env` の `TOOL_*` を設定 or フォールバックのままデモ
- 権限/パス: CLI の PATH と実行権限を確認

## 6) 既知の制約（デモ時）
- ログはノード完了単位で反映（逐次ログは次期追加）
- 評価は簡易スコア（情報量/コード/差分/テスト語）

参照: `docs/70_demo_playbook.md`, `docs/80_progress_next.md`

## 7) テスト（任意）
- ユニット/E2E（標準ライブラリunittest）
  - 実行例（bash/fish 共通）:
    - `PYTHONPATH=backend python -m unittest discover -v backend/tests`
  - 目的:
    - loader: 推奨・実行オプションの構築
    - evaluator: 指標算出とスコア
    - runner: denyブロックや出力トリムの挙動
 - PRパッケージ作成（左を採用する代わりに tool を明示）
```
curl -s -X POST http://localhost:8000/runs/$RUN_ID/package_pr \
  -H 'Content-Type: application/json' \
  -d '{"tool":"claude_code","title":"Demo PR"}' | jq .
```
- ワンクリックデモ: Runs画面の「デモ実行（3ツール一括）」で、既定プロンプト+3ツールで即時実行できます（DEMO_MODE=1 推奨）
