# Backend Skeleton

- Framework: FastAPI (ASGI)。SSE/WSで実行更新の配信を想定。
- 目的: 並列実行エンドポイントと履歴APIの骨組み。

起動（例）:
- `pip install -r requirements.txt`
- `uvicorn app.api.server:app --reload`

環境変数（実CLI設定）:
- `TOOL_CLAUDE_CODE_CMD` / `TOOL_CLAUDE_CODE_ARGS` / `TOOL_CLAUDE_CODE_USE_STDIN=1`
- `TOOL_CODEX_CLI_CMD` / `TOOL_CODEX_CLI_ARGS` / `TOOL_CODEX_CLI_USE_STDIN=1`
- `TOOL_GEMINI_CLI_CMD` / `TOOL_GEMINI_CLI_ARGS` / `TOOL_GEMINI_CLI_USE_STDIN=1`
- `TOOL_SPEC_KIT_CMD` / `TOOL_SPEC_KIT_ARGS` / `TOOL_SPEC_KIT_USE_STDIN=1`

備考:
- 既定値は `echo` による簡易出力です（実CLI未設定時のフォールバック）。
- `*_USE_STDIN` が `1` の場合、プロンプトは標準入力として渡されます。
