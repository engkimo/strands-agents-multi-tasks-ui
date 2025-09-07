# アーキテクチャ（案）

## コンポーネント
- UI: 実行一覧、グラフビュー、ノード詳細（I/O/ログ/トレース）。ローカル Web を想定。
- API/Backend: 実行管理、履歴保存、ストリーミング更新（SSE/WebSocket）。
- Agent Runtime: Strands Agents ベースの Graph/Swarm 実行、ツール呼び出し（async）。
- Tool Adapters: CLI ラッパー（Python）、入出力スキーマ、サニタイズ、タイムアウト。
- Storage: SQLite + ファイルストレージ（アーティファクト）。
- Telemetry: OpenTelemetry SDK（Span/Metric）、ローカルエクスポータ。

## 実行フロー（概略）
1. ユーザーが UI でツールセット/入力を指定 → 実行リクエスト作成。
2. Backend が Run を作成し、Agent Runtime に Graph/Swarm を指示。
3. 各ノードは CLI ラッパーを非同期実行。STDOUT/STDERR をキャプチャ。
4. 結果とメタデータを保存、OTel Span を発行。
5. UI はストリーミングで状態更新を受け取り、グラフ/ログを描画。

## エラー/リトライ
- ノード単位のリトライ、指数バックオフ、フォールバック経路。
- 途中失敗時も部分結果閲覧可、再開/再実行（from ノード）に対応。

## デプロイ/運用
- ローカル開発（Mac/Linux）: Python + SQLite。将来 Docker 化。
- 設定: ツール/API キー、実行権限（ネットワーク/ファイル）、保持期間。

参照: `../01_requirements.md`

