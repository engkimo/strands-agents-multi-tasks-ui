# スーパーバイザーと tools.yml（雛形）

本機能は、プロンプト（タスク）の内容に応じて推奨ツールを自動選択する仕組みです。MVPでは簡易ルールベースで実装しています。

## 目的
- 入力プロンプトから「コード修正/リファクタ」「アイデア出し」「仕様/設計」などのカテゴリを推定し、適切なツールセット（Claude/Codex/Gemini）を提示する。
- `.env` は主に API Key 管理に集中し、実行の方針は `tools.yml` に集約する。

## tools.yml（雛形）
- パス: `backend/app/config/tools.yml`
- 例:
```
tools:
  claude_code:
    env_keys: [ANTHROPIC_API_KEY]
    stdin: true
  codex_cli:
    env_keys: [OPENAI_API_KEY]
    stdin: true
  gemini_cli:
    env_keys: [GEMINI_API_KEY, GOOGLE_API_KEY]
    stdin: true

selectors:
  - name: code_refactor
    keywords: ["refactor", "リファクタ", "テスト", "差分", "diff"]
    recommend: ["claude_code", "codex_cli"]
  - name: ideation
    keywords: ["アイデア", "ブレスト", "発想", "提案", "ideas"]
    recommend: ["claude_code", "gemini_cli"]
  - name: spec_design
    keywords: ["仕様", "設計", "要件", "spec", "design"]
    recommend: ["claude_code", "gemini_cli"]

default:
  recommend: ["claude_code", "codex_cli", "gemini_cli"]
```

## API
- `POST /recommend` → `{"prompt": "..."}` を渡すと、`{"tools": ["claude_code", ...], "selector": "ideation"}` を返す。
- `GET /config/tools` → 読み込まれた `tools.yml` の内容を返す。

## UI
- Runs 画面に「推奨ツール選択」ボタンを追加。現在のプロンプトを `POST /recommend` に送り、返ってきたツールでチェックを更新。

## 拡張案（将来）
- ルール→スコアリング（重み付け）→学習ベース（評価データで学習）へ拡張。
- `tools.yml` をプロファイル化（引数テンプレ/安全制約/コスト上限など）。
- スーパーバイザーがセマンティックに「タスク→最適なDAG」を生成して実行。

