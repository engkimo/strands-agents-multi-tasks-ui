# UI Skeleton

- Stack: Vite + React（依存は少数、ハッシュルーティングで簡易遷移）
- API先: `VITE_API_BASE`（未設定時は `http://localhost:8000`）

## 開発
- `cd ui && npm install`
- `npm run dev` で `http://localhost:5173` を開く

## 画面
- Runs: 実行作成フォーム（プロンプト + ツール選択）、実行一覧
- RunDetail: 状態表示、各ノードのI/O、簡易差分（2出力の行単位）

