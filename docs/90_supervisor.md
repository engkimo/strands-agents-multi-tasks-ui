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
    env_allow: [PATH]      # 親環境から許可するキー（PATHは自動的に許可）
    env_add: {}            # 追加で与える環境変数
    stdin: true            # 入力はSTDINで渡す
    arg_template: ""       # stdin=falseのとき {text} をプロンプトで置換
    limits:
      timeout_seconds: 120 # ツール別のタイムアウト
      retries: 0           # 失敗時の再試行回数
      max_output_bytes: 200000  # 出力上限（UTF‑8バイト換算）
    safety:
      deny: ["rm -rf", "shutdown", "reboot", "mkfs", ":(){:|:&};:"]
    cwd: null             # 作業ディレクトリ（nullで親のまま）
  codex_cli:
    env_keys: [OPENAI_API_KEY]
    env_allow: [PATH]
    env_add: {}
    stdin: true
    arg_template: ""
    limits:
      timeout_seconds: 120
      retries: 0
      max_output_bytes: 200000
    safety:
      deny: ["rm -rf", "shutdown", "reboot"]
    cwd: null
  gemini_cli:
    env_keys: [GEMINI_API_KEY, GOOGLE_API_KEY]
    env_allow: [PATH]
    env_add: {}
    stdin: true
    arg_template: ""
    limits:
      timeout_seconds: 120
      retries: 0
      max_output_bytes: 200000
    safety:
      deny: ["rm -rf", "shutdown", "reboot"]
    cwd: null

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
  concurrency: 0  # 並列度（0は無制限、>0で同時実行数を制限）
```

## API
- `POST /recommend` → `{"prompt": "..."}` を渡すと、`{"tools": ["claude_code", ...], "selector": "ideation"}` を返す。
- `GET /config/tools` → 読み込まれた `tools.yml` の内容を返す。
  - 実行時は `tools.yml` に基づき、stdin/arg_template/timeout_seconds を反映して各ツールを起動。
  - 環境変数は `env_allow`（許可）と `env_add`（追加）で制御（PATHは常に許可）。
  - `default.concurrency` が >0 の場合、同時実行数を制限（セマフォ制御）。

## セーフティ/制限（初版）
- `limits.max_output_bytes`: 各ツールの出力を概算バイト上限でトリム（UTF‑8換算・超過時は `[truncated]` を付与）
- `limits.retries`: 失敗（非ゼロ終了など）の再試行回数（指数的バックオフ）
- `safety.deny`: コマンドラインの単純サブストリング拒否（例: `rm -rf`, `shutdown`）。一致時は実行せず失敗として扱う

注意: 初版は簡易実装です。将来は正規表現/ホワイトリスト・シェル解釈なしの厳密検査や、サンドボックスの分離度向上を検討します。

## UI
- Runs 画面に「推奨ツール選択」ボタンを追加。現在のプロンプトを `POST /recommend` に送り、返ってきたツールでチェックを更新。

## 拡張案（将来）
- ルール→スコアリング（重み付け）→学習ベース（評価データで学習）へ拡張。
- `tools.yml` をプロファイル化（引数テンプレ/安全制約/コスト上限など）。
- スーパーバイザーがセマンティックに「タスク→最適なDAG」を生成して実行。
